"use client";

import { clsx } from "clsx";
import { useCallback } from "react";
import { type FileRejection, useDropzone } from "react-dropzone";

type Props = {
  onFile: (file: File) => void;
  onReject?: (message: string) => void;
  disabled?: boolean;
};

export function Dropzone({ onFile, onReject, disabled }: Props) {
  const onDrop = useCallback(
    (files: File[]) => {
      const file = files[0];
      if (file) onFile(file);
    },
    [onFile],
  );
  const onDropRejected = useCallback(
    (rejections: FileRejection[]) => {
      if (!onReject) return;
      const code = rejections[0]?.errors[0]?.code;
      if (code === "file-invalid-type") {
        onReject("Please drop a .zip file from your Whoop export.");
      } else if (code === "too-many-files") {
        onReject("Please drop one file at a time.");
      } else {
        onReject("Couldn't accept that file. Please drop a single .zip.");
      }
    },
    [onReject],
  );
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    onDropRejected,
    accept: { "application/zip": [".zip"] },
    maxFiles: 1,
    multiple: false,
    disabled,
  });

  return (
    <div
      {...getRootProps()}
      className={clsx(
        "group flex min-h-[280px] cursor-pointer flex-col items-center justify-center rounded-3xl border-2 border-dashed border-white/15 bg-card/50 px-8 py-12 text-center transition-all duration-300 hover:border-teal/60",
        isDragActive && "border-teal bg-teal/5",
        disabled && "pointer-events-none opacity-60",
      )}
    >
      <input {...getInputProps()} />
      <div className="text-[10px] font-semibold uppercase tracking-[0.2em] text-text-3">
        Step 1
      </div>
      <h2 className="mt-2 text-3xl font-bold text-text-primary">
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
