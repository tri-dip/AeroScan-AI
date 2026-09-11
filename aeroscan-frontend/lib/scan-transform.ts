import { FieldComparison, RiskFactor, ScanApiResponse, TamperedRegion } from "./types";

function normalize(value: unknown): string {
  return String(value ?? "")
    .replace(/[\s-]/g, "")
    .toUpperCase();
}

function display(value: unknown): string {
  return value == null || value === "" ? "—" : String(value);
}

export function buildFieldComparisons(res: ScanApiResponse): FieldComparison[] {
  const viz = res.viz_data ?? {};
  const mrz = res.mrz_decoded ?? {};

  const rows: Array<[string, unknown, unknown]> = [
    ["Surname", viz.last_name, mrz.surname],
    ["Given Names", viz.first_name, mrz.given_names],
    ["Document No.", viz.document_number, mrz.document_number],
    ["Nationality", null, mrz.nationality],
    ["Date of Birth", viz.dob, mrz.date_of_birth],
    ["Sex", viz.sex, mrz.sex],
    ["Date of Expiry", viz.expiry, mrz.date_of_expiry],
    ["Personal No.", null, mrz.personal_number],
  ];

  return rows
    .filter(([, viz_value, mrz_value]) => viz_value != null || mrz_value != null)
    .map(([field, viz_value, mrz_value]) => ({
      field,
      viz: display(viz_value),
      mrz: display(mrz_value),
      match: viz_value == null || mrz_value == null ? true : normalize(viz_value) === normalize(mrz_value),
    }));
}

export function buildRiskFactors(res: ScanApiResponse): RiskFactor[] {
  const mismatchCount = res.cross_check_mismatches?.length ?? 0;
  const faceScore = res.face_match_score ?? 0;
  const tampering = res.tampering_score ?? 0;

  return [
    {
      label: "MRZ Checksum",
      detail: "Digit verification on document number, DOB, expiry & composite fields",
      score: res.mrz_checksum_valid ? 100 : 0,
      status: res.mrz_checksum_valid ? "pass" : "fail",
    },
    {
      label: "VIZ / MRZ Cross-Check",
      detail:
        mismatchCount > 0
          ? `${mismatchCount} field mismatch${mismatchCount > 1 ? "es" : ""} detected`
          : "Printed fields agree with the machine-readable zone",
      score: res.field_cross_check_passed ? 100 : 0,
      status: res.field_cross_check_passed ? "pass" : "fail",
    },
    {
      label: "Face Match",
      detail: "Document portrait vs. live selfie capture similarity",
      score: Math.round(faceScore),
      status: res.face_match_verified ? "pass" : res.face_match_score == null ? "warn" : "fail",
    },
    {
      label: "Document Forensics",
      detail: describeForensicsFlags(res.flags),
      score: Math.round(Math.max(0, 100 - tampering)),
      status: tampering < 30 ? "pass" : tampering < 60 ? "warn" : "fail",
    },
  ];
}

const FORENSICS_FLAG_TEXT: Record<string, string> = {
  ELA_ANOMALY_DETECTED: "compression-error hotspots",
  SUSPICIOUS_PHOTO_SEAM: "sharp edge around the portrait boundary",
  PHOTO_ELA_MISMATCH: "compression mismatch on the portrait",
  LOCALIZED_NOISE_ANOMALY: "irregular sensor-noise pattern",
};

function describeForensicsFlags(flags: string[]): string {
  const hits = flags.map((f) => FORENSICS_FLAG_TEXT[f]).filter(Boolean);
  return hits.length > 0
    ? `Error-level analysis detected: ${hits.join(", ")}.`
    : "Error-level analysis found no compression or noise anomalies.";
}

const FACE_REGION_FLAGS: Record<string, string> = {
  SUSPICIOUS_PHOTO_SEAM: "sharp edge discontinuity around the portrait boundary",
  PHOTO_ELA_MISMATCH: "compression-history mismatch between the portrait and the surrounding document",
  FACE_MATCH_FAILED: "does not match the live selfie capture",
};

export function buildTamperedRegions(
  res: ScanApiResponse,
  imageSize: { width: number; height: number }
): TamperedRegion[] {
  const bbox = res.face_match_bbox;
  if (!bbox || bbox.length !== 4 || !imageSize.width || !imageSize.height) return [];

  const hitFlags = res.flags.filter((f) => f in FACE_REGION_FLAGS);
  if (hitFlags.length === 0) return [];

  const [x1, y1, x2, y2] = bbox;
  const severity: TamperedRegion["severity"] = hitFlags.length > 1 ? "high" : "medium";

  return [
    {
      id: "face-region",
      label: "Portrait Region Anomaly",
      detail: `Detected: ${hitFlags.map((f) => FACE_REGION_FLAGS[f]).join("; ")}.`,
      confidence: Math.round(res.tampering_score ?? 0),
      left: (x1 / imageSize.width) * 100,
      top: (y1 / imageSize.height) * 100,
      width: ((x2 - x1) / imageSize.width) * 100,
      height: ((y2 - y1) / imageSize.height) * 100,
      severity,
    },
  ];
}

export function mapDecision(
  finalDecision: string | null
): "approve" | "inspect" | "reject" | null {
  switch (finalDecision) {
    case "APPROVE":
      return "approve";
    case "REJECT":
      return "reject";
    case "MANUAL_REVIEW":
      return "inspect";
    default:
      return null;
  }
}
