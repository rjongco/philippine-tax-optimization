import { useEffect, useState } from "react";

import { api } from "../api/client";
import type { EmployeeSchedule, Scenario } from "../api/types";
import { Badge } from "../components/Badge";
import { Money } from "../components/Money";
import { pesos } from "../lib/format";

type View = "bimonthly" | "monthly";

export function Schedule({ scenario }: { scenario: Scenario }) {
  const [schedules, setSchedules] = useState<EmployeeSchedule[]>([]);
  const [selectedId, setSelectedId] = useState<string>("");
  const [view, setView] = useState<View>("bimonthly");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .schedule(scenario)
      .then((s) => {
        setSchedules(s);
        setError(null);
        setSelectedId((current) =>
          current && s.some((x) => x.employee_id === current)
            ? current
            : (s[0]?.employee_id ?? ""),
        );
      })
      .catch((e: Error) => setError(e.message));
  }, [scenario]);

  const selected = schedules.find((s) => s.employee_id === selectedId);

  return (
    <div className="page">
      <header className="page-head">
        <div>
          <h1>Payout schedule</h1>
          <p className="subtle">
            What actually leaves the bank, and when. The breakdown page is an{" "}
            <em>accrual</em> view — it says what each component is worth per month.
            This is the <em>cash</em> view. They are different objects, which is why
            this is computed rather than divided by two.
          </p>
        </div>
      </header>

      {error && <div className="alert alert-danger">{error}</div>}

      <div className="toolbar">
        <select
          value={selectedId}
          onChange={(e) => setSelectedId(e.target.value)}
          className="select"
        >
          {schedules.map((s) => (
            <option key={s.employee_id} value={s.employee_id}>
              {s.name}
            </option>
          ))}
        </select>

        <div className="segmented">
          <button
            className={view === "bimonthly" ? "active" : ""}
            onClick={() => setView("bimonthly")}
          >
            Bimonthly (15th / 30th)
          </button>
          <button
            className={view === "monthly" ? "active" : ""}
            onClick={() => setView("monthly")}
          >
            Monthly
          </button>
        </div>
      </div>

      {selected && (
        <>
          {selected.notes.map((n) => (
            <div key={n} className="alert alert-info">
              {n}
            </div>
          ))}

          <section className="stat-row">
            <div className="stat">
              <div className="stat-label">Annual gross cash</div>
              <div className="stat-value">
                {pesos(selected.annual_gross_cash)}
              </div>
              <div className="stat-hint">
                Twelve months of signed gross plus the 13th-month payment
              </div>
            </div>
            <div className="stat">
              <div className="stat-label">Annual net cash</div>
              <div className="stat-value">{pesos(selected.annual_net_cash)}</div>
              <div className="stat-hint">After statutory deductions and withholding</div>
            </div>
            <div className="stat">
              <div className="stat-label">Reconciliation</div>
              <div className="stat-value">
                <Badge tone={selected.reconciles ? "ok" : "danger"}>
                  {selected.reconciles ? "Balanced" : "FAILED"}
                </Badge>
              </div>
              <div className="stat-hint">
                Proof that re-timing moved money without creating or losing any
              </div>
            </div>
          </section>

          <div className="table-scroll">
            {view === "bimonthly" ? (
              <table className="grid">
                <thead>
                  <tr>
                    <th className="col-name">Month</th>
                    <th>Cutoff</th>
                    <th className="ralign">Basic</th>
                    <th className="ralign">De minimis</th>
                    <th className="ralign">Incentive</th>
                    <th className="ralign">13th month</th>
                    <th className="ralign">Gross cash</th>
                    <th className="ralign">Deductions</th>
                    <th className="ralign">Net cash</th>
                  </tr>
                </thead>
                <tbody>
                  {selected.cutoffs.map((c) => {
                    const deductions =
                      c.sss + c.philhealth + c.pagibig + c.withholding;
                    return (
                      <tr
                        key={`${c.month}-${c.cutoff}`}
                        className={c.thirteenth_month > 0 ? "row-highlight" : ""}
                      >
                        <td className="col-name">
                          {c.cutoff === 1 ? c.month_name : ""}
                        </td>
                        <td className="subtle">
                          {c.cutoff === 1 ? "15th" : "30th"}
                        </td>
                        <td className="ralign">
                          <Money value={c.basic} />
                        </td>
                        <td className="ralign">
                          <Money value={c.deminimis} />
                        </td>
                        <td className="ralign">
                          <Money value={c.incentive} dashZero />
                        </td>
                        <td className="ralign">
                          <Money value={c.thirteenth_month} dashZero />
                        </td>
                        <td className="ralign">
                          <Money value={c.gross_cash} />
                        </td>
                        <td className="ralign subtle">
                          <Money value={deductions} />
                        </td>
                        <td className="ralign">
                          <Money value={c.net_cash} strong />
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            ) : (
              <table className="grid">
                <thead>
                  <tr>
                    <th className="col-name">Month</th>
                    <th className="ralign">Basic</th>
                    <th className="ralign">De minimis</th>
                    <th className="ralign">Incentive</th>
                    <th className="ralign">13th month</th>
                    <th className="ralign">Gross cash</th>
                    <th className="ralign">Deductions</th>
                    <th className="ralign">Net cash</th>
                  </tr>
                </thead>
                <tbody>
                  {selected.months.map((m) => (
                    <tr
                      key={m.month}
                      className={m.thirteenth_month > 0 ? "row-highlight" : ""}
                    >
                      <td className="col-name">{m.month_name}</td>
                      <td className="ralign">
                        <Money value={m.basic} />
                      </td>
                      <td className="ralign">
                        <Money value={m.deminimis} />
                      </td>
                      <td className="ralign">
                        <Money value={m.incentive} dashZero />
                      </td>
                      <td className="ralign">
                        <Money value={m.thirteenth_month} dashZero />
                      </td>
                      <td className="ralign">
                        <Money value={m.gross_cash} />
                      </td>
                      <td className="ralign subtle">
                        <Money value={m.deductions} />
                      </td>
                      <td className="ralign">
                        <Money value={m.net_cash} strong />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          <p className="subtle small footnote">
            The two cutoffs are uneven by exactly the productivity incentive, which
            lands on the 15th for the previous month's determination. The 13th-month
            payment falls on December's first cutoff so it clears the 24 December
            deadline under PD 851.
          </p>
        </>
      )}
    </div>
  );
}
