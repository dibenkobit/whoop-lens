import { clsx } from "clsx";
import type { ReactNode } from "react";

type Props = {
  children: ReactNode;
  className?: string;
};

export function Card({ children, className }: Props) {
  return (
    <div className={clsx("rounded-2xl bg-card p-5", className)}>{children}</div>
  );
}
