import { LucideIcon, ArrowDownRight, ArrowUpRight } from "lucide-react";
import { cx } from "@/lib/utils";

interface StatCardProps {
  label: string;
  value: string;
  icon: LucideIcon;
  trend: number;
  trendGoodDirection: "up" | "down";
  accent: "slate" | "red" | "cyan";
}

const accentStyles = {
  slate: "bg-slate-900 text-white",
  red: "bg-red-50 text-red-600",
  cyan: "bg-cyan-50 text-checkpoint-cyan",
};

export default function StatCard({
  label,
  value,
  icon: Icon,
  trend,
  trendGoodDirection,
  accent,
}: StatCardProps) {
  const isPositiveTrend = trend >= 0;
  const isGood = isPositiveTrend
    ? trendGoodDirection === "up"
    : trendGoodDirection === "down";

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-panel">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
            {label}
          </p>
          <p className="mt-2 text-2xl font-semibold text-slate-900">{value}</p>
        </div>
        <div className={cx("flex h-9 w-9 items-center justify-center rounded-md", accentStyles[accent])}>
          <Icon className="h-4.5 w-4.5" strokeWidth={2} />
        </div>
      </div>
      <div className="mt-3 flex items-center gap-1 text-xs">
        <span
          className={cx(
            "flex items-center gap-0.5 font-medium",
            isGood ? "text-emerald-600" : "text-red-600"
          )}
        >
          {isPositiveTrend ? (
            <ArrowUpRight className="h-3.5 w-3.5" />
          ) : (
            <ArrowDownRight className="h-3.5 w-3.5" />
          )}
          {Math.abs(trend).toFixed(1)}%
        </span>
        <span className="text-slate-400">vs. yesterday</span>
      </div>
    </div>
  );
}
