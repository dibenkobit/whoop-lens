import { Card } from "@/components/report/Card";
import { CardLabel } from "@/components/report/CardLabel";
import { TopStrainDays } from "@/components/report/TopStrainDays";
import { WorkoutsList } from "@/components/report/WorkoutsList";
import type { WhoopReport } from "@/lib/types";

export function WorkoutsSection({ report }: { report: WhoopReport }) {
  if (report.workouts === null) {
    return (
      <p className="text-sm text-text-3">No workouts found in this export.</p>
    );
  }
  const { by_activity, top_strain_days, total } = report.workouts;
  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      <Card>
        <CardLabel>By activity · {total} total</CardLabel>
        <div className="mt-3">
          <WorkoutsList items={by_activity} />
        </div>
      </Card>
      <Card>
        <CardLabel>Top 10 strain days</CardLabel>
        <div className="mt-3">
          <TopStrainDays days={top_strain_days} />
        </div>
      </Card>
    </div>
  );
}
