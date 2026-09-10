"use client";

import { RadialBarChart, RadialBar, PolarAngleAxis } from "recharts";
import { RiskFactor } from "@/lib/types";
import { cx, riskTier } from "@/lib/utils";
import { CheckCircle2, XCircle, AlertCircle, ShieldAlert } from "lucide-react";

const tierStyles = {
  low: { text: "text-emerald-600", fill: "#059669" },
  medium: { text: "text-amber-600", fill: "#d97706" },
  high: { text: "text-red-600", fill: "#dc2626" },
};

const statusIcon = {
  pass: <CheckCircle2 className="h-4 w-4 text-emerald-500" />,
  warn: <AlertCircle className="h-4 w-4 text-amber-500" />,
  fail: <XCircle className="h-4 w-4 text-red-500" />,
};

interface RiskScorePanelProps {
  score: number;
  factors: RiskFactor[];
  onDecision: (decision: "approve" | "inspect" | "reject") => void;
}

export default function RiskScorePanel({ score, factors, onDecision }: RiskScorePanelProps) {
  const tier = riskTier(score);
  const style = tierStyles[tier];
  const chartData = [{ name: "risk", value: score, fill: style.fill }];

  return (
    <div className="flex h-full flex-col rounded-lg border border-slate-200 bg-white shadow-panel">
      <div className="flex items-center gap-2 border-b border-slate-200 px-4 py-3">
        <ShieldAlert className="h-4 w-4 text-slate-500" />
        <h2 className="text-sm font-semibold text-slate-900">Risk Assessment</h2>
      </div>

      <div className="flex flex-col items-center border-b border-slate-100 py-4">
        <div className="relative h-36 w-36">
          <RadialBarChart
            width={144}
            height={144}
            innerRadius="72%"
            outerRadius="100%"
            barSize={10}
            data={chartData}
            startAngle={90}
            endAngle={-270}
          >
            <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
            <RadialBar background={{ fill: "#f1f5f9" }} dataKey="value" cornerRadius={20} />
          </RadialBarChart>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className={cx("text-3xl font-bold tabular-nums", style.text)}>{score}</span>
            <span className="text-[11px] text-slate-400">out of 100</span>
          </div>
        </div>
        <span
          className={cx(
            "mt-2 rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide",
            tier === "high" && "bg-red-50 text-red-600",
            tier === "medium" && "bg-amber-50 text-amber-600",
            tier === "low" && "bg-emerald-50 text-emerald-600"
          )}
        >
          {tier === "high" ? "High Risk" : tier === "medium" ? "Elevated Risk" : "Low Risk"}
        </span>
      </div>

      <div className="scrollbar-thin flex-1 space-y-1 overflow-y-auto px-4 py-3">
        {factors.map((factor) => (
          <div
            key={factor.label}
            className="flex items-center justify-between gap-3 rounded-md px-2 py-2 hover:bg-slate-50"
          >
            <div className="flex items-center gap-2.5">
              {statusIcon[factor.status]}
              <div>
                <p className="text-[13px] font-medium text-slate-800">{factor.label}</p>
                <p className="text-[11px] text-slate-400">{factor.detail}</p>
              </div>
            </div>
            <span className="shrink-0 font-mono text-xs font-semibold text-slate-600">
              {factor.score}%
            </span>
          </div>
        ))}
      </div>

      <div className="space-y-2 border-t border-slate-200 p-4">
        <button
          onClick={() => onDecision("approve")}
          className="w-full rounded-md bg-emerald-600 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-emerald-700"
        >
          Approve Entry
        </button>
        <button
          onClick={() => onDecision("inspect")}
          className="w-full rounded-md bg-amber-500 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-amber-600"
        >
          Secondary Inspection
        </button>
        <button
          onClick={() => onDecision("reject")}
          className="w-full rounded-md bg-red-600 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-red-700"
        >
          Reject
        </button>
      </div>
    </div>
  );
}
