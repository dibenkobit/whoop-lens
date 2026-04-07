"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { ReportShell } from "@/components/report/ReportShell";
import { OverviewSection } from "@/components/report/sections/OverviewSection";
import { RecoverySection } from "@/components/report/sections/RecoverySection";
import { useReport } from "@/context/ReportContext";

export default function ReportPage() {
  const router = useRouter();
  const { report } = useReport();

  useEffect(() => {
    if (!report) router.replace("/");
  }, [report, router]);

  if (!report) return null;

  return (
    <ReportShell
      report={report}
      canShare={true}
      renderSection={(key) => {
        if (key === "overview") return <OverviewSection report={report} />;
        if (key === "recovery") return <RecoverySection report={report} />;
        return (
          <div className="rounded-2xl bg-card p-5 text-sm text-text-2">
            Section: <span className="font-mono">{key}</span> — placeholder.
          </div>
        );
      }}
    />
  );
}
