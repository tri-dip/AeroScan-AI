"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  ScanLine,
  Database,
  Settings,
  ShieldCheck,
} from "lucide-react";
import { cx } from "@/lib/utils";

const navItems = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/scan", label: "New Scan", icon: ScanLine },
  { href: "/database", label: "Database", icon: Database },
  { href: "/settings", label: "Settings", icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex h-screen w-60 shrink-0 flex-col border-r border-slate-200 bg-white">
      <div className="flex items-center gap-2.5 border-b border-slate-200 px-5 py-5">
        <div className="flex h-8 w-8 items-center justify-center rounded bg-slate-900">
          <ShieldCheck className="h-4.5 w-4.5 text-white" strokeWidth={2} />
        </div>
        <div className="leading-tight">
          <p className="text-sm font-semibold text-slate-900">Sentry Gate</p>
          <p className="text-[11px] text-slate-500">Checkpoint Terminal 4</p>
        </div>
      </div>

      <nav className="flex-1 space-y-0.5 px-3 py-4">
        {navItems.map((item) => {
          const active =
            item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cx(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                active
                  ? "bg-slate-900 text-white"
                  : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
              )}
            >
              <Icon className="h-4 w-4" strokeWidth={2} />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-slate-200 px-3 py-4">
        <div className="flex items-center gap-3 rounded-md bg-slate-50 px-3 py-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-200 text-xs font-semibold text-slate-600">
            RA
          </div>
          <div className="leading-tight">
            <p className="text-xs font-medium text-slate-900">R. Alvarez</p>
            <p className="text-[11px] text-slate-500">Duty Officer</p>
          </div>
        </div>
      </div>
    </aside>
  );
}
