from __future__ import annotations

import asyncio
import base64
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

# ============================================================================
# Tunable thresholds - THESE ARE UNCALIBRATED HACKATHON DEFAULTS.
#
# Unlike the ICAO checksum math (a formal spec) or the ArcFace match threshold
# (a published benchmark), there is no authoritative source for "what ELA/
# gradient/noise anomaly level means tampering" - it depends on scanner/camera
# characteristics, JPEG history, and document substrate. These values are
# reasonable starting points reasoned from first principles, NOT validated
# against a labeled dataset. Before trusting this for a demo, run it against a
# handful of genuine documents and a few deliberately-edited ones (e.g. a
# GIMP-pasted photo, a Photoshopped digit) and adjust these to separate the
# two populations. Treat every number below as "tune me".
# ============================================================================

_JPEG_RESAVE_QUALITY = 90
_ELA_AMPLIFICATION = 15.0

_BLOCK_SIZE = 16
_ELA_ROBUST_Z_THRESHOLD = 2.5       # MAD-based robust z-score for "this block is a hotspot"
_ELA_HOTSPOT_FLAG_THRESHOLD = 0.15  # >15% of blocks anomalous -> flag

_SEAM_BAND_PX = 8
_SEAM_DISCONTINUITY_REFERENCE = 3.0  # normalizes raw discontinuity score to ~[0,1]
_SEAM_FLAG_THRESHOLD = 0.40

_VARIANCE_LOG_REFERENCE = 1.5  # normalizes |log(ela_variance_ratio)| to ~[0,1]
_VARIANCE_FLAG_THRESHOLD = 0.30

_NOISE_ROBUST_Z_THRESHOLD = 3.0
_NOISE_FLAG_THRESHOLD = 0.10  # >10% of blocks anomalous -> flag

_WEIGHT_ELA_HOTSPOT = 40.0
_WEIGHT_BOUNDARY_SEAM = 35.0
_WEIGHT_NOISE_RESIDUAL = 25.0


class ELAAnalysisError(Exception):
    """Raised when the input image can't be decoded/processed for tampering analysis."""


def _decode_bgr(image_bytes: bytes) -> np.ndarray:
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ELAAnalysisError("Could not decode image bytes for tampering analysis.")
    return img


# ----------------------------------------------------------------------------
# 1. Error Level Analysis
# ----------------------------------------------------------------------------


def _compute_ela_map(img_bgr: np.ndarray) -> np.ndarray:
    """
    Resaves the image as a 90%-quality JPEG and returns the amplified,
    per-pixel absolute difference (uint8, single channel - max across BGR
    channels so a tamper visible in only one channel isn't averaged away).
    """
    ok, encoded = cv2.imencode(".jpg", img_bgr, [cv2.IMWRITE_JPEG_QUALITY, _JPEG_RESAVE_QUALITY])
    if not ok:
        raise ELAAnalysisError("Failed to re-encode image as JPEG for ELA.")

    resaved = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
    if resaved is None:
        raise ELAAnalysisError("Failed to decode the resaved JPEG for ELA.")
    if resaved.shape != img_bgr.shape:
        resaved = cv2.resize(resaved, (img_bgr.shape[1], img_bgr.shape[0]))

    diff = cv2.absdiff(img_bgr.astype(np.int16), resaved.astype(np.int16))
    diff_gray = diff.max(axis=2)  # per-pixel max across channels
    amplified = np.clip(diff_gray.astype(np.float32) * _ELA_AMPLIFICATION, 0, 255).astype(np.uint8)
    return amplified


def _make_heatmap_data_uri(ela_map: np.ndarray) -> str:
    colored = cv2.applyColorMap(ela_map, cv2.COLORMAP_JET)
    ok, encoded = cv2.imencode(".png", colored)
    if not ok:
        raise ELAAnalysisError("Failed to encode ELA heatmap as PNG.")
    b64 = base64.b64encode(encoded.tobytes()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def _block_stat(map_2d: np.ndarray, block_size: int, stat: str) -> np.ndarray:
    """Returns a 1D array of per-block mean or std, tiling the array (edge remainder dropped)."""
    h, w = map_2d.shape
    n_rows, n_cols = h // block_size, w // block_size
    values = np.empty(n_rows * n_cols, dtype=np.float64)
    i = 0
    for by in range(n_rows):
        for bx in range(n_cols):
            block = map_2d[by * block_size:(by + 1) * block_size, bx * block_size:(bx + 1) * block_size]
            values[i] = block.mean() if stat == "mean" else block.std()
            i += 1
    return values


def _robust_z_scores(values: np.ndarray) -> np.ndarray:
    """
    Median Absolute Deviation (MAD) based z-score - much more resistant to the
    outliers-we're-looking-for skewing the baseline than a plain std-based
    z-score would be (std is inflated BY the outliers, which masks them).
    This is what makes the anomaly detection "relative to the document's own
    baseline" rather than an absolute threshold that false-positives on
    genuinely high-contrast passport text.
    """
    median = np.median(values)
    mad = np.median(np.abs(values - median)) + 1e-6
    return 0.6745 * (values - median) / mad


def _localized_ela_hotspot_ratio(ela_map: np.ndarray) -> float:
    block_means = _block_stat(ela_map, _BLOCK_SIZE, "mean")
    z = _robust_z_scores(block_means)
    hotspot_mask = z > _ELA_ROBUST_Z_THRESHOLD  # one-sided: only ABOVE-baseline blocks are suspicious
    return float(hotspot_mask.sum()) / len(block_means)


# ----------------------------------------------------------------------------
# 2. Photo splicing / boundary seam detection (only runs if face_bbox given)
# ----------------------------------------------------------------------------


def _clip_bbox(bbox: List[int], w: int, h: int) -> Tuple[int, int, int, int]:
    x1, y1, x2, y2 = bbox
    return max(0, int(x1)), max(0, int(y1)), min(w, int(x2)), min(h, int(y2))


def _boundary_seam_discontinuity(gray: np.ndarray, face_bbox: List[int]) -> float:
    """
    Compares gradient magnitude on a thin ring around the face bbox's perimeter
    against the gradient distribution in the rest of the document. A pasted
    photo often leaves an artificially sharp, unnaturally uniform edge where it
    was composited - this shows up as the perimeter ring's strong-edge tail
    (95th percentile) being elevated relative to the document's own natural
    gradient distribution, normalized by the document's own median gradient
    (so a naturally high-contrast document doesn't false-positive itself).
    """
    h, w = gray.shape
    x1, y1, x2, y2 = face_bbox

    x1o, y1o, x2o, y2o = _clip_bbox([x1 - _SEAM_BAND_PX, y1 - _SEAM_BAND_PX, x2 + _SEAM_BAND_PX, y2 + _SEAM_BAND_PX], w, h)
    x1i, y1i, x2i, y2i = _clip_bbox([x1 + _SEAM_BAND_PX, y1 + _SEAM_BAND_PX, x2 - _SEAM_BAND_PX, y2 - _SEAM_BAND_PX], w, h)

    gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    grad_mag = cv2.magnitude(gx, gy)

    ring_mask = np.zeros((h, w), dtype=bool)
    ring_mask[y1o:y2o, x1o:x2o] = True
    if x2i > x1i and y2i > y1i:
        ring_mask[y1i:y2i, x1i:x2i] = False

    background_mask = np.ones((h, w), dtype=bool)
    background_mask[y1o:y2o, x1o:x2o] = False

    ring_values = grad_mag[ring_mask]
    background_values = grad_mag[background_mask]

    if ring_values.size == 0 or background_values.size == 0:
        return 0.0

    ring_p95 = float(np.percentile(ring_values, 95))
    bg_p95 = float(np.percentile(background_values, 95))
    bg_median = float(np.median(background_values)) + 1e-6

    return max(0.0, ring_p95 - bg_p95) / bg_median


def _ela_variance_ratio(ela_map: np.ndarray, face_bbox: List[int]) -> float:
    """
    Ratio of ELA variance inside the portrait box vs the rest of the document.
    A pasted photo often has a different JPEG compression history than the
    surrounding card substrate, which shows up as an ELA variance that doesn't
    match the background - far from 1.0 in either direction is suspicious.
    """
    h, w = ela_map.shape
    x1, y1, x2, y2 = _clip_bbox(face_bbox, w, h)
    if x2 <= x1 or y2 <= y1:
        return 1.0  # can't evaluate - neutral, no evidence either way

    face_region = ela_map[y1:y2, x1:x2]
    mask = np.ones((h, w), dtype=bool)
    mask[y1:y2, x1:x2] = False
    background_region = ela_map[mask]

    face_var = float(face_region.var()) + 1e-6
    bg_var = float(background_region.var()) + 1e-6
    return face_var / bg_var


# ----------------------------------------------------------------------------
# 3. High-frequency noise residual consistency
# ----------------------------------------------------------------------------


def _noise_residual_outlier_ratio(gray: np.ndarray) -> float:
    """
    Median-filter residual, block-wise std, MAD-based outlier detection -
    TWO-SIDED on purpose: inpainting/smoothing shows up as anomalously LOW
    local noise (smoother than the sensor/print noise around it), while
    copy-move or added noise shows up as anomalously HIGH local noise. Both
    directions are worth flagging, for different tampering signatures.
    """
    median_filtered = cv2.medianBlur(gray, 3)
    residual = cv2.absdiff(gray, median_filtered).astype(np.float32)

    block_stds = _block_stat(residual, _BLOCK_SIZE, "std")
    z = _robust_z_scores(block_stds)
    outlier_mask = np.abs(z) > _NOISE_ROBUST_Z_THRESHOLD
    return float(outlier_mask.sum()) / len(block_stds)


# ----------------------------------------------------------------------------
# 4. Composite scoring
# ----------------------------------------------------------------------------


def _analyze_tampering_sync(image_bytes: bytes, face_bbox: Optional[List[int]]) -> Dict[str, Any]:
    img_bgr = _decode_bgr(image_bytes)
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

    ela_map = _compute_ela_map(img_bgr)
    ela_hotspot_ratio = _localized_ela_hotspot_ratio(ela_map)

    flags: List[str] = []
    if ela_hotspot_ratio > _ELA_HOTSPOT_FLAG_THRESHOLD:
        flags.append("ELA_ANOMALY_DETECTED")

    boundary_gradient_discontinuity = 0.0
    if face_bbox and len(face_bbox) == 4:
        seam_raw = _boundary_seam_discontinuity(gray, face_bbox)
        seam_norm = min(seam_raw / _SEAM_DISCONTINUITY_REFERENCE, 1.0)

        variance_ratio = _ela_variance_ratio(ela_map, face_bbox)
        variance_anomaly = abs(float(np.log(variance_ratio + 1e-6)))
        variance_norm = min(variance_anomaly / _VARIANCE_LOG_REFERENCE, 1.0)

        if seam_norm > _SEAM_FLAG_THRESHOLD:
            flags.append("SUSPICIOUS_PHOTO_SEAM")
        if variance_norm > _VARIANCE_FLAG_THRESHOLD:
            flags.append("PHOTO_ELA_MISMATCH")

        # Either strong evidence type alone is meaningful - a forger who nails
        # the edge blend might still mismatch on compression noise, or vice
        # versa, so we take the max rather than requiring both to agree.
        boundary_gradient_discontinuity = max(seam_norm, variance_norm)
    else:
        flags.append("PHOTO_SPLICE_CHECK_SKIPPED")

    noise_inconsistency_ratio = _noise_residual_outlier_ratio(gray)
    if noise_inconsistency_ratio > _NOISE_FLAG_THRESHOLD:
        flags.append("LOCALIZED_NOISE_ANOMALY")

    tampering_score = (
        min(ela_hotspot_ratio, 1.0) * _WEIGHT_ELA_HOTSPOT
        + boundary_gradient_discontinuity * _WEIGHT_BOUNDARY_SEAM
        + min(noise_inconsistency_ratio, 1.0) * _WEIGHT_NOISE_RESIDUAL
    )
    tampering_score = round(float(np.clip(tampering_score, 0.0, 100.0)), 2)

    return {
        "tampering_score": tampering_score,
        "tampering_flags": flags,
        "heatmap_base64": _make_heatmap_data_uri(ela_map),
        "metrics": {
            "ela_hotspot_ratio": round(float(ela_hotspot_ratio), 4),
            "boundary_gradient_discontinuity": round(float(boundary_gradient_discontinuity), 4),
            "noise_inconsistency_ratio": round(float(noise_inconsistency_ratio), 4),
        },
    }


async def analyze_tampering(image_bytes: bytes, face_bbox: Optional[List[int]] = None) -> Dict[str, Any]:
    """
    Runs ELA + photo-splice + noise-residual analysis on a document image and
    returns a composite tampering_score (0-100) plus flags/heatmap/metrics.

    `face_bbox` ([x1,y1,x2,y2], pixel coords in `image_bytes`'s own frame) is
    optional - when provided (e.g. from face_service's document face
    detection), the photo-splice check (seam gradient + ELA variance ratio)
    runs; when absent, that check is skipped (contributes 0 to the score,
    flagged PHOTO_SPLICE_CHECK_SKIPPED) rather than guessed at.

    Offloads all OpenCV/NumPy work to a worker thread so the FastAPI event
    loop is never blocked - same pattern as face_service.compare_faces().
    """
    return await asyncio.to_thread(_analyze_tampering_sync, image_bytes, face_bbox)