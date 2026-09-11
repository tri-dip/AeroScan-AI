import { FieldComparison } from "@/lib/types";
import { cx } from "@/lib/utils";
import { AlertTriangle, CheckCircle2, FileScan } from "lucide-react";

export default function ExtractedData({ fields }: { fields: FieldComparison[] }) {
  const mismatchCount = fields.filter((f) => !f.match).length;

  return (
    <div className="flex h-full flex-col rounded-lg border border-slate-200 bg-white shadow-panel">
      <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3">
        <div className="flex items-center gap-2">
          <FileScan className="h-4 w-4 text-slate-500" />
          <h2 className="text-sm font-semibold text-slate-900">Data Cross-Check</h2>
        </div>
        {fields.length === 0 ? (
          <span className="flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-0.5 text-[11px] font-medium text-slate-500 ring-1 ring-inset ring-slate-500/20">
            <AlertTriangle className="h-3 w-3" />
            No data extracted
          </span>
        ) : mismatchCount > 0 ? (
          <span className="flex items-center gap-1 rounded-full bg-red-50 px-2.5 py-0.5 text-[11px] font-medium text-red-600 ring-1 ring-inset ring-red-600/20">
            <AlertTriangle className="h-3 w-3" />
            {mismatchCount} mismatch{mismatchCount > 1 ? "es" : ""}
          </span>
        ) : (
          <span className="flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-0.5 text-[11px] font-medium text-emerald-700 ring-1 ring-inset ring-emerald-600/20">
            <CheckCircle2 className="h-3 w-3" />
            All fields match
          </span>
        )}
      </div>

      <div className="grid grid-cols-2 border-b border-slate-200 bg-slate-50 px-4 py-2 text-[11px] font-medium uppercase tracking-wide text-slate-400">
        <span>VIZ · Printed</span>
        <span>MRZ · Machine Read</span>
      </div>

      <div className="scrollbar-thin flex-1 divide-y divide-slate-100 overflow-y-auto">
        {fields.length === 0 && (
          <p className="px-4 py-6 text-center text-xs text-slate-400">
            No VIZ or MRZ fields could be extracted from this document.
          </p>
        )}
        {fields.map((field) => (
          <div
            key={field.field}
            className={cx(
              "grid grid-cols-2 px-4 py-3 text-sm",
              !field.match && "bg-red-50/60"
            )}
          >
            <div className="pr-3">
              <p className="text-[11px] text-slate-400">{field.field}</p>
              <p
                className={cx(
                  "font-mono text-[13px]",
                  !field.match ? "font-semibold text-red-600" : "text-slate-800"
                )}
              >
                {field.viz}
              </p>
            </div>
            <div className="flex items-start justify-between pl-3">
              <div>
                <p className="text-[11px] text-slate-400">{field.field}</p>
                <p
                  className={cx(
                    "font-mono text-[13px]",
                    !field.match ? "font-semibold text-red-600" : "text-slate-800"
                  )}
                >
                  {field.mrz}
                </p>
              </div>
              {!field.match && (
                <span
                  className="mt-0.5 h-2 w-2 shrink-0 animate-pulseGlow rounded-full bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.8)]"
                  aria-hidden
                />
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
