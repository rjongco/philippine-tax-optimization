const peso = new Intl.NumberFormat("en-PH", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const whole = new Intl.NumberFormat("en-PH", { maximumFractionDigits: 0 });

/** Money, two decimals. Zero renders as a dash so real values stand out. */
export function money(value: number, dashZero = false): string {
  if (dashZero && value === 0) return "—";
  return peso.format(value);
}

export function pesos(value: number): string {
  return `₱${peso.format(value)}`;
}

export function compact(value: number): string {
  return whole.format(value);
}

export function percent(rate: number): string {
  return `${(rate * 100).toFixed(2)}%`;
}
