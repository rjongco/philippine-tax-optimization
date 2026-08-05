import type { ComputeResult, Scenario } from "../api/types";
import { Badge } from "../components/Badge";
import { Money } from "../components/Money";

interface Props {
  scenario: Scenario;
  result: ComputeResult | null;
  onChange: (next: Scenario) => void;
}

export function Employees({ scenario, result, onChange }: Props) {
  const byId = new Map(result?.breakdowns.map((b) => [b.employee_id, b]) ?? []);

  const setGross = (id: string, raw: string) => {
    const value = Number(raw);
    if (!Number.isFinite(value) || value < 0) return;
    onChange({
      ...scenario,
      employees: scenario.employees.map((e) =>
        e.id === id ? { ...e, signed_gross_monthly: value } : e,
      ),
    });
  };

  const setRestructure = (id: string, restructure: boolean) => {
    onChange({
      ...scenario,
      employees: scenario.employees.map((e) =>
        e.id === id ? { ...e, restructure } : e,
      ),
    });
  };

  return (
    <div className="page">
      <header className="page-head">
        <div>
          <h1>Employees</h1>
          <p className="subtle">
            Signed gross salary and whether each employee is restructured. Mark
            someone as <em>not</em> restructured when their taxable income already
            sits below ₱250,000 — restructuring gains them nothing while eroding
            their 13th month base and SSS accrual. They are then held harmless
            automatically.
          </p>
        </div>
      </header>

      <div className="table-scroll">
        <table className="grid">
          <thead>
            <tr>
              <th className="col-name">Employee</th>
              <th className="ralign">Signed gross / mo</th>
              <th>Restructure</th>
              <th className="ralign">Taxable basic</th>
              <th className="ralign">Annual taxable</th>
              <th className="ralign">Tax saved / yr</th>
              <th>Effect</th>
            </tr>
          </thead>
          <tbody>
            {scenario.employees.map((e) => {
              const b = byId.get(e.id);
              return (
                <tr key={e.id}>
                  <td className="col-name">{e.name}</td>
                  <td className="ralign">
                    <input
                      type="number"
                      step="1"
                      min="0"
                      className="cell-input"
                      value={e.signed_gross_monthly}
                      onChange={(ev) => setGross(e.id, ev.target.value)}
                    />
                  </td>
                  <td>
                    <label className="switch">
                      <input
                        type="checkbox"
                        checked={e.restructure}
                        onChange={(ev) =>
                          setRestructure(e.id, ev.target.checked)
                        }
                      />
                      <span>{e.restructure ? "Yes" : "No"}</span>
                    </label>
                  </td>
                  <td className="ralign">
                    {b ? <Money value={b.basic_monthly} /> : "—"}
                  </td>
                  <td className="ralign">
                    {b ? <Money value={b.annual_taxable} /> : "—"}
                  </td>
                  <td className="ralign">
                    {b ? (
                      <Money value={b.tax_saved_annual} strong signed dashZero />
                    ) : (
                      "—"
                    )}
                  </td>
                  <td>
                    {b && <EffectBadge zero={b.tax_saved_annual === 0} b={b} />}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function EffectBadge({
  zero,
  b,
}: {
  zero: boolean;
  b: { restructure: boolean; saturated: boolean; annual_taxable: number };
}) {
  if (!b.restructure) return <Badge tone="muted">Held harmless</Badge>;
  if (b.saturated) return <Badge tone="warn">Bucket already full</Badge>;
  if (zero && b.annual_taxable <= 250000)
    return <Badge tone="muted">Below the zero bracket</Badge>;
  return <Badge tone="ok">Saving tax</Badge>;
}
