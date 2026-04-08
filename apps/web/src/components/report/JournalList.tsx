import type { JournalQuestionAgg } from "@/lib/types";

function delta(
  yes: number | null,
  no: number | null,
): { value: string; tone: string } {
  if (yes === null || no === null) {
    return { value: "—", tone: "var(--color-text-3)" };
  }
  const d = yes - no;
  const sign = d >= 0 ? "+" : "";
  return {
    value: `${sign}${d.toFixed(0)}`,
    tone: d >= 0 ? "var(--color-rec-green)" : "var(--color-rec-red)",
  };
}

export function JournalList({
  questions,
}: {
  questions: JournalQuestionAgg[];
}) {
  if (questions.length === 0) {
    return <p className="text-sm text-text-3">No journal entries logged.</p>;
  }
  return (
    <table className="w-full text-xs">
      <thead>
        <tr className="text-[10px] uppercase tracking-[0.12em] text-text-3">
          <th className="text-left">Question</th>
          <th className="text-right">Yes</th>
          <th className="text-right">No</th>
          <th className="text-right">ΔRec</th>
        </tr>
      </thead>
      <tbody>
        {questions.map((q) => {
          const d = delta(q.mean_rec_yes, q.mean_rec_no);
          return (
            <tr key={q.question} className="border-t border-white/5">
              <td className="py-2 text-text-2">{q.question}</td>
              <td className="py-2 text-right font-mono text-text-primary">
                {q.yes}
              </td>
              <td className="py-2 text-right font-mono text-text-3">{q.no}</td>
              <td
                className="py-2 text-right font-mono font-bold"
                style={{ color: d.tone }}
              >
                {d.value}
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
