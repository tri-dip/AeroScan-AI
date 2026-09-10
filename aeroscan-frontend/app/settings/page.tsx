import Topbar from "@/components/Topbar";
import { Sliders } from "lucide-react";

const settingsGroups = [
  {
    title: "Detection Sensitivity",
    items: [
      { label: "Error Level Analysis threshold", value: "High" },
      { label: "MRZ checksum enforcement", value: "Strict" },
      { label: "Face match minimum confidence", value: "92%" },
    ],
  },
  {
    title: "Terminal",
    items: [
      { label: "Terminal ID", value: "Checkpoint Terminal 4" },
      { label: "Assigned officer", value: "R. Alvarez" },
      { label: "Auto-log to database", value: "Enabled" },
    ],
  },
];

export default function SettingsPage() {
  return (
    <>
      <Topbar title="Settings" subtitle="System configuration" />
      <div className="flex-1 space-y-4 p-6">
        {settingsGroups.map((group) => (
          <div key={group.title} className="rounded-lg border border-slate-200 bg-white shadow-panel">
            <div className="flex items-center gap-2 border-b border-slate-200 px-5 py-3">
              <Sliders className="h-4 w-4 text-slate-500" />
              <h2 className="text-sm font-semibold text-slate-900">{group.title}</h2>
            </div>
            <div className="divide-y divide-slate-100">
              {group.items.map((item) => (
                <div key={item.label} className="flex items-center justify-between px-5 py-3.5 text-sm">
                  <span className="text-slate-600">{item.label}</span>
                  <span className="font-mono text-xs font-medium text-slate-900">{item.value}</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </>
  );
}
