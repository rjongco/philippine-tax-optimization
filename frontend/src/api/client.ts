import type {
  ComputeResult,
  ConceptDoc,
  EmployeeSchedule,
  ParameterDoc,
  Scenario,
} from "./types";

// Vite proxies /api to the FastAPI server in dev — see vite.config.ts.
const BASE = "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!response.ok) {
    const detail = await response.text().catch(() => response.statusText);
    throw new Error(`${response.status} ${path}: ${detail}`);
  }
  return response.json() as Promise<T>;
}

/**
 * ScenarioOut carries derived fields the input model rejects, so strip them
 * before sending anything back.
 */
function toInput(scenario: Scenario) {
  const { minimum_basic_monthly: _derived, ...parameters } = scenario.parameters;
  return {
    parameters,
    deminimis_items: scenario.deminimis_items.map((i) => ({
      key: i.key,
      label: i.label,
      statutory_cap_monthly: i.statutory_cap_monthly,
      granted_monthly: i.granted_monthly,
      authority: i.authority,
      note: i.note,
      unconditional: i.unconditional,
    })),
    employees: scenario.employees.map((e) => ({
      id: e.id,
      name: e.name,
      signed_gross_monthly: e.signed_gross_monthly,
      restructure: e.restructure,
    })),
  };
}

/** Filename from Content-Disposition, so the server names the file, not the client. */
function filenameFrom(header: string | null, fallback: string): string {
  const match = header?.match(/filename="([^"]+)"/);
  return match?.[1] ?? fallback;
}

export const api = {
  getScenario: () => request<Scenario>("/scenario"),

  /** Live .xlsx of the breakdown. Returns the blob and the server's filename. */
  exportXlsx: async (scenario: Scenario) => {
    const response = await fetch(`${BASE}/export/xlsx`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(toInput(scenario)),
    });
    if (!response.ok) {
      const detail = await response.text().catch(() => response.statusText);
      throw new Error(`${response.status} export: ${detail}`);
    }
    return {
      blob: await response.blob(),
      filename: filenameFrom(
        response.headers.get("Content-Disposition"),
        "payroll-breakdown.xlsx",
      ),
    };
  },

  saveScenario: (scenario: Scenario) =>
    request<Scenario>("/scenario", {
      method: "PUT",
      body: JSON.stringify(toInput(scenario)),
    }),

  resetScenario: () => request<Scenario>("/scenario/reset", { method: "POST" }),

  compute: (scenario: Scenario) =>
    request<ComputeResult>("/compute", {
      method: "POST",
      body: JSON.stringify(toInput(scenario)),
    }),

  schedule: (scenario: Scenario) =>
    request<EmployeeSchedule[]>("/schedule", {
      method: "POST",
      body: JSON.stringify(toInput(scenario)),
    }),

  parameterDocs: () => request<ParameterDoc[]>("/parameters/meta"),

  concepts: () => request<ConceptDoc[]>("/concepts"),
};
