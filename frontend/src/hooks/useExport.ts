import { useCallback, useState } from "react";

import { api } from "../api/client";
import type { Scenario } from "../api/types";

/**
 * Downloads the breakdown as .xlsx.
 *
 * The file is built server-side from the scenario currently on screen, including
 * unsaved edits — what you see is what you export.
 */
export function useExport(scenario: Scenario | null) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const download = useCallback(async () => {
    if (!scenario || busy) return;
    setBusy(true);
    setError(null);

    let url: string | null = null;
    try {
      const { blob, filename } = await api.exportXlsx(scenario);
      url = URL.createObjectURL(blob);

      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      // Revoking immediately can cancel the download in some browsers.
      if (url) {
        const objectUrl = url;
        setTimeout(() => URL.revokeObjectURL(objectUrl), 30_000);
      }
      setBusy(false);
    }
  }, [scenario, busy]);

  return { download, busy, error };
}
