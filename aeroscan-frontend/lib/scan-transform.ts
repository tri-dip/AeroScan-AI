import { FieldComparison, RiskFactor, ScanApiResponse } from "./types";

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
      detail: "Error-level analysis tampering score",
      score: Math.round(Math.max(0, 100 - tampering)),
      status: tampering < 30 ? "pass" : tampering < 60 ? "warn" : "fail",
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
