// Mirrors app/schemas.py. Every money field arrives already rounded to centavos —
// the backend is the only thing that rounds, and the only thing that computes.

export interface Parameters {
  philhealth_rate: number;
  philhealth_floor: number;
  philhealth_ceiling: number;
  pagibig_employee: number;
  benefits_ceiling: number;
  cash_anchor: number;
  baseline_award: number;
  min_wage_daily: number;
  working_days: number;
  minimum_basic_monthly: number; // derived, not editable
}

export type EditableParameter = Exclude<keyof Parameters, "minimum_basic_monthly">;

export interface DeMinimisItem {
  key: string;
  label: string;
  statutory_cap_monthly: number;
  granted_monthly: number;
  annual: number;
  authority: string;
  note: string;
  unconditional: boolean;
  over_cap: boolean;
}

export interface Employee {
  id: string;
  name: string;
  signed_gross_monthly: number;
  restructure: boolean;
}

export interface Scenario {
  parameters: Parameters;
  deminimis_items: DeMinimisItem[];
  employees: Employee[];
  deminimis_monthly: number;
}

export interface Invariants {
  structure_balances: boolean;
  minimum_wage_ok: boolean;
  thirteenth_month_covered: boolean;
  held_harmless: boolean | null;
  all_ok: boolean;
}

export interface Breakdown {
  employee_id: string;
  name: string;
  restructure: boolean;
  saturated: boolean;

  signed_gross_monthly: number;
  deminimis_monthly: number;
  thirteenth_month_payment: number;
  incentive_monthly: number;
  basic_monthly: number;
  daily_rate: number;

  sss_employee: number;
  philhealth_employee: number;
  pagibig_employee: number;
  net_taxable_monthly: number;

  bucket_annual: number;
  spill_annual: number;
  annual_taxable: number;
  annual_tax: number;
  withholding_monthly: number;
  net_pay_monthly: number;
  total_exempt_annual: number;

  baseline_basic_monthly: number;
  baseline_annual_taxable: number;
  baseline_annual_tax: number;
  tax_saved_annual: number;

  bir_deminimis_annual: number;
  bir_benefits_annual: number;
  bir_taxable_spill: number;

  invariants: Invariants;
  notes: string[];
}

export interface Totals {
  signed_gross_monthly: number;
  deminimis_monthly: number;
  incentive_monthly: number;
  basic_monthly: number;
  net_pay_monthly: number;
  annual_tax: number;
  baseline_annual_tax: number;
  tax_saved_annual: number;
  total_exempt_annual: number;
}

export interface ComputeResult {
  deminimis_monthly: number;
  minimum_basic_monthly: number;
  breakdowns: Breakdown[];
  totals: Totals;
  warnings: string[];
}

export type ParameterCategory = "fact" | "lever" | "assumption";

export interface ParameterDoc {
  key: EditableParameter;
  label: string;
  category: ParameterCategory;
  unit: string;
  authority: string;
  description: string;
  affects: string;
  warning: string | null;
  editable: boolean;
}

export interface ConceptDoc {
  key: string;
  title: string;
  body: string;
}

export interface Cutoff {
  month: number;
  month_name: string;
  cutoff: number;
  basic: number;
  deminimis: number;
  incentive: number;
  thirteenth_month: number;
  gross_cash: number;
  sss: number;
  philhealth: number;
  pagibig: number;
  withholding: number;
  net_cash: number;
  note: string;
}

export interface MonthLine {
  month: number;
  month_name: string;
  basic: number;
  deminimis: number;
  incentive: number;
  thirteenth_month: number;
  gross_cash: number;
  deductions: number;
  net_cash: number;
}

export interface EmployeeSchedule {
  employee_id: string;
  name: string;
  months: MonthLine[];
  cutoffs: Cutoff[];
  annual_gross_cash: number;
  annual_net_cash: number;
  reconciles: boolean;
  notes: string[];
}
