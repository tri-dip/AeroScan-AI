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

export type WorkflowState = "idle" | "scanning" | "results";
