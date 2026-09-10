import { ScanRecord } from "@/lib/types";
import { cx, formatTime, statusStyles } from "@/lib/utils";
import { FileText } from "lucide-react";

export default function ScansTable({ scans }: { scans: ScanRecord[] }) {
  return (
    <div className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-panel">
      <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
        <h2 className="text-sm font-semibold text-slate-900">Recent Scans</h2>
        <button className="text-xs font-medium text-slate-500 hover:text-slate-900">
          View all
        </button>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-slate-100 text-xs uppercase tracking-wide text-slate-400">
              <th className="px-5 py-3 font-medium">ID</th>
              <th className="px-5 py-3 font-medium">Name</th>
              <th className="px-5 py-3 font-medium">Document</th>
              <th className="px-5 py-3 font-medium">Time</th>
              <th className="px-5 py-3 font-medium">Risk</th>
              <th className="px-5 py-3 font-medium">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {scans.map((scan) => {
              const style = statusStyles[scan.status];
              return (
                <tr key={scan.id} className="transition-colors hover:bg-slate-50/80">
                  <td className="px-5 py-3.5 font-mono text-xs text-slate-500">
                    {scan.id}
                  </td>
                  <td className="px-5 py-3.5">
                    <div className="flex items-center gap-2.5">
                      <div className="flex h-7 w-7 items-center justify-center rounded-full bg-slate-100 text-[10px] font-semibold text-slate-500">
                        {scan.name
                          .split(" ")
                          .map((n) => n[0])
                          .slice(0, 2)
                          .join("")}
                      </div>
                      <div>
                        <p className="font-medium text-slate-900">{scan.name}</p>
                        <p className="text-xs text-slate-400">{scan.nationality}</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-5 py-3.5 text-slate-600">
                    <span className="inline-flex items-center gap-1.5">
                      <FileText className="h-3.5 w-3.5 text-slate-400" />
                      {scan.documentType}
                    </span>
                  </td>
                  <td className="px-5 py-3.5 text-slate-500">{formatTime(scan.timestamp)}</td>
                  <td className="px-5 py-3.5">
                    {scan.status === "pending" ? (
                      <span className="text-slate-400">—</span>
                    ) : (
                      <span
                        className={cx(
                          "font-mono text-xs font-semibold",
                          scan.riskScore >= 70 ? "text-red-600" : "text-slate-600"
                        )}
                      >
                        {scan.riskScore}%
                      </span>
                    )}
                  </td>
                  <td className="px-5 py-3.5">
                    <span
                      className={cx(
                        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ring-1 ring-inset",
                        style.bg,
                        style.text,
                        style.ring
                      )}
                    >
                      <span className={cx("h-1.5 w-1.5 rounded-full", style.dot)} />
                      {style.label}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
