import type { ReactNode } from "react";

export function CardLabel({ children }: { children: ReactNode }) {
  return (
    <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-3">
      {children}
    </div>
  );
}
