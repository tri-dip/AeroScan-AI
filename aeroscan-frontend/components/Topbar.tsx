"use client";

import { Bell, Wifi } from "lucide-react";
import { useEffect, useState } from "react";

export default function Topbar({ title, subtitle }: { title: string; subtitle?: string }) {
  const [now, setNow] = useState<Date | null>(null);

  useEffect(() => {
    setNow(new Date());
    const timer = setInterval(() => setNow(new Date()), 1000 * 30);
    return () => clearInterval(timer);
  }, []);

  return (
    <header className="flex h-16 shrink-0 items-center justify-between border-b border-slate-200 bg-white px-6">
      <div>
        <h1 className="text-[15px] font-semibold text-slate-900">{title}</h1>
        {subtitle && <p className="text-xs text-slate-500">{subtitle}</p>}
      </div>

      <div className="flex items-center gap-5">
        <div className="flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700 ring-1 ring-inset ring-emerald-600/20">
          <Wifi className="h-3.5 w-3.5" strokeWidth={2.25} />
          System Online
        </div>
        <button
          type="button"
          className="relative flex h-8 w-8 items-center justify-center rounded-md text-slate-500 hover:bg-slate-100 hover:text-slate-900"
          aria-label="Notifications"
        >
          <Bell className="h-4 w-4" />
          <span className="absolute right-1.5 top-1.5 h-1.5 w-1.5 rounded-full bg-red-500" />
        </button>
        <div className="text-xs tabular-nums text-slate-400 font-mono">
          {now
            ? now.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" })
            : "--:--"}
        </div>
      </div>
    </header>
  );
}
