"use client";

import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { Dialog } from "@/components/ui/Dialog";
import { createShare } from "@/lib/api";
import type { WhoopReport } from "@/lib/types";

type Props = {
  open: boolean;
  onClose: () => void;
  report: WhoopReport;
};

export function ShareDialog({ open, onClose, report }: Props) {
  const [state, setState] = useState<"idle" | "creating" | "done" | "error">(
    "idle",
  );
  const [url, setUrl] = useState<string | null>(null);

  async function create() {
    setState("creating");
    try {
      const resp = await createShare(report);
      const fullUrl = `${window.location.origin}${resp.url}`;
      setUrl(fullUrl);
      setState("done");
    } catch {
      setState("error");
    }
  }

  function reset() {
    setState("idle");
    setUrl(null);
    onClose();
  }

  return (
    <Dialog open={open} onClose={reset} title="Share Report">
      {state === "idle" && (
        <>
          <p className="text-sm text-text-2">
            Your report will be saved for 30 days under an anonymous URL. Anyone
            with the link can view it. Nothing beyond the computed report is
            stored.
          </p>
          <div className="mt-6 flex justify-end gap-3">
            <Button variant="ghost" onClick={reset}>
              Cancel
            </Button>
            <Button onClick={create}>Create link</Button>
          </div>
        </>
      )}
      {state === "creating" && (
        <p className="py-6 text-center text-sm text-text-2">Creating link…</p>
      )}
      {state === "done" && url && (
        <>
          <p className="text-sm text-text-2">
            Your share link (valid 30 days):
          </p>
          <div className="mt-3 break-all rounded-md bg-black/40 px-3 py-2 font-mono text-xs">
            {url}
          </div>
          <div className="mt-6 flex justify-end gap-3">
            <Button
              variant="secondary"
              onClick={() => {
                void navigator.clipboard.writeText(url);
              }}
            >
              Copy
            </Button>
            <Button onClick={reset}>Done</Button>
          </div>
        </>
      )}
      {state === "error" && (
        <>
          <p className="text-sm text-rec-red">
            Couldn't create the share link. Please try again.
          </p>
          <div className="mt-6 flex justify-end gap-3">
            <Button variant="ghost" onClick={reset}>
              Close
            </Button>
            <Button onClick={create}>Retry</Button>
          </div>
        </>
      )}
    </Dialog>
  );
}
