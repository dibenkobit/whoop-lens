"use client";

import { clsx } from "clsx";
import type { ReactNode } from "react";
import { useEffect } from "react";

type Props = {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  className?: string;
};

export function Dialog({ open, onClose, title, children, className }: Props) {
  useEffect(() => {
    if (!open) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={title}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
      onClick={onClose}
      onKeyDown={(e) => e.key === "Escape" && onClose()}
    >
      <div
        role="document"
        className={clsx(
          "w-full max-w-md rounded-xl bg-card p-6 shadow-2xl",
          className,
        )}
        onClick={(e) => e.stopPropagation()}
        onKeyDown={(e) => e.stopPropagation()}
      >
        <h2 className="mb-4 text-sm font-bold uppercase tracking-[0.12em] text-text-2">
          {title}
        </h2>
        {children}
      </div>
    </div>
  );
}
