"use client";

import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { formatPeriod } from "@/lib/format";
import type { WhoopReport } from "@/lib/types";

import { ShareDialog } from "./ShareDialog";

type Props = {
  report: WhoopReport;
  canShare: boolean;
};

export function ReportHeader({ report, canShare }: Props) {
  const [open, setOpen] = useState(false);
  return (
    <header className="mb-6 flex flex-col gap-2 border-b border-white/5 pb-6 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-text-3">
          Report Period
        </div>
        <div className="mt-1 text-sm text-text-primary">
          {formatPeriod(report.period.start, report.period.end)}
          <span className="ml-2 text-text-3">· {report.period.days} days</span>
        </div>
      </div>
      {canShare ? (
        <>
          <Button onClick={() => setOpen(true)}>↗ Share Report</Button>
          <ShareDialog
            open={open}
            onClose={() => setOpen(false)}
            report={report}
          />
        </>
      ) : null}
    </header>
  );
}
