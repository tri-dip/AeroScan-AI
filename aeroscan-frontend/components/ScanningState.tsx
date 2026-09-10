import { Loader2 } from "lucide-react";

const steps = [
  "Extracting VIZ text fields",
  "Decoding MRZ checksum",
  "Running error-level analysis",
  "Cross-referencing watchlist",
];

export default function ScanningState() {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-6 rounded-lg border border-slate-200 bg-white p-10 shadow-panel">
      <div className="relative flex h-16 w-16 items-center justify-center">
        <Loader2 className="h-16 w-16 animate-spin text-checkpoint-cyan" strokeWidth={1.5} />
      </div>
      <div className="text-center">
        <p className="text-sm font-semibold text-slate-900">Analyzing document…</p>
        <p className="mt-1 text-xs text-slate-500">This usually takes a few seconds</p>
      </div>
      <div className="w-full max-w-xs space-y-2.5">
        {steps.map((step, i) => (
          <div key={step} className="flex items-center gap-2.5 text-xs text-slate-500">
            <span
              className="h-1.5 w-1.5 shrink-0 rounded-full bg-checkpoint-cyan"
              style={{ animationDelay: `${i * 0.2}s` }}
            />
            {step}
          </div>
        ))}
      </div>
    </div>
  );
}
