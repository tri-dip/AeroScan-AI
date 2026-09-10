import { ScanStatus } from "./types";

export function cx(...classes: Array<string | false | null | undefined>) {
  return classes.filter(Boolean).join(" ");
}

export function formatTime(iso: string) {
  return new Date(iso).toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatFullTimestamp(iso: string) {
  return new Date(iso).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export const statusStyles: Record<
  ScanStatus,
  { label: string; dot: string; text: string; bg: string; ring: string }
> = {
  cleared: {
    label: "Cleared",
    dot: "bg-emerald-500",
    text: "text-emerald-700",
    bg: "bg-emerald-50",
    ring: "ring-emerald-600/20",
  },
  high_risk: {
    label: "High Risk",
    dot: "bg-red-500",
    text: "text-red-700",
    bg: "bg-red-50",
    ring: "ring-red-600/20",
  },
  pending: {
    label: "Pending",
    dot: "bg-amber-500",
    text: "text-amber-700",
    bg: "bg-amber-50",
    ring: "ring-amber-600/20",
  },
};

export function riskTier(score: number): "low" | "medium" | "high" {
  if (score >= 70) return "high";
  if (score >= 35) return "medium";
  return "low";
}
