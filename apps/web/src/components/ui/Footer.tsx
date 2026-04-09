import Link from "next/link";

import { Disclaimer } from "./Disclaimer";

export function Footer() {
  return (
    <footer className="mt-16 border-t border-white/5 px-6 py-6 text-xs text-text-3">
      <div className="mx-auto flex max-w-7xl justify-between gap-8">
        <div className="flex flex-col gap-2">
          <p>
            <span className="tracking-[0.18em] font-semibold text-text-2">
              WHOOP·LENS
            </span>{" "}
            — open source, MIT licensed.
          </p>
          <Disclaimer className="max-w-xl leading-relaxed" />
        </div>
        <nav className="flex shrink-0 flex-col items-end gap-2">
          <Link href="/about" className="hover:text-text-primary">
            About
          </Link>
          <a
            href="https://github.com/dibenkobit/whoop-lens"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-text-primary"
          >
            GitHub
          </a>
        </nav>
      </div>
    </footer>
  );
}
