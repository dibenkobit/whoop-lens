import { COLORS } from "@/lib/colors";
import type { RecoveryDistribution as DistType } from "@/lib/types";

export function RecoveryDistribution({
  distribution,
}: {
  distribution: DistType;
}) {
  return (
    <div className="space-y-2">
      <div className="flex h-3 w-full overflow-hidden rounded-sm">
        <div
          style={{
            width: `${distribution.green}%`,
            backgroundColor: COLORS.recGreen,
          }}
        />
        <div
          style={{
            width: `${distribution.yellow}%`,
            backgroundColor: COLORS.recYellow,
          }}
        />
        <div
          style={{
            width: `${distribution.red}%`,
            backgroundColor: COLORS.recRed,
          }}
        />
      </div>
      <div className="flex justify-between text-[10px] text-text-3">
        <span style={{ color: COLORS.recGreen }}>
          {distribution.green.toFixed(0)}% green
        </span>
        <span style={{ color: COLORS.recYellow }}>
          {distribution.yellow.toFixed(0)}% yellow
        </span>
        <span style={{ color: COLORS.recRed }}>
          {distribution.red.toFixed(0)}% red
        </span>
      </div>
    </div>
  );
}
