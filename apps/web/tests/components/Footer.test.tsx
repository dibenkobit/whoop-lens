import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Footer } from "@/components/ui/Footer";

describe("Footer", () => {
  it("renders the WHOOP disclaimer", () => {
    render(<Footer />);
    expect(
      screen.getByText(/not affiliated with.*whoop, inc/i),
    ).toBeInTheDocument();
  });

  it("links to /about and to the GitHub repo", () => {
    render(<Footer />);
    const about = screen.getByRole("link", { name: /about/i });
    expect(about).toHaveAttribute("href", "/about");
    const repo = screen.getByRole("link", { name: /github/i });
    expect(repo.getAttribute("href")).toMatch(/github\.com/);
  });
});
