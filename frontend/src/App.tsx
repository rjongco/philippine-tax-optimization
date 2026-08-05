import { useState } from "react";

import { useScenario } from "./hooks/useScenario";
import { Configuration } from "./pages/Configuration";
import { Dashboard } from "./pages/Dashboard";
import { Employees } from "./pages/Employees";
import { Schedule } from "./pages/Schedule";
import "./App.css";

type Tab = "dashboard" | "employees" | "configuration" | "schedule";

const TABS: { id: Tab; label: string }[] = [
  { id: "dashboard", label: "Breakdown" },
  { id: "employees", label: "Employees" },
  { id: "configuration", label: "Configuration" },
  { id: "schedule", label: "Payout schedule" },
];

export default function App() {
  const [tab, setTab] = useState<Tab>("dashboard");
  const { scenario, result, dirty, computing, error, update, save, reset } =
    useScenario();

  return (
    <div className="app">
      <nav className="nav">
        <div className="brand">
          <span className="brand-mark">₱</span>
          <div>
            <div className="brand-name">Payroll Structure</div>
            <div className="brand-sub">Philippine tax optimization</div>
          </div>
        </div>

        <div className="nav-tabs">
          {TABS.map((t) => (
            <button
              key={t.id}
              className={tab === t.id ? "active" : ""}
              onClick={() => setTab(t.id)}
            >
              {t.label}
            </button>
          ))}
        </div>

        <div className="nav-actions">
          {computing && <span className="computing">computing…</span>}
          {dirty && <span className="dirty">unsaved</span>}
          <button className="btn" onClick={save} disabled={!dirty}>
            Save
          </button>
          <button
            className="btn btn-ghost"
            onClick={() => {
              if (
                confirm(
                  "Discard all changes and restore the values from the workbook?",
                )
              )
                reset();
            }}
          >
            Reset
          </button>
        </div>
      </nav>

      {error && <div className="alert alert-danger global">{error}</div>}

      <main>
        {!scenario ? (
          <div className="loading">Loading…</div>
        ) : tab === "dashboard" ? (
          result ? (
            <Dashboard result={result} scenario={scenario} />
          ) : (
            <div className="loading">Computing…</div>
          )
        ) : tab === "employees" ? (
          <Employees scenario={scenario} result={result} onChange={update} />
        ) : tab === "configuration" ? (
          <Configuration scenario={scenario} result={result} onChange={update} />
        ) : (
          <Schedule scenario={scenario} />
        )}
      </main>
    </div>
  );
}
