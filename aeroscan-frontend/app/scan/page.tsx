"use client";

import { useEffect, useMemo, useState } from "react";
import Topbar from "@/components/Topbar";
import DocumentUpload from "@/components/DocumentUpload";
import SelfieCapture from "@/components/SelfieCapture";
import ScanningState from "@/components/ScanningState";
import AIViewer from "@/components/AIViewer";
import ExtractedData from "@/components/ExtractedData";
import RiskScorePanel from "@/components/RiskScorePanel";
import DecisionBanner from "@/components/DecisionBanner";
import { scanDocument, ScanApiError } from "@/lib/api";
import {
  buildFieldComparisons,
  buildRiskFactors,
  buildTamperedRegions,
  mapDecision,
} from "@/lib/scan-transform";
import { ScanApiResponse, WorkflowState } from "@/lib/types";
import { AlertTriangle, RotateCcw } from "lucide-react";

export default function ScanPage() {
  const [state, setState] = useState<WorkflowState>("idle");
  const [documentFile, setDocumentFile] = useState<File | null>(null);
  const [selfieFile, setSelfieFile] = useState<Blob | null>(null);
  const [result, setResult] = useState<ScanApiResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [decision, setDecision] = useState<"approve" | "inspect" | "reject" | null>(null);
  const [submittedAt, setSubmittedAt] = useState<string | null>(null);
  const [imageSize, setImageSize] = useState<{ width: number; height: number } | null>(null);

  const imageUrl = useMemo(
    () => (documentFile ? URL.createObjectURL(documentFile) : null),
    [documentFile]
  );
  const selfieUrl = useMemo(
    () => (selfieFile ? URL.createObjectURL(selfieFile) : null),
    [selfieFile]
  );

  useEffect(() => {
    return () => {
      if (imageUrl) URL.revokeObjectURL(imageUrl);
    };
  }, [imageUrl]);

  useEffect(() => {
    return () => {
      if (selfieUrl) URL.revokeObjectURL(selfieUrl);
    };
  }, [selfieUrl]);

  useEffect(() => {
    if (!documentFile) {
      setImageSize(null);
      return;
    }
    let cancelled = false;
    createImageBitmap(documentFile)
      .then((bitmap) => {
        if (!cancelled) setImageSize({ width: bitmap.width, height: bitmap.height });
        bitmap.close();
      })
      .catch(() => setImageSize(null));
    return () => {
      cancelled = true;
    };
  }, [documentFile]);

  function handleFileSelected(file: File | null) {
    if (!file) return;
    setDocumentFile(file);
    setDecision(null);
    setErrorMessage(null);
    setState("selfie");
  }

  async function handleSelfieCaptured(selfie: Blob) {
    if (!documentFile) return;
    setSelfieFile(selfie);
    setState("scanning");
    setSubmittedAt(new Date().toISOString());

    try {
      const response = await scanDocument(documentFile, selfie);
      setResult(response);
      setState("results");
    } catch (err) {
      setErrorMessage(
        err instanceof ScanApiError ? err.message : "Unexpected error while scanning the document."
      );
      setState("error");
    }
  }

  function reset() {
    setState("idle");
    setDocumentFile(null);
    setSelfieFile(null);
    setResult(null);
    setDecision(null);
    setErrorMessage(null);
  }

  const fields = result ? buildFieldComparisons(result) : [];
  const riskFactors = result ? buildRiskFactors(result) : [];
  const riskScore = result?.risk_score != null ? Math.round(result.risk_score) : 0;
  const recommendedDecision = result ? mapDecision(result.final_decision) : null;
  const tamperedRegions = result && imageSize ? buildTamperedRegions(result, imageSize) : [];

  return (
    <>
      <Topbar
        title="Screening Terminal"
        subtitle={
          state === "idle"
            ? "Awaiting document"
            : state === "selfie"
            ? "Awaiting live selfie capture"
            : state === "scanning"
            ? "Processing…"
            : state === "error"
            ? "Scan failed"
            : `Case: ${result?.file_name ?? ""}`
        }
      />

      <div className="flex-1 p-6">
        {state === "idle" && (
          <div className="h-[calc(100vh-8.5rem)] rounded-lg border border-slate-200 bg-white shadow-panel">
            <DocumentUpload onFileSelected={handleFileSelected} />
          </div>
        )}

        {state === "selfie" && (
          <div className="h-[calc(100vh-8.5rem)] rounded-lg border border-slate-200 bg-white shadow-panel">
            <SelfieCapture onCaptured={handleSelfieCaptured} onBack={reset} />
          </div>
        )}

        {state === "scanning" && (
          <div className="h-[calc(100vh-8.5rem)]">
            <ScanningState />
          </div>
        )}

        {state === "error" && (
          <div className="flex h-[calc(100vh-8.5rem)] flex-col items-center justify-center gap-4 rounded-lg border border-slate-200 bg-white p-10 text-center shadow-panel">
            <AlertTriangle className="h-10 w-10 text-red-500" />
            <p className="text-sm font-semibold text-slate-900">Scan failed</p>
            <p className="max-w-sm text-xs text-slate-500">{errorMessage}</p>
            <button
              onClick={reset}
              className="rounded-md bg-slate-900 px-4 py-2 text-xs font-medium text-white hover:bg-slate-800"
            >
              Try again
            </button>
          </div>
        )}

        {state === "results" && result && (
          <div className="space-y-4">
            {decision && <DecisionBanner decision={decision} />}

            {result.errors.length > 0 && (
              <div className="flex items-start gap-2.5 rounded-lg bg-amber-50 px-4 py-3 text-xs text-amber-700 ring-1 ring-inset ring-amber-600/20">
                <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                <div className="space-y-0.5">
                  {result.errors.map((message) => (
                    <p key={message}>{message}</p>
                  ))}
                </div>
              </div>
            )}

            <div className="flex items-center justify-between">
              <p className="text-xs text-slate-500">
                Submitted at {submittedAt ? new Date(submittedAt).toLocaleTimeString() : "—"}
              </p>
              <button
                onClick={reset}
                className="flex items-center gap-1.5 rounded-md border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50"
              >
                <RotateCcw className="h-3.5 w-3.5" />
                New Document
              </button>
            </div>

            <div className="grid grid-cols-1 gap-4 lg:grid-cols-12">
              <div className="lg:col-span-5">
                <div className="h-[560px]">
                  <AIViewer
                    imageUrl={imageUrl ?? ""}
                    tamperedRegions={tamperedRegions}
                    heatmapUrl={result.ela_heatmap_base64}
                    selfieUrl={selfieUrl}
                  />
                </div>
              </div>
              <div className="lg:col-span-4">
                <div className="h-[560px]">
                  <ExtractedData fields={fields} />
                </div>
              </div>
              <div className="lg:col-span-3">
                <div className="h-[560px]">
                  <RiskScorePanel
                    score={riskScore}
                    factors={riskFactors}
                    recommendation={recommendedDecision}
                    onDecision={(d) => setDecision(d)}
                  />
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
