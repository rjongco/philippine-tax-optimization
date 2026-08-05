import { money } from "../lib/format";

interface Props {
  value: number;
  dashZero?: boolean;
  strong?: boolean;
  /** Colour by sign — only for figures where a negative is meaningful. */
  signed?: boolean;
}

export function Money({ value, dashZero, strong, signed }: Props) {
  const classes = ["num"];
  if (strong) classes.push("num-strong");
  if (signed && value > 0) classes.push("num-positive");
  if (signed && value < 0) classes.push("num-negative");

  return <span className={classes.join(" ")}>{money(value, dashZero)}</span>;
}
