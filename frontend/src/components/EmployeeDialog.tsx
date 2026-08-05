import { useEffect, useRef } from "react";

import type { Breakdown } from "../api/types";
import { money, pesos } from "../lib/format";
import { Money } from "./Money";
import { StatusBadge, WageBadge } from "./Badge";

interface Props {
  breakdown: Breakdown;
  onClose: () => void;
}

export function EmployeeDialog({ breakdown: b, onClose }: Props) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    ref.current?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div className="overlay" onClick={onClose}>
      <div
        className="dialog"
        role="dialog"
        aria-modal="true"
        aria-label={`Breakdown for ${b.name}`}
        tabIndex={-1}
        ref={ref}
        onClick={(e) => e.stopPropagation()}
      >
        <header className="dialog-head">
          <div>
            <h2>{b.name}</h2>
            <div className="dialog-tags">
              <StatusBadge restructure={b.restructure} saturated={b.saturated} />
              <WageBadge ok={b.invariants.minimum_wage_ok} />
            </div>
          </div>
          <button className="icon-button" onClick={onClose} aria-label="Close">
            ×
          </button>
        </header>

        <div className="dialog-body">
          {b.notes.map((n) => (
            <div key={n} className="alert alert-info">
              {n}
            </div>
          ))}

          <Section
            title="Monthly structure"
            caption="The signed gross salary, split three ways. These add to gross exactly — take-home is unchanged."
          >
            <Row label="Signed gross salary" value={b.signed_gross_monthly} strong />
            <Row label="De minimis (Tier 1, exempt)" value={b.deminimis_monthly} />
            <Row label="Productivity incentive (Tier 2)" value={b.incentive_monthly} />
            <Row label="Taxable basic salary" value={b.basic_monthly} />
            <Divider />
            <Row
              label="Daily rate"
              value={b.daily_rate}
              note={
                b.invariants.minimum_wage_ok
                  ? "Above the minimum wage floor"
                  : "BELOW THE MINIMUM WAGE FLOOR"
              }
            />
          </Section>

          <Section
            title="Monthly deductions"
            caption="SSS is computed on gross less de minimis. PhilHealth is on basic salary only, correctly excluding de minimis and the incentive."
          >
            <Row label="SSS employee share" value={b.sss_employee} />
            <Row label="PhilHealth employee share" value={b.philhealth_employee} />
            <Row label="Pag-IBIG" value={b.pagibig_employee} />
            <Row label="Withholding tax" value={b.withholding_monthly} />
            <Divider />
            <Row label="Net pay" value={b.net_pay_monthly} strong />
          </Section>

          <Section
            title="The 90,000 bucket"
            caption="13th month pay and other benefits share one annual ceiling under NIRC Sec. 32(B)(7)(e). The 13th-month payment goes in first; the incentive fills the rest."
          >
            <Row
              label="13th-month-date payment"
              value={b.thirteenth_month_payment}
            />
            <Row
              label="Incentive, annualised"
              value={b.incentive_monthly * 12}
            />
            <Divider />
            <Row label="Bucket total" value={b.bucket_annual} strong />
            <Row
              label="Spill (taxable)"
              value={b.spill_annual}
              note={
                b.spill_annual > 0
                  ? "Past the ceiling — this amount is taxed"
                  : "Within the ceiling"
              }
            />
            <BucketBar
              bucket={b.bucket_annual}
              ceiling={b.bucket_annual - b.spill_annual}
            />
          </Section>

          <Section
            title="Annual position"
            caption="What the restructure achieves against the old structure."
          >
            <Row label="Total exempt" value={b.total_exempt_annual} strong />
            <Row label="Annual taxable income" value={b.annual_taxable} />
            <Row label="Annual tax" value={b.annual_tax} />
            <Divider />
            <Row
              label="Annual tax under the old structure"
              value={b.baseline_annual_tax}
            />
            <Row
              label="Tax saved per year"
              value={b.tax_saved_annual}
              strong
              signed
            />
          </Section>

          <Section
            title="BIR Form 2316 mapping"
            caption="How this employee's year lands on the annual information return."
          >
            <Row label="De minimis benefits" value={b.bir_deminimis_annual} />
            <Row
              label="13th month pay and other benefits (max 90,000)"
              value={b.bir_benefits_annual}
            />
            <Row label="Taxable compensation from spill" value={b.bir_taxable_spill} />
          </Section>

          <Section title="Checks" caption="Each of these must hold. A failure is a bug, not a tuning decision.">
            <Check
              ok={b.invariants.structure_balances}
              label="De minimis + incentive + basic equals signed gross"
            />
            <Check
              ok={b.invariants.minimum_wage_ok}
              label={`Daily rate ${money(b.daily_rate)} clears the minimum wage`}
            />
            <Check
              ok={b.invariants.thirteenth_month_covered}
              label="13th-month payment covers the statutory 13th month"
            />
            {b.invariants.held_harmless !== null && (
              <Check
                ok={b.invariants.held_harmless}
                label="Not restructured, and not made worse off"
              />
            )}
          </Section>
        </div>
      </div>
    </div>
  );
}

function Section({
  title,
  caption,
  children,
}: {
  title: string;
  caption?: string;
  children: React.ReactNode;
}) {
  return (
    <section className="dialog-section">
      <h3>{title}</h3>
      {caption && <p className="subtle small">{caption}</p>}
      <div className="rows">{children}</div>
    </section>
  );
}

function Row({
  label,
  value,
  note,
  strong,
  signed,
}: {
  label: string;
  value: number;
  note?: string;
  strong?: boolean;
  signed?: boolean;
}) {
  return (
    <div className={`row${strong ? " row-strong" : ""}`}>
      <div className="row-label">
        {label}
        {note && <span className="row-note">{note}</span>}
      </div>
      <Money value={value} strong={strong} signed={signed} />
    </div>
  );
}

function Divider() {
  return <div className="row-divider" />;
}

function Check({ ok, label }: { ok: boolean; label: string }) {
  return (
    <div className="check">
      <span className={ok ? "check-ok" : "check-fail"}>{ok ? "✓" : "✗"}</span>
      <span>{label}</span>
    </div>
  );
}

function BucketBar({ bucket, ceiling }: { bucket: number; ceiling: number }) {
  const used = Math.min(bucket, ceiling);
  const usedPct = (used / Math.max(bucket, ceiling)) * 100;
  const spillPct = 100 - usedPct;

  return (
    <div className="bucket">
      <div className="bucket-bar">
        <div className="bucket-used" style={{ width: `${usedPct}%` }} />
        {spillPct > 0.5 && (
          <div className="bucket-spill" style={{ width: `${spillPct}%` }} />
        )}
      </div>
      <div className="bucket-legend">
        <span>
          <i className="swatch swatch-used" /> Exempt {pesos(used)}
        </span>
        {bucket > ceiling && (
          <span>
            <i className="swatch swatch-spill" /> Spill {pesos(bucket - ceiling)}
          </span>
        )}
      </div>
    </div>
  );
}
