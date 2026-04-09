"use client";

import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { Dropzone } from "@/components/upload/Dropzone";
import { UploadError } from "@/components/upload/UploadError";
import { UploadProgress } from "@/components/upload/UploadProgress";
import { useReport } from "@/context/ReportContext";
import { ApiError, analyzeZip } from "@/lib/api";
import { type FriendlyError, friendlyError } from "@/lib/errors";

type Stage = "idle" | "uploading" | "parsing" | "analyzing" | "error";

export default function Page() {
  const router = useRouter();
  const { setReport } = useReport();
  const [stage, setStage] = useState<Stage>("idle");
  const [error, setError] = useState<FriendlyError | null>(null);
  const timerIds = useRef<number[]>([]);

  useEffect(() => {
    return () => {
      for (const id of timerIds.current) {
        window.clearTimeout(id);
      }
      timerIds.current = [];
    };
  }, []);

  async function handleFile(file: File) {
    // Clear any timers from a previous attempt
    for (const id of timerIds.current) {
      window.clearTimeout(id);
    }
    timerIds.current = [];

    setError(null);
    setStage("uploading");
    // staged UX — small delay between visual states so the user can read the progress
    timerIds.current.push(
      window.setTimeout(
        () => setStage((s) => (s === "uploading" ? "parsing" : s)),
        400,
      ),
      window.setTimeout(
        () => setStage((s) => (s === "parsing" ? "analyzing" : s)),
        900,
      ),
    );
    try {
      const report = await analyzeZip(file);
      setReport(report);
      router.push("/report");
    } catch (e) {
      if (e instanceof ApiError) {
        setError(friendlyError(e.body, e.status));
      } else {
        setError({
          title: "Network error",
          description:
            "Couldn't reach the Whoop Lens API. Check your connection and try again.",
          canRetry: true,
        });
      }
      setStage("error");
    }
  }

  const busy =
    stage === "uploading" || stage === "parsing" || stage === "analyzing";

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-8 px-6 py-20">
      <header className="text-center">
        <div className="text-[11px] uppercase tracking-[0.24em] text-text-3">
          WHOOP·LENS
        </div>
        <h1 className="mt-3 text-4xl font-bold leading-tight text-text-primary">
          Your Whoop data,
          <br />
          <span className="text-teal">visualized.</span>
        </h1>
        <p className="mx-auto mt-4 max-w-xl text-sm text-text-2">
          Drop your Whoop data export ZIP and get an interactive report in
          seconds. Private by default — nothing is stored unless you choose to
          share it.
        </p>
      </header>
      {busy ? (
        <UploadProgress
          stage={
            stage === "uploading"
              ? "uploading"
              : stage === "parsing"
                ? "parsing"
                : "analyzing"
          }
        />
      ) : (
        <Dropzone
          onFile={handleFile}
          disabled={busy}
          onReject={(message) =>
            setError({
              title: "Can't read that file",
              description: message,
              canRetry: false,
            })
          }
        />
      )}
      {error ? (
        <UploadError
          error={error}
          onRetry={() => {
            setError(null);
            setStage("idle");
          }}
        />
      ) : null}
    </div>
  );
}
