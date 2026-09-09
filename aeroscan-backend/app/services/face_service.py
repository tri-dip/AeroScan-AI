from __future__ import annotations

import asyncio
import io
import os
import threading
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
import onnxruntime as ort
from PIL import Image

# Model pack: InsightFace "buffalo_l" (the same pack the `insightface` PyPI package
# itself downloads on first use). We call the two ONNX graphs directly via
# onnxruntime instead of depending on the `insightface` package because its
# dependency chain (opencv-python, scikit-image, etc.) has no Python 3.14 wheels
# yet - onnxruntime, numpy and pillow do.
#
#   det_10g.onnx    -> SCRFD-10GF face detector (bbox + 5-point landmarks)
#   w600k_r50.onnx  -> ArcFace (ResNet50) 512-d face recognition embedding
_MODEL_ZIP_URL = "https://github.com/deepinsight/insightface/releases/download/v0.7/buffalo_l.zip"
_MODEL_DIR_NAME = "buffalo_l"
_DETECTOR_FILE = "det_10g.onnx"
_RECOGNIZER_FILE = "w600k_r50.onnx"

_DETECTOR_INPUT_SIZE = (640, 640)
_RECOGNIZER_INPUT_SIZE = (112, 112)
_FEAT_STRIDES = (8, 16, 32)
_NUM_ANCHORS = 2
_DET_SCORE_THRESHOLD = 0.5
_NMS_IOU_THRESHOLD = 0.4

# Reference 5-point landmark template ArcFace models are trained to expect
# after alignment to a 112x112 crop (left eye, right eye, nose, left mouth,
# right mouth) - standard across the InsightFace model zoo.
_ARCFACE_REFERENCE_LANDMARKS = np.array(
    [
        [38.2946, 51.6963],
        [73.5318, 51.5014],
        [56.0252, 71.7366],
        [41.5493, 92.3655],
        [70.7299, 92.2041],
    ],
    dtype=np.float32,
)

# Cosine similarity threshold for a same-person verdict. InsightFace's own
# published benchmarks put buffalo_l's LFW-optimal threshold in the 0.28-0.36
# band; 0.32 is a reasonable operating point that favors precision (fewer
# false accepts) for an identity-verification use case.
_MATCH_THRESHOLD = 0.32


class FaceServiceError(Exception):
    pass


@dataclass(frozen=True)
class FaceMatchResult:
    score: float  # 0-100, higher = more similar
    verified: bool
    cosine_similarity: float


def _model_cache_dir() -> Path:
    override = os.environ.get("FACE_MODEL_CACHE_DIR")
    base = Path(override) if override else Path.home() / ".cache" / "aeroscan-ai" / "models"
    return base / _MODEL_DIR_NAME


_download_lock = threading.Lock()


def _ensure_models_downloaded() -> Tuple[Path, Path]:
    cache_dir = _model_cache_dir()
    det_path = cache_dir / _DETECTOR_FILE
    rec_path = cache_dir / _RECOGNIZER_FILE

    if det_path.exists() and rec_path.exists():
        return det_path, rec_path

    with _download_lock:
        # Re-check after acquiring the lock in case another thread just finished.
        if det_path.exists() and rec_path.exists():
            return det_path, rec_path

        import urllib.error
        import urllib.request

        cache_dir.mkdir(parents=True, exist_ok=True)
        print(f"[face_service] downloading face model pack from {_MODEL_ZIP_URL}")

        try:
            with urllib.request.urlopen(_MODEL_ZIP_URL, timeout=120) as resp:
                zip_bytes = resp.read()
        except (urllib.error.URLError, TimeoutError) as exc:
            raise FaceServiceError(
                f"Failed to download face model pack from {_MODEL_ZIP_URL}: {exc}"
            ) from exc

        try:
            with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
                for member in zf.namelist():
                    name = Path(member).name
                    if name in (_DETECTOR_FILE, _RECOGNIZER_FILE):
                        with zf.open(member) as src, open(cache_dir / name, "wb") as dst:
                            dst.write(src.read())
        except zipfile.BadZipFile as exc:
            raise FaceServiceError(f"Face model pack download was not a valid zip: {exc}") from exc

        if not det_path.exists() or not rec_path.exists():
            raise FaceServiceError(
                f"Face model pack did not contain expected files "
                f"({_DETECTOR_FILE}, {_RECOGNIZER_FILE}) after extraction."
            )

        print(f"[face_service] face model pack cached at {cache_dir}")

    return det_path, rec_path


class _Models:
    _lock = threading.Lock()
    _detector: Optional[ort.InferenceSession] = None
    _recognizer: Optional[ort.InferenceSession] = None

    @classmethod
    def get(cls) -> Tuple[ort.InferenceSession, ort.InferenceSession]:
        if cls._detector is not None and cls._recognizer is not None:
            return cls._detector, cls._recognizer

        with cls._lock:
            if cls._detector is not None and cls._recognizer is not None:
                return cls._detector, cls._recognizer

            det_path, rec_path = _ensure_models_downloaded()
            providers = ["CPUExecutionProvider"]
            cls._detector = ort.InferenceSession(str(det_path), providers=providers)
            cls._recognizer = ort.InferenceSession(str(rec_path), providers=providers)

        return cls._detector, cls._recognizer


def _decode_image(image_bytes: bytes) -> np.ndarray:
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img.load()
    except Exception as exc:
        raise FaceServiceError(f"Could not decode image: {exc}") from exc
    return np.array(img.convert("RGB"))


def _distance2bbox(points: np.ndarray, distance: np.ndarray) -> np.ndarray:
    x1 = points[:, 0] - distance[:, 0]
    y1 = points[:, 1] - distance[:, 1]
    x2 = points[:, 0] + distance[:, 2]
    y2 = points[:, 1] + distance[:, 3]
    return np.stack([x1, y1, x2, y2], axis=-1)


def _distance2kps(points: np.ndarray, distance: np.ndarray) -> np.ndarray:
    preds = []
    for i in range(0, distance.shape[1], 2):
        px = points[:, i % 2] + distance[:, i]
        py = points[:, i % 2 + 1] + distance[:, i + 1]
        preds.append(px)
        preds.append(py)
    return np.stack(preds, axis=-1)


def _nms(dets: np.ndarray, thresh: float) -> List[int]:
    x1, y1, x2, y2, scores = dets[:, 0], dets[:, 1], dets[:, 2], dets[:, 3], dets[:, 4]
    areas = (x2 - x1) * (y2 - y1)
    order = scores.argsort()[::-1]

    keep: List[int] = []
    while order.size > 0:
        i = order[0]
        keep.append(int(i))
        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])
        w = np.maximum(0.0, xx2 - xx1)
        h = np.maximum(0.0, yy2 - yy1)
        inter = w * h
        iou = inter / (areas[i] + areas[order[1:]] - inter)
        order = order[np.where(iou <= thresh)[0] + 1]

    return keep


def _letterbox(img: np.ndarray, target_size: Tuple[int, int]) -> Tuple[np.ndarray, float]:
    h, w = img.shape[:2]
    target_w, target_h = target_size
    scale = min(target_w / w, target_h / h)
    new_w, new_h = int(round(w * scale)), int(round(h * scale))

    resized = np.array(Image.fromarray(img).resize((new_w, new_h), Image.BILINEAR))
    canvas = np.zeros((target_h, target_w, 3), dtype=np.uint8)
    canvas[:new_h, :new_w] = resized
    return canvas, scale


def _detect_largest_face(img: np.ndarray) -> Tuple[np.ndarray, float]:
    """Returns (5x2 landmarks, detection_score) for the largest detected face."""
    detector, _ = _Models.get()

    blob_img, scale = _letterbox(img, _DETECTOR_INPUT_SIZE)
    blob = blob_img.astype(np.float32)
    blob = (blob - 127.5) / 128.0
    blob = np.transpose(blob, (2, 0, 1))[None, ...]  # NCHW

    input_name = detector.get_inputs()[0].name
    output_names = [o.name for o in detector.get_outputs()]
    outputs = detector.run(output_names, {input_name: blob})

    input_h, input_w = _DETECTOR_INPUT_SIZE[1], _DETECTOR_INPUT_SIZE[0]
    fmc = len(_FEAT_STRIDES)

    scores_list, bboxes_list, kpss_list = [], [], []

    for idx, stride in enumerate(_FEAT_STRIDES):
        scores = outputs[idx].reshape(-1)
        bbox_preds = outputs[idx + fmc].reshape(-1, 4) * stride
        kps_preds = outputs[idx + fmc * 2].reshape(-1, 10) * stride

        height, width = input_h // stride, input_w // stride
        anchor_centers = np.stack(np.mgrid[:height, :width][::-1], axis=-1).astype(np.float32)
        anchor_centers = (anchor_centers * stride).reshape(-1, 2)
        anchor_centers = np.repeat(anchor_centers, _NUM_ANCHORS, axis=0)

        pos_inds = np.where(scores >= _DET_SCORE_THRESHOLD)[0]
        if pos_inds.size == 0:
            continue

        bboxes = _distance2bbox(anchor_centers, bbox_preds)
        kpss = _distance2kps(anchor_centers, kps_preds).reshape(-1, 5, 2)

        scores_list.append(scores[pos_inds])
        bboxes_list.append(bboxes[pos_inds])
        kpss_list.append(kpss[pos_inds])

    if not scores_list:
        raise FaceServiceError("No face detected in image.")

    all_scores = np.concatenate(scores_list)
    all_bboxes = np.concatenate(bboxes_list) / scale
    all_kpss = np.concatenate(kpss_list) / scale

    pre_nms = np.hstack([all_bboxes, all_scores[:, None]])
    keep = _nms(pre_nms, _NMS_IOU_THRESHOLD)

    if not keep:
        raise FaceServiceError("No face detected in image.")

    kept_bboxes = all_bboxes[keep]
    kept_kpss = all_kpss[keep]
    kept_scores = all_scores[keep]

    areas = (kept_bboxes[:, 2] - kept_bboxes[:, 0]) * (kept_bboxes[:, 3] - kept_bboxes[:, 1])
    largest_idx = int(np.argmax(areas))

    return kept_kpss[largest_idx], float(kept_scores[largest_idx])


def _umeyama_similarity_transform(src: np.ndarray, dst: np.ndarray) -> np.ndarray:
    """Least-squares similarity (scale+rotation+translation) transform src -> dst.
    Returns a 2x3 affine matrix. Standard Umeyama algorithm."""
    num = src.shape[0]
    src_mean = src.mean(axis=0)
    dst_mean = dst.mean(axis=0)
    src_c = src - src_mean
    dst_c = dst - dst_mean

    cov = (dst_c.T @ src_c) / num
    u, s, vt = np.linalg.svd(cov)

    d = np.ones(2)
    if np.linalg.det(u) * np.linalg.det(vt) < 0:
        d[-1] = -1

    r = u @ np.diag(d) @ vt
    var_src = (src_c ** 2).sum() / num
    scale = (s * d).sum() / var_src if var_src > 1e-8 else 1.0

    t = dst_mean - scale * (r @ src_mean)

    m = np.zeros((2, 3), dtype=np.float64)
    m[:2, :2] = scale * r
    m[:2, 2] = t
    return m


def _align_face(img: np.ndarray, landmarks: np.ndarray) -> np.ndarray:
    m = _umeyama_similarity_transform(landmarks.astype(np.float64), _ARCFACE_REFERENCE_LANDMARKS.astype(np.float64))

    # PIL's Image.transform(AFFINE) expects the *inverse* mapping (output px -> input px).
    a = np.vstack([m, [0, 0, 1]])
    a_inv = np.linalg.inv(a)
    coeffs = (a_inv[0, 0], a_inv[0, 1], a_inv[0, 2], a_inv[1, 0], a_inv[1, 1], a_inv[1, 2])

    pil_img = Image.fromarray(img)
    aligned = pil_img.transform(_RECOGNIZER_INPUT_SIZE, Image.AFFINE, coeffs, resample=Image.BILINEAR)
    return np.array(aligned)


def _embed_face(aligned_face: np.ndarray) -> np.ndarray:
    _, recognizer = _Models.get()

    blob = aligned_face.astype(np.float32)
    blob = (blob - 127.5) / 127.5
    blob = np.transpose(blob, (2, 0, 1))[None, ...]  # NCHW

    input_name = recognizer.get_inputs()[0].name
    output_name = recognizer.get_outputs()[0].name
    embedding = recognizer.run([output_name], {input_name: blob})[0][0]

    norm = np.linalg.norm(embedding)
    if norm < 1e-8:
        raise FaceServiceError("Degenerate face embedding produced (zero norm).")
    return embedding / norm


def _face_embedding(image_bytes: bytes) -> np.ndarray:
    img = _decode_image(image_bytes)
    landmarks, _det_score = _detect_largest_face(img)
    aligned = _align_face(img, landmarks)
    return _embed_face(aligned)


def _compare_faces_sync(document_image_bytes: bytes, live_image_bytes: bytes) -> FaceMatchResult:
    if not document_image_bytes:
        raise FaceServiceError("Document image is empty.")
    if not live_image_bytes:
        raise FaceServiceError("Live/selfie image is empty.")

    doc_embedding = _face_embedding(document_image_bytes)
    live_embedding = _face_embedding(live_image_bytes)

    cosine_similarity = float(np.dot(doc_embedding, live_embedding))
    # Map cosine similarity ([-1, 1], realistically ~[0, 0.7] for faces) onto a
    # 0-100 UI-friendly score without letting negative similarities go negative.
    score = max(0.0, min(1.0, (cosine_similarity + 1.0) / 2.0)) * 100.0
    verified = cosine_similarity >= _MATCH_THRESHOLD

    return FaceMatchResult(score=round(score, 2), verified=verified, cosine_similarity=round(cosine_similarity, 4))


async def compare_faces(document_image_bytes: bytes, live_image_bytes: bytes) -> FaceMatchResult:
    """
    Detects a face in the passport/ID photo and in a live/selfie capture,
    computes ArcFace embeddings for both, and returns their cosine-similarity
    based match score. Runs the CPU-bound ONNX inference off the event loop.
    """
    return await asyncio.to_thread(_compare_faces_sync, document_image_bytes, live_image_bytes)
