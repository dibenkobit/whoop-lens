import Link from "next/link";

export default function AboutPage() {
  return (
    <div className="mx-auto max-w-2xl px-6 py-16">
      <div className="text-[11px] uppercase tracking-[0.2em] text-text-3">
        About
      </div>
      <h1 className="mt-3 text-3xl font-bold text-text-primary">
        Whoop Lens
      </h1>
      <p className="mt-6 text-sm leading-relaxed text-text-2">
        Whoop Lens is an open-source web app that takes a Whoop data export ZIP
        and turns it into a visual report styled after the Whoop app. Drop your
        file, get insights in seconds. Nothing is stored unless you explicitly
        share a report.
      </p>
      <h2 className="mt-10 text-sm font-bold uppercase tracking-[0.1em] text-text-2">
        How it works
      </h2>
      <ol className="mt-3 list-decimal space-y-2 pl-5 text-sm text-text-2">
        <li>Export your data from Whoop (Settings · Data · Export My Data).</li>
        <li>Drop the ZIP onto the landing page.</li>
        <li>
          We parse it in memory, compute the metrics and insights, and render
          the report. Your CSVs never hit our database.
        </li>
        <li>
          If you want to share the report, click <em>Share</em>. That saves the
          computed JSON (no CSVs) for 30 days under an anonymous URL.
        </li>
      </ol>
      <h2 className="mt-10 text-sm font-bold uppercase tracking-[0.1em] text-text-2">
        What the export should look like
      </h2>
      <p className="mt-3 text-sm text-text-2">
        Your ZIP should contain these files at the top level:
      </p>
      <ul className="mt-2 list-disc space-y-1 pl-5 text-xs text-text-primary">
        <li>physiological_cycles.csv (required)</li>
        <li>sleeps.csv (required)</li>
        <li>workouts.csv (optional)</li>
        <li>journal_entries.csv (optional)</li>
      </ul>
      <h2 className="mt-10 text-sm font-bold uppercase tracking-[0.1em] text-text-2">
        Privacy
      </h2>
      <p className="mt-3 text-sm text-text-2">
        We don't log, track, or analyze usage. No cookies, no accounts. Shared
        reports expire after 30 days and we only store the computed aggregates
        (never the raw CSVs).
      </p>
      <h2 className="mt-10 text-sm font-bold uppercase tracking-[0.1em] text-text-2">
        Disclaimer
      </h2>
      <p className="mt-3 text-sm text-text-2">
        Whoop Lens is an independent open-source project. Not affiliated with,
        endorsed by, or sponsored by WHOOP, Inc. WHOOP is a trademark of WHOOP,
        Inc. No Whoop source code, logos, or proprietary assets are used in this
        project.
      </p>
      <Link
        href="/"
        className="mt-10 inline-block text-xs font-bold uppercase tracking-[0.1em] text-teal hover:brightness-110"
      >
        ← Back to upload
      </Link>
    </div>
  );
}
