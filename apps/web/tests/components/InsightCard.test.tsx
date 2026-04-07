import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { InsightCard } from "@/components/report/InsightCard";
import type { Insight } from "@/lib/types";

describe("InsightCard", () => {
  it("renders title, highlight, and body", () => {
    const insight: Insight = {
      kind: "undersleep",
      severity: "high",
      title: "You undersleep 13% of nights",
      body: "Adding sleep is your biggest lever.",
      highlight: { value: "+30", unit: "pp" },
    };
    render(<InsightCard insight={insight} />);
    expect(screen.getByText(/undersleep 13% of nights/i)).toBeInTheDocument();
    expect(screen.getByText("+30")).toBeInTheDocument();
    expect(screen.getByText("pp")).toBeInTheDocument();
    expect(screen.getByText(/biggest lever/i)).toBeInTheDocument();
    expect(screen.getByText("HIGH PRIORITY")).toBeInTheDocument();
  });

  it("omits unit when highlight.unit is absent", () => {
    const insight: Insight = {
      kind: "late_chronotype",
      severity: "low",
      title: "Night owl",
      body: "late bedtime",
      highlight: { value: "01:00+" },
    };
    render(<InsightCard insight={insight} />);
    expect(screen.getByText("01:00+")).toBeInTheDocument();
  });
});
