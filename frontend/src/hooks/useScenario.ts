import { useCallback, useEffect, useRef, useState } from "react";

import { api } from "../api/client";
import type { ComputeResult, Scenario } from "../api/types";

/**
 * Single source of scenario state.
 *
 * Every edit recomputes against the server, debounced. The computation is never
 * mirrored in TypeScript — a second implementation would drift from the Python one
 * and the divergence would surface in a payslip months later.
 *
 * Edits are held locally until saved, so the config page can preview a change
 * without committing it.
 */
export function useScenario() {
  const [scenario, setScenario] = useState<Scenario | null>(null);
  const [result, setResult] = useState<ComputeResult | null>(null);
  const [dirty, setDirty] = useState(false);
  const [computing, setComputing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generation = useRef(0);

  useEffect(() => {
    api
      .getScenario()
      .then(setScenario)
      .catch((e: Error) => setError(e.message));
  }, []);

  // Debounced recompute. `generation` discards responses that arrive out of
  // order, so fast typing cannot leave stale numbers on screen.
  useEffect(() => {
    if (!scenario) return;
    const mine = ++generation.current;
    setComputing(true);

    const timer = setTimeout(() => {
      api
        .compute(scenario)
        .then((r) => {
          if (mine === generation.current) {
            setResult(r);
            setError(null);
          }
        })
        .catch((e: Error) => {
          if (mine === generation.current) setError(e.message);
        })
        .finally(() => {
          if (mine === generation.current) setComputing(false);
        });
    }, 180);

    return () => clearTimeout(timer);
  }, [scenario]);

  const update = useCallback((next: Scenario) => {
    setScenario(next);
    setDirty(true);
  }, []);

  const save = useCallback(async () => {
    if (!scenario) return;
    try {
      const saved = await api.saveScenario(scenario);
      setScenario(saved);
      setDirty(false);
      setError(null);
    } catch (e) {
      setError((e as Error).message);
    }
  }, [scenario]);

  const reset = useCallback(async () => {
    try {
      const seeded = await api.resetScenario();
      setScenario(seeded);
      setDirty(false);
      setError(null);
    } catch (e) {
      setError((e as Error).message);
    }
  }, []);

  return { scenario, result, dirty, computing, error, update, save, reset };
}
