import { Fragment, useEffect, useState } from "react";

import { api } from "../api/client";
import type {
  ComputeResult,
  ConceptDoc,
  EditableParameter,
  ParameterDoc,
  Scenario,
} from "../api/types";
import { Badge } from "../components/Badge";
import { Money } from "../components/Money";
import { money, percent } from "../lib/format";

interface Props {
  scenario: Scenario;
  result: ComputeResult | null;
  onChange: (next: Scenario) => void;
}

export function Configuration({ scenario, result, onChange }: Props) {
  const [docs, setDocs] = useState<ParameterDoc[]>([]);
  const [concepts, setConcepts] = useState<ConceptDoc[]>([]);
  const [open, setOpen] = useState<string | null>(null);

  useEffect(() => {
    api.parameterDocs().then(setDocs).catch(() => setDocs([]));
    api.concepts().then(setConcepts).catch(() => setConcepts([]));
  }, []);

  const setParameter = (key: EditableParameter, raw: string) => {
    const value = Number(raw);
    if (!Number.isFinite(value)) return;
    onChange({
      ...scenario,
      parameters: { ...scenario.parameters, [key]: value },
    });
  };

  const setGranted = (key: string, raw: string) => {
    const value = Number(raw);
    if (!Number.isFinite(value)) return;
    onChange({
      ...scenario,
      deminimis_items: scenario.deminimis_items.map((i) =>
        i.key === key ? { ...i, granted_monthly: value } : i,
      ),
    });
  };

  const grantedTotal = scenario.deminimis_items.reduce(
    (sum, i) => sum + i.granted_monthly,
    0,
  );
  const capTotal = scenario.deminimis_items.reduce(
    (sum, i) => sum + i.statutory_cap_monthly,
    0,
  );

  return (
    <div className="page">
      <header className="page-head">
        <div>
          <h1>Configuration</h1>
          <p className="subtle">
            Every value the model reads. Each one shows what it does, where it comes
            from, and what breaks if it is wrong. Changes recompute immediately but
            are not stored until you save.
          </p>
        </div>
      </header>

      <section className="panel">
        <h2>De minimis schedule — Tier 1</h2>
        <p className="subtle small">
          Per-item statutory caps. This tier does <strong>not</strong> consume the
          ₱90,000 ceiling, so it is free space — fill it first. Granting above a cap
          is strictly worse than not granting at all: the excess drops into the
          ₱90,000 bucket and consumes it, while also reducing basic salary.
        </p>

        <div className="table-scroll">
          <table className="grid">
            <thead>
              <tr>
                <th className="col-name">Item</th>
                <th className="ralign">Statutory cap / mo</th>
                <th className="ralign">Granted / mo</th>
                <th className="ralign">Annual</th>
                <th>Basis</th>
              </tr>
            </thead>
            <tbody>
              {scenario.deminimis_items.map((item) => (
                <Fragment key={item.key}>
                  <tr className={item.over_cap ? "row-danger" : ""}>
                    <td className="col-name">
                      {item.label}
                      {!item.unconditional && (
                        <button
                          className="link"
                          onClick={() =>
                            setOpen(open === item.key ? null : item.key)
                          }
                        >
                          {open === item.key ? "hide risk" : "risk note"}
                        </button>
                      )}
                    </td>
                    <td className="ralign subtle">
                      {money(item.statutory_cap_monthly)}
                    </td>
                    <td className="ralign">
                      <input
                        type="number"
                        step="0.01"
                        className={`cell-input${item.over_cap ? " invalid" : ""}`}
                        value={item.granted_monthly}
                        onChange={(e) => setGranted(item.key, e.target.value)}
                      />
                    </td>
                    <td className="ralign">
                      <Money value={item.granted_monthly * 12} />
                    </td>
                    <td className="subtle small">{item.authority}</td>
                  </tr>
                  {open === item.key && (
                    <tr>
                      <td colSpan={5}>
                        <div className="alert alert-warn">{item.note}</div>
                      </td>
                    </tr>
                  )}
                </Fragment>
              ))}
            </tbody>
            <tfoot>
              <tr>
                <td className="col-name">Total</td>
                <td className="ralign subtle">{money(capTotal)}</td>
                <td className="ralign">
                  <Money value={grantedTotal} strong />
                </td>
                <td className="ralign">
                  <Money value={grantedTotal * 12} strong />
                </td>
                <td />
              </tr>
            </tfoot>
          </table>
        </div>
      </section>

      <section className="panel">
        <h2>Parameters</h2>
        <div className="param-legend">
          <span>
            <Badge tone="muted">fact</Badge> set by law — editing means the law
            changed
          </span>
          <span>
            <Badge tone="info">lever</Badge> a genuine modelling choice
          </span>
          <span>
            <Badge tone="warn">assumption</Badge> unverified placeholder
          </span>
        </div>

        <div className="params">
          {docs.map((doc) => (
            <ParameterField
              key={doc.key}
              doc={doc}
              value={scenario.parameters[doc.key]}
              onChange={(raw) => setParameter(doc.key, raw)}
            />
          ))}
        </div>

        <div className="derived">
          <div>
            <strong>Minimum basic salary per month</strong>
            <span className="subtle small">
              Derived: minimum wage × working days ÷ 12. Not editable — it moves when
              the two assumptions above move.
            </span>
          </div>
          <Money value={scenario.parameters.minimum_basic_monthly} strong />
        </div>

        {result && (
          <div className="derived">
            <div>
              <strong>PhilHealth rate as applied</strong>
              <span className="subtle small">
                {percent(scenario.parameters.philhealth_rate)} of basic salary,
                floored at {money(scenario.parameters.philhealth_floor)} and capped at{" "}
                {money(scenario.parameters.philhealth_ceiling)}
              </span>
            </div>
          </div>
        )}
      </section>

      <section className="panel">
        <h2>How the model works</h2>
        <div className="concepts">
          {concepts.map((c) => (
            <article key={c.key} className="concept">
              <h3>{c.title}</h3>
              {c.body.split("\n\n").map((p, i) => (
                <p key={i}>{p}</p>
              ))}
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}

function ParameterField({
  doc,
  value,
  onChange,
}: {
  doc: ParameterDoc;
  value: number;
  onChange: (raw: string) => void;
}) {
  const tone =
    doc.category === "fact"
      ? "muted"
      : doc.category === "lever"
        ? "info"
        : "warn";

  return (
    <div className={`param param-${doc.category}`}>
      <div className="param-head">
        <label htmlFor={doc.key}>{doc.label}</label>
        <Badge tone={tone}>{doc.category}</Badge>
      </div>

      <div className="param-input">
        <input
          id={doc.key}
          type="number"
          step={doc.unit === "rate" ? "0.001" : "0.01"}
          value={value}
          onChange={(e) => onChange(e.target.value)}
        />
        <span className="unit">{doc.unit}</span>
      </div>

      <p className="param-authority">{doc.authority}</p>
      <p className="param-desc">{doc.description}</p>
      <p className="param-affects">
        <strong>Affects:</strong> {doc.affects}
      </p>
      {doc.warning && <p className="param-warning">{doc.warning}</p>}
    </div>
  );
}
