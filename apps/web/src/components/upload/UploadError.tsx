"use client";

import type { FriendlyError } from "@/lib/errors";

type Props = {
  error: FriendlyError;
  onRetry?: () => void;
};

export function UploadError({ error, onRetry }: Props) {
  return (
    <div
      role="alert"
      className="rounded-2xl border border-rec-red/30 bg-rec-red/10 px-6 py-5 text-left"
    >
      <h3 className="text-sm font-semibold text-rec-red">{error.title}</h3>
      <p className="mt-2 text-sm text-text-2">{error.description}</p>
      {error.canRetry && onRetry ? (
        <button
          type="button"
          onClick={onRetry}
          className="mt-4 text-xs font-bold uppercase tracking-[0.1em] text-teal hover:brightness-110"
        >
          Try again →
        </button>
      ) : null}
    </div>
  );
}
