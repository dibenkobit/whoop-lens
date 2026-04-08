import Link from "next/link";

export function Footer() {
  return (
    <footer className="mt-16 border-t border-white/5 px-6 py-6 text-xs text-text-3">
      <div className="mx-auto flex max-w-7xl flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <p>
          <span className="tracking-[0.18em] font-semibold text-text-2">
            WHOOP·LENS
          </span>{" "}
          — open source, MIT licensed.
        </p>
        <p className="max-w-xl leading-relaxed">
          Whoop Lens is an independent open-source project. Not affiliated with,
          endorsed by, or sponsored by WHOOP, Inc. WHOOP is a trademark of
          WHOOP, Inc.
        </p>
        <div className="flex gap-4">
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
        </div>
      </div>
    </footer>
  );
}
