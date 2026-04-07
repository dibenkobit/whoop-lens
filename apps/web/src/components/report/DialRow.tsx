import { COLORS } from "@/lib/colors";
import type { Dials } from "@/lib/types";

import { Dial } from "./Dial";

type Props = { dials: Dials };

export function DialRow({ dials }: Props) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
      <Dial
        value={Math.min(dials.sleep.value, 12)}
        max={12}
        color={COLORS.sleep}
        display={`${dials.sleep.value.toFixed(2)}h`}
        label="Avg Sleep"
        sub={`${dials.sleep.performance_pct.toFixed(0)}% performance`}
      />
      <Dial
        value={dials.recovery.value}
        max={100}
        color={
          dials.recovery.value >= 67
            ? COLORS.recGreen
            : dials.recovery.value >= 34
              ? COLORS.recYellow
              : COLORS.recRed
        }
        display={`${dials.recovery.value.toFixed(0)}%`}
        label="Avg Recovery"
        sub={`${dials.recovery.green_pct.toFixed(0)}% green days`}
      />
      <Dial
        value={dials.strain.value}
        max={21}
        color={COLORS.strain}
        display={dials.strain.value.toFixed(1)}
        label="Avg Strain"
        sub={dials.strain.label.replace("_", " ")}
      />
    </div>
  );
}
