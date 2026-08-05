import { useState } from "react";

import type { Breakdown, ComputeResult, Scenario } from "../api/types";
import { StatusBadge, WageBadge } from "../components/Badge";
import { EmployeeDialog } from "../components/EmployeeDialog";
import { Money } from "../components/Money";
import { useExport } from "../hooks/useExport";
import { pesos } from "../lib/format";

interface Props {
  result: ComputeResult;
  scenario: Scenario | null;
}

export function Dashboard({ result, scenario }: Props) {
  const [selected, setSelected] = useState<Breakdown | null>(null);
  const { download, busy, error: exportError } = useExport(scenario);
  const { totals, breakdowns } = result;

  return (
    <div className="page">
      <header className="page-head">
        <div>
          <h1>Employee breakdown</h1>
          <p className="subtle">
            Click any employee for their full computation. Nothing here changes
            what anyone is paid — only how each peso is characterised.
          </p>
        </div>
        <div className="head-actions">
          <button className="btn btn-primary" onClick={download} disabled={busy}>
            {busy ? "Building…" : "Export to Excel"}
          </button>
          <span className="subtle small">
            Live formulas, not frozen numbers — edit a salary in the file and it
            recalculates.
          </span>
        </div>
      </header>

      {exportError && <div className="alert alert-danger">{exportError}</div>}

      {result.warnings.length > 0 && (
        <div className="alert alert-danger">
          <strong>Attention</strong>
          <ul>
            {result.warnings.map((w) => (
              <li key={w}>{w}</li>
            ))}
          </ul>
        </div>
      )}

      <section className="stat-row">
        <Stat
          label="Tax saved per year"
          value={pesos(totals.tax_saved_annual)}
          hint="Against the pre-restructure baseline, at zero incremental company cost"
          accent
        />
        <Stat
          label="Exempt per year"
          value={pesos(totals.total_exempt_annual)}
          hint="De minimis plus the 90,000 benefits ceiling, across all employees"
        />
        <Stat
          label="Monthly gross"
          value={pesos(totals.signed_gross_monthly)}
          hint="Unchanged — this is the constraint the model works inside"
        />
        <Stat
          label="De minimis per month"
          value={pesos(result.deminimis_monthly)}
          hint="Tier 1, does not consume the 90,000 ceiling"
        />
      </section>

      <div className="table-scroll">
        <table className="grid">
          <thead>
            <tr>
              <th className="col-name">Employee</th>
              <th>Status</th>
              <th className="ralign">Signed gross</th>
              <th className="ralign">De minimis</th>
              <th className="ralign">Incentive</th>
              <th className="ralign">Taxable basic</th>
              <th className="ralign">Net pay</th>
              <th className="ralign">Exempt / yr</th>
              <th className="ralign">Tax saved / yr</th>
              <th>Min wage</th>
            </tr>
          </thead>
          <tbody>
            {breakdowns.map((b) => (
              <tr
                key={b.employee_id}
                onClick={() => setSelected(b)}
                className="clickable"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    setSelected(b);
                  }
                }}
              >
                <td className="col-name">{b.name}</td>
                <td>
                  <StatusBadge
                    restructure={b.restructure}
                    saturated={b.saturated}
                  />
                </td>
                <td className="ralign">
                  <Money value={b.signed_gross_monthly} />
                </td>
                <td className="ralign">
                  <Money value={b.deminimis_monthly} />
                </td>
                <td className="ralign">
                  <Money value={b.incentive_monthly} />
                </td>
                <td className="ralign">
                  <Money value={b.basic_monthly} />
                </td>
                <td className="ralign">
                  <Money value={b.net_pay_monthly} />
                </td>
                <td className="ralign">
                  <Money value={b.total_exempt_annual} />
                </td>
                <td className="ralign">
                  <Money value={b.tax_saved_annual} strong signed dashZero />
                </td>
                <td>
                  <WageBadge ok={b.invariants.minimum_wage_ok} />
                </td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr>
              <td className="col-name">Total</td>
              <td />
              <td className="ralign">
                <Money value={totals.signed_gross_monthly} strong />
              </td>
              <td className="ralign">
                <Money value={totals.deminimis_monthly} strong />
              </td>
              <td className="ralign">
                <Money value={totals.incentive_monthly} strong />
              </td>
              <td className="ralign">
                <Money value={totals.basic_monthly} strong />
              </td>
              <td className="ralign">
                <Money value={totals.net_pay_monthly} strong />
              </td>
              <td className="ralign">
                <Money value={totals.total_exempt_annual} strong />
              </td>
              <td className="ralign">
                <Money value={totals.tax_saved_annual} strong signed />
              </td>
              <td />
            </tr>
          </tfoot>
        </table>
      </div>

      {selected && (
        <EmployeeDialog
          breakdown={selected}
          onClose={() => setSelected(null)}
        />
      )}
    </div>
  );
}

function Stat({
  label,
  value,
  hint,
  accent,
}: {
  label: string;
  value: string;
  hint: string;
  accent?: boolean;
}) {
  return (
    <div className={`stat${accent ? " stat-accent" : ""}`}>
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
      <div className="stat-hint">{hint}</div>
    </div>
  );
}
