import Topbar from "@/components/Topbar";
import StatCard from "@/components/StatCard";
import ScansTable from "@/components/ScansTable";
import { dashboardSummary, recentScans } from "@/lib/mock-data";
import { ScanLine, ShieldAlert, Timer } from "lucide-react";
import Link from "next/link";

export default function DashboardPage() {
  return (
    <>
      <Topbar title="Dashboard" subtitle="Checkpoint Terminal 4 — Overview" />

      <div className="flex-1 space-y-6 p-6">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <StatCard
            label="Total Scans Today"
            value={dashboardSummary.totalScansToday.toString()}
            icon={ScanLine}
            trend={dashboardSummary.scansTrend}
            trendGoodDirection="up"
            accent="slate"
          />
          <StatCard
            label="Fakes Detected"
            value={dashboardSummary.fakesDetected.toString()}
            icon={ShieldAlert}
            trend={dashboardSummary.fakesTrend}
            trendGoodDirection="down"
            accent="red"
          />
          <StatCard
            label="Avg. Processing Time"
            value={`${dashboardSummary.avgProcessingTimeSeconds.toFixed(1)}s`}
            icon={Timer}
            trend={dashboardSummary.timeTrend}
            trendGoodDirection="down"
            accent="cyan"
          />
        </div>

        <div className="flex items-center justify-between rounded-lg border border-slate-200 bg-white px-5 py-4 shadow-panel">
          <div>
            <p className="text-sm font-semibold text-slate-900">Ready for the next traveler</p>
            <p className="text-xs text-slate-500">
              Start a new screening session at the terminal.
            </p>
          </div>
          <Link
            href="/scan"
            className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-slate-800"
          >
            New Scan
          </Link>
        </div>

        <ScansTable scans={recentScans} />
      </div>
    </>
  );
}
