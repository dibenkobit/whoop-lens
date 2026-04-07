import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

// Mock the dynamic echarts import so jsdom doesn't need to render a canvas
vi.mock("echarts-for-react/lib/core", () => ({
  default: () => <div data-testid="echarts-stub" />,
}));

// next/dynamic treats the import as static in jsdom — Next's dynamic
// helper works fine when the module being dynamic-imported is mocked above.

import { Dial } from "@/components/report/Dial";

describe("Dial", () => {
  it("renders the display text and label", () => {
    render(
      <Dial
        value={68}
        max={100}
        color="#16EC06"
        display="68%"
        label="Avg Recovery"
        sub="57% green days"
      />,
    );
    expect(screen.getByText("68%")).toBeInTheDocument();
    expect(screen.getByText(/avg recovery/i)).toBeInTheDocument();
    expect(screen.getByText(/57% green days/i)).toBeInTheDocument();
  });

  it("omits sub when not provided", () => {
    render(
      <Dial
        value={10}
        max={21}
        color="#0093E7"
        display="10.2"
        label="Avg Strain"
      />,
    );
    expect(screen.getByText("10.2")).toBeInTheDocument();
    expect(screen.getByText(/avg strain/i)).toBeInTheDocument();
  });
});
