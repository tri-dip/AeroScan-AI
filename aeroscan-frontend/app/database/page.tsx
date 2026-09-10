import Topbar from "@/components/Topbar";
import ScansTable from "@/components/ScansTable";
import { recentScans } from "@/lib/mock-data";
import { Search } from "lucide-react";

export default function DatabasePage() {
  return (
    <>
      <Topbar title="Document Database" subtitle="All processed identity records" />
      <div className="flex-1 space-y-4 p-6">
        <div className="flex items-center gap-2 rounded-md border border-slate-200 bg-white px-3 py-2 shadow-panel">
          <Search className="h-4 w-4 text-slate-400" />
          <input
            className="w-full text-sm text-slate-700 outline-none placeholder:text-slate-400"
            placeholder="Search by name, ID, or nationality…"
          />
        </div>
        <ScansTable scans={recentScans} />
      </div>
    </>
  );
}
