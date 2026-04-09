import Link from "next/link";

const linkClass =
  "block w-full rounded-md px-3 py-2 text-[11px] font-semibold uppercase tracking-[0.1em] text-text-2 transition hover:bg-white/[0.03] hover:text-text-primary";

export function ExternalLinks({ className }: { className?: string }) {
  return (
    <ul className={className}>
      <li>
        <Link href="/about" className={linkClass}>
          About
        </Link>
      </li>
      <li>
        <a
          href="https://github.com/dibenkobit/whoop-lens"
          target="_blank"
          rel="noopener noreferrer"
          className={linkClass}
        >
          GitHub
        </a>
      </li>
    </ul>
  );
}
