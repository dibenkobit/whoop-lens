"use client";

import { ReportShell } from "@/components/report/ReportShell";
import { JournalSection } from "@/components/report/sections/JournalSection";
import { OverviewSection } from "@/components/report/sections/OverviewSection";
import { RecoverySection } from "@/components/report/sections/RecoverySection";
import { SleepSection } from "@/components/report/sections/SleepSection";
import { StrainSection } from "@/components/report/sections/StrainSection";
import { TrendsSection } from "@/components/report/sections/TrendsSection";
import { WorkoutsSection } from "@/components/report/sections/WorkoutsSection";
import type { WhoopReport } from "@/lib/types";

export function SharedReportView({ report }: { report: WhoopReport }) {
  return (
    <ReportShell
      report={report}
      canShare={false}
      renderSection={(key) => {
        switch (key) {
          case "overview":
            return <OverviewSection report={report} />;
          case "recovery":
            return <RecoverySection report={report} />;
          case "sleep":
            return <SleepSection report={report} />;
          case "strain":
            return <StrainSection report={report} />;
          case "trends":
            return <TrendsSection report={report} />;
          case "workouts":
            return <WorkoutsSection report={report} />;
          case "journal":
            return <JournalSection report={report} />;
        }
      }}
    />
  );
}
