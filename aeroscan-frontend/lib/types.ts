export type ScanStatus = "cleared" | "high_risk" | "pending";

export interface ScanRecord {
  id: string;
  name: string;
  nationality: string;
  documentType: "Passport" | "Visa" | "National ID";
  timestamp: string;
  status: ScanStatus;
  riskScore: number;
  officer: string;
}

export interface TamperedRegion {
  id: string;
  label: string;
  detail: string;
  confidence: number;
  left: number;
  top: number;
  width: number;
  height: number;
  severity: "high" | "medium" | "low";
}

export interface FieldComparison {
  field: string;
  viz: string;
  mrz: string;
  match: boolean;
}

export interface RiskFactor {
  label: string;
  detail: string;
  score: number;
  status: "pass" | "warn" | "fail";
}

export interface DocumentCase {
  documentId: string;
  imageUrl: string;
  submittedAt: string;
  tamperedRegions: TamperedRegion[];
  fields: FieldComparison[];
  riskScore: number;
  riskFactors: RiskFactor[];
  verdictHint: "approve" | "inspect" | "reject";
}

export type WorkflowState = "idle" | "selfie" | "scanning" | "results" | "error";

// Mirrors aeroscan-backend's app.schemas.api_models.ScanResponse.
export interface ScanApiResponse {
  file_name: string;
  document_type: string | null;
  station_id: string | null;

  viz_data: Record<string, string | null> | null;
  mrz_data: Record<string, string | null> | null;
  mrz_decoded: Record<string, string | null> | null;

  mrz_checksum_valid: boolean | null;
  mrz_checksum_results: Record<string, boolean> | null;
  cross_check_mismatches: string[] | null;
  field_cross_check_passed: boolean | null;

  tampering_score: number | null;
  ela_heatmap_base64: string | null;
  face_match_score: number | null;
  face_match_similarity: number | null;
  face_match_verified: boolean | null;
  face_match_bbox: [number, number, number, number] | null;

  risk_level: string | null;
  risk_score: number | null;
  risk_brief: string | null;
  final_decision: string | null;

  flags: string[];
  errors: string[];
  node_trace: string[];
}
