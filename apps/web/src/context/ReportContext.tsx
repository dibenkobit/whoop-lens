"use client";

import {
  createContext,
  type ReactNode,
  useContext,
  useMemo,
  useState,
} from "react";

import type { WhoopReport } from "@/lib/types";

type Ctx = {
  report: WhoopReport | null;
  setReport: (report: WhoopReport | null) => void;
};

const ReportCtx = createContext<Ctx | null>(null);

export function ReportProvider({ children }: { children: ReactNode }) {
  const [report, setReport] = useState<WhoopReport | null>(null);
  const value = useMemo(() => ({ report, setReport }), [report]);
  return <ReportCtx.Provider value={value}>{children}</ReportCtx.Provider>;
}

export function useReport(): Ctx {
  const ctx = useContext(ReportCtx);
  if (!ctx) {
    throw new Error("useReport must be used inside <ReportProvider>");
  }
  return ctx;
}
