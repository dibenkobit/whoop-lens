"use client";

type Props = {
  stage: "uploading" | "parsing" | "analyzing";
};

const LABELS: Record<Props["stage"], string> = {
  uploading: "Uploading your export…",
  parsing: "Parsing CSVs…",
  analyzing: "Computing insights…",
};

export function UploadProgress({ stage }: Props) {
  return (
    <div className="flex min-h-[280px] flex-col items-center justify-center rounded-3xl bg-card px-8 py-12 text-center">
      <div className="h-10 w-10 animate-spin rounded-full border-4 border-white/10 border-t-teal" />
      <p className="mt-6 text-sm uppercase tracking-[0.15em] text-text-2">
        {LABELS[stage]}
      </p>
    </div>
  );
}
