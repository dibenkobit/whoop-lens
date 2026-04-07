"use client";

import { type ReactNode, useState } from "react";

import type { WhoopReport } from "@/lib/types";

import { ReportHeader } from "./ReportHeader";
import { type SectionKey, Sidebar } from "./Sidebar";

type Props = {
  report: WhoopReport;
  canShare: boolean;
  renderSection: (key: SectionKey) => ReactNode;
};

export function ReportShell({ report, canShare, renderSection }: Props) {
  const [section, setSection] = useState<SectionKey>("overview");
  return (
    <div className="mx-auto grid max-w-7xl grid-cols-1 lg:grid-cols-[220px_1fr]">
      <Sidebar active={section} onChange={setSection} report={report} />
      <div className="px-6 py-8 lg:px-10">
        <ReportHeader report={report} canShare={canShare} />
        {renderSection(section)}
      </div>
    </div>
  );
}
