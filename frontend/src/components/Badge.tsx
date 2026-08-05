import type { ReactNode } from "react";

type Tone = "ok" | "warn" | "danger" | "muted" | "info";

export function Badge({ tone, children }: { tone: Tone; children: ReactNode }) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}

/** A minimum-wage breach is a wage violation, not a tax outcome — make it loud. */
export function WageBadge({ ok }: { ok: boolean }) {
  return <Badge tone={ok ? "ok" : "danger"}>{ok ? "OK" : "BREACH"}</Badge>;
}

export function StatusBadge({
  restructure,
  saturated,
}: {
  restructure: boolean;
  saturated: boolean;
}) {
  if (!restructure) return <Badge tone="muted">Held harmless</Badge>;
  if (saturated) return <Badge tone="warn">Saturated</Badge>;
  return <Badge tone="info">Optimized</Badge>;
}
