"use client";

import { useState } from "react";
import Topbar from "@/components/Topbar";
import DocumentUpload from "@/components/DocumentUpload";
import ScanningState from "@/components/ScanningState";
import AIViewer from "@/components/AIViewer";
import ExtractedData from "@/components/ExtractedData";
import RiskScorePanel from "@/components/RiskScorePanel";
import DecisionBanner from "@/components/DecisionBanner";
import { mockDocumentCase } from "@/lib/mock-data";
import { WorkflowState } from "@/lib/types";
import { RotateCcw } from "lucide-react";

export default function ScanPage() {
  const [state, setState] = useState<WorkflowState>("idle");
  const [decision, setDecision] = useState<"approve" | "inspect" | "reject" | null>(null);

  function handleFileSelected(file: File | null) {
    if (!file) return;
    setState("scanning");
    setDecision(null);
    // Simulate backend AI processing latency for the demo.
    setTimeout(() => setState("results"), 2200);
  }

  function reset() {
    setState("idle");
    setDecision(null);
  }

  return (
    <>
      <Topbar
        title="Screening Terminal"
        subtitle={
          state === "idle"
            ? "Awaiting document"
            : state === "scanning"
            ? "Processing…"
            : `Case ${mockDocumentCase.documentId}`
        }
      />

      <div className="flex-1 p-6">
        {state === "idle" && (
          <div className="h-[calc(100vh-8.5rem)] rounded-lg border border-slate-200 bg-white shadow-panel">
            <DocumentUpload onFileSelected={handleFileSelected} />
          </div>
        )}

        {state === "scanning" && (
          <div className="h-[calc(100vh-8.5rem)]">
            <ScanningState />
          </div>
        )}

        {state === "results" && (
          <div className="space-y-4">
            {decision && <DecisionBanner decision={decision} />}

            <div className="flex items-center justify-between">
              <p className="text-xs text-slate-500">
                Submitted at {new Date(mockDocumentCase.submittedAt).toLocaleTimeString()}
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
                    imageUrl={mockDocumentCase.imageUrl}
                    tamperedRegions={mockDocumentCase.tamperedRegions}
                  />
                </div>
              </div>
              <div className="lg:col-span-4">
                <div className="h-[560px]">
                  <ExtractedData fields={mockDocumentCase.fields} />
                </div>
              </div>
              <div className="lg:col-span-3">
                <div className="h-[560px]">
                  <RiskScorePanel
                    score={mockDocumentCase.riskScore}
                    factors={mockDocumentCase.riskFactors}
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
