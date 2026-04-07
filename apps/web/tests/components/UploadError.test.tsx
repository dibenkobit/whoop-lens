import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { UploadError } from "@/components/upload/UploadError";

describe("UploadError", () => {
  it("renders title and description", () => {
    render(
      <UploadError
        error={{
          title: "File too large",
          description: "Max 50 MB.",
          canRetry: false,
        }}
      />,
    );
    expect(screen.getByText("File too large")).toBeInTheDocument();
    expect(screen.getByText(/max 50 mb/i)).toBeInTheDocument();
  });

  it("shows retry button when canRetry", () => {
    const onRetry = vi.fn();
    render(
      <UploadError
        error={{ title: "x", description: "y", canRetry: true }}
        onRetry={onRetry}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /try again/i }));
    expect(onRetry).toHaveBeenCalledOnce();
  });

  it("hides retry when canRetry is false", () => {
    render(
      <UploadError
        error={{ title: "x", description: "y", canRetry: false }}
        onRetry={() => {}}
      />,
    );
    expect(screen.queryByRole("button", { name: /try again/i })).toBeNull();
  });
});
