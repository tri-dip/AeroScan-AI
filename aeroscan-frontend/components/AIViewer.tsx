"use client";

import { useState } from "react";
import Image from "next/image";
import { TamperedRegion } from "@/lib/types";
import { cx } from "@/lib/utils";
import { Flame, ScanEye } from "lucide-react";

const severityRing: Record<TamperedRegion["severity"], string> = {
  high: "border-red-500 shadow-[0_0_0_2px_rgba(239,68,68,0.25),0_0_18px_rgba(239,68,68,0.55)]",
  medium: "border-amber-500 shadow-[0_0_0_2px_rgba(245,158,11,0.2),0_0_14px_rgba(245,158,11,0.45)]",
  low: "border-yellow-400 shadow-[0_0_0_2px_rgba(250,204,21,0.15),0_0_10px_rgba(250,204,21,0.35)]",
};

const severityDot: Record<TamperedRegion["severity"], string> = {
  high: "bg-red-500",
  medium: "bg-amber-500",
  low: "bg-yellow-400",
};

export default function AIViewer({
  imageUrl,
  tamperedRegions,
  heatmapUrl,
  selfieUrl,
}: {
  imageUrl: string;
  tamperedRegions: TamperedRegion[];
  heatmapUrl?: string | null;
  selfieUrl?: string | null;
}) {
  const [activeRegion, setActiveRegion] = useState<string | null>(null);
  const [showHeatmap, setShowHeatmap] = useState(false);

  return (
    <div className="flex h-full flex-col rounded-lg border border-slate-200 bg-white shadow-panel">
      <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3">
        <div className="flex items-center gap-2">
          <ScanEye className="h-4 w-4 text-slate-500" />
          <h2 className="text-sm font-semibold text-slate-900">Forensic Viewer</h2>
        </div>
        <div className="flex items-center gap-2">
          {heatmapUrl && (
            <button
              onClick={() => setShowHeatmap((v) => !v)}
              className={cx(
                "flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[11px] font-medium ring-1 ring-inset transition-colors",
                showHeatmap
                  ? "bg-checkpoint-cyan/10 text-checkpoint-cyan ring-checkpoint-cyan/30"
                  : "bg-slate-50 text-slate-500 ring-slate-500/20 hover:bg-slate-100"
              )}
            >
              <Flame className="h-3 w-3" />
              ELA Heatmap
            </button>
          )}
          <span
            className={cx(
              "rounded-full px-2.5 py-0.5 text-[11px] font-medium ring-1 ring-inset",
              tamperedRegions.length > 0
                ? "bg-red-50 text-red-600 ring-red-600/20"
                : "bg-emerald-50 text-emerald-700 ring-emerald-600/20"
            )}
          >
            {tamperedRegions.length} anomalies flagged
          </span>
        </div>
      </div>

      <div className="relative flex-1 overflow-hidden tech-grid p-4">
        <div className="relative mx-auto aspect-[3/2] w-full max-w-xl overflow-hidden rounded-md border border-slate-300 bg-slate-900">
          <Image
            src={imageUrl}
            alt="Uploaded identity document"
            fill
            unoptimized
            className="object-contain opacity-90"
          />

          {showHeatmap && heatmapUrl && (
            <Image
              src={heatmapUrl}
              alt="Error-level analysis heatmap"
              fill
              unoptimized
              className="object-contain opacity-70 mix-blend-screen"
            />
          )}

          {/* Simulated active scan sweep */}
          <div className="pointer-events-none absolute inset-0 overflow-hidden">
            <div className="absolute left-0 right-0 h-16 bg-gradient-to-b from-cyan-400/0 via-cyan-300/25 to-cyan-400/0 animate-scanline" />
          </div>

          {selfieUrl && (
            <div className="absolute bottom-2 right-2 w-16 overflow-hidden rounded-md border-2 border-white/80 shadow-lg sm:w-20">
              <div className="relative aspect-square">
                <Image
                  src={selfieUrl}
                  alt="Live selfie capture"
                  fill
                  unoptimized
                  className="object-cover"
                />
              </div>
              <div className="bg-slate-900/80 py-0.5 text-center text-[9px] font-medium uppercase tracking-wide text-white">
                Live Capture
              </div>
            </div>
          )}

          {tamperedRegions.map((region) => (
            <div
              key={region.id}
              onMouseEnter={() => setActiveRegion(region.id)}
              onMouseLeave={() => setActiveRegion(null)}
              className={cx(
                "absolute cursor-pointer rounded-sm border-2 bg-red-500/5 transition-all animate-pulseGlow",
                severityRing[region.severity]
              )}
              style={{
                left: `${region.left}%`,
                top: `${region.top}%`,
                width: `${region.width}%`,
                height: `${region.height}%`,
              }}
            >
              <span
                className={cx(
                  "absolute -left-1.5 -top-1.5 h-3 w-3 rounded-full ring-2 ring-white",
                  severityDot[region.severity]
                )}
              />

              {activeRegion === region.id && (
                <div className="absolute left-1/2 top-full z-10 mt-2 w-60 -translate-x-1/2 rounded-md bg-slate-900 p-3 text-left text-white shadow-xl">
                  <div className="absolute -top-1 left-1/2 h-2 w-2 -translate-x-1/2 rotate-45 bg-slate-900" />
                  <p className="text-xs font-semibold text-white">{region.label}</p>
                  <p className="mt-1 text-[11px] leading-relaxed text-slate-300">
                    {region.detail}
                  </p>
                  <div className="mt-2 flex items-center gap-1.5">
                    <div className="h-1 flex-1 overflow-hidden rounded-full bg-slate-700">
                      <div
                        className="h-full rounded-full bg-red-500"
                        style={{ width: `${region.confidence}%` }}
                      />
                    </div>
                    <span className="font-mono text-[11px] font-semibold text-red-400">
                      {region.confidence}%
                    </span>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="flex items-center gap-4 border-t border-slate-200 px-4 py-2.5 text-[11px] text-slate-500">
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-red-500" /> High severity
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-amber-500" /> Medium severity
        </span>
        <span className="ml-auto">Hover a region for details</span>
      </div>
    </div>
  );
}
