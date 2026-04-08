import { Card } from "@/components/report/Card";
import { CardLabel } from "@/components/report/CardLabel";
import { JournalList } from "@/components/report/JournalList";
import type { WhoopReport } from "@/lib/types";

export function JournalSection({ report }: { report: WhoopReport }) {
  if (report.journal === null) {
    return (
      <p className="text-sm text-text-3">No journal data in this export.</p>
    );
  }
  const { days_logged, questions, note } = report.journal;
  return (
    <div className="flex flex-col gap-4">
      <Card>
        <CardLabel>Journal · {days_logged} days logged</CardLabel>
        <p className="mt-2 text-sm text-text-2">{note}</p>
        <div className="mt-4">
          <JournalList questions={questions} />
        </div>
      </Card>
    </div>
  );
}
