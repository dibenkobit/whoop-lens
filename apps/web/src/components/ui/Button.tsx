import { clsx } from "clsx";
import type { ButtonHTMLAttributes, ReactNode } from "react";

type Variant = "primary" | "secondary" | "ghost";

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: Variant;
  children: ReactNode;
};

const variantClass: Record<Variant, string> = {
  primary:
    "bg-teal text-[#001a10] hover:brightness-95 disabled:opacity-50 disabled:cursor-not-allowed",
  secondary:
    "bg-card-alt text-text-primary hover:brightness-110 disabled:opacity-50 disabled:cursor-not-allowed",
  ghost:
    "text-text-2 hover:text-text-primary hover:bg-white/5 disabled:opacity-50 disabled:cursor-not-allowed",
};

export function Button({
  variant = "primary",
  className,
  children,
  ...rest
}: Props) {
  return (
    <button
      type="button"
      className={clsx(
        "inline-flex items-center justify-center gap-2 rounded-md px-4 py-2 text-xs font-bold uppercase tracking-[0.1em] transition",
        variantClass[variant],
        className,
      )}
      {...rest}
    >
      {children}
    </button>
  );
}
