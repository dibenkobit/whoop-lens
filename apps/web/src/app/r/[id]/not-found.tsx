import Link from "next/link";

export default function NotFound() {
  return (
    <div className="mx-auto max-w-xl px-6 py-24 text-center">
      <div className="text-[11px] uppercase tracking-[0.2em] text-text-3">
        404
      </div>
      <h1 className="mt-3 text-3xl font-bold text-text-primary">
        This report no longer exists
      </h1>
      <p className="mt-4 text-sm text-text-2">
        Shared reports live for 30 days. It may have expired, or the link may be
        wrong.
      </p>
      <Link
        href="/"
        className="mt-8 inline-block text-xs font-bold uppercase tracking-[0.1em] text-teal hover:brightness-110"
      >
        Upload your own →
      </Link>
    </div>
  );
}
