"use client";

import Link from "next/link";
import { useEffect } from "react";

export default function SharedRouteError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="mx-auto max-w-xl px-6 py-24 text-center">
      <div className="font-mono text-[11px] uppercase tracking-[0.2em] text-text-3">
        Error
      </div>
      <h1 className="mt-3 font-mono text-3xl font-bold text-text-primary">
        Something went wrong
      </h1>
      <p className="mt-4 text-sm text-text-2">
        We couldn't load this shared report. The link may be broken, or the
        backend might be unreachable.
      </p>
      <div className="mt-8 flex items-center justify-center gap-4">
        <button
          type="button"
          onClick={reset}
          className="text-xs font-bold uppercase tracking-[0.1em] text-teal hover:brightness-110"
        >
          Try again
        </button>
        <Link
          href="/"
          className="text-xs font-bold uppercase tracking-[0.1em] text-text-2 hover:text-text-primary"
        >
          ← Back to upload
        </Link>
      </div>
    </div>
  );
}
