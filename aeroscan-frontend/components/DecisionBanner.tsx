import { CheckCircle2, Eye, XOctagon } from "lucide-react";
import { cx } from "@/lib/utils";

const config = {
  approve: {
    icon: CheckCircle2,
    text: "Entry approved. Traveler cleared to proceed.",
    classes: "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
  },
  inspect: {
    icon: Eye,
    text: "Routed to secondary inspection. Officer notified.",
    classes: "bg-amber-50 text-amber-700 ring-amber-600/20",
  },
  reject: {
    icon: XOctagon,
    text: "Entry rejected. Case logged for review.",
    classes: "bg-red-50 text-red-700 ring-red-600/20",
  },
};

export default function DecisionBanner({
  decision,
}: {
  decision: "approve" | "inspect" | "reject";
}) {
  const { icon: Icon, text, classes } = config[decision];
  return (
    <div
      className={cx(
        "flex items-center gap-2.5 rounded-lg px-4 py-3 text-sm font-medium ring-1 ring-inset",
        classes
      )}
    >
      <Icon className="h-4.5 w-4.5" />
      {text}
    </div>
  );
}
