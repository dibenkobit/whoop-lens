"use client";

import { clsx } from "clsx";
import { useCallback } from "react";
import { useDropzone } from "react-dropzone";

type Props = {
  onFile: (file: File) => void;
  disabled?: boolean;
};

export function Dropzone({ onFile, disabled }: Props) {
  const onDrop = useCallback(
    (files: File[]) => {
      const file = files[0];
      if (file) onFile(file);
    },
    [onFile],
  );
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/zip": [".zip"] },
    maxFiles: 1,
    multiple: false,
    disabled,
  });

  return (
    <div
      {...getRootProps()}
      className={clsx(
        "group flex min-h-[280px] cursor-pointer flex-col items-center justify-center rounded-3xl border-2 border-dashed border-white/15 bg-card/50 px-8 py-12 text-center transition",
        isDragActive && "border-teal bg-teal/5",
        disabled && "pointer-events-none opacity-60",
      )}
    >
      <input {...getInputProps()} />
      <div className="text-[10px] font-semibold uppercase tracking-[0.2em] text-text-3">
        Step 1
      </div>
      <h2 className="mt-2 font-mono text-3xl font-bold text-text-primary">
        Drop your <span className="text-teal">my_whoop_data</span>.zip
      </h2>
      <p className="mt-4 max-w-lg text-sm leading-relaxed text-text-2">
        Get your export from the Whoop app · Settings · Data · Export My Data.
        We analyze it in memory and never store the CSVs.
      </p>
      <p className="mt-6 text-[11px] uppercase tracking-[0.15em] text-text-3">
        {isDragActive ? "Drop it" : "or click to browse"}
      </p>
    </div>
  );
}
