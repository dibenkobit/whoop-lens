import { afterEach, beforeEach, describe, expect, it } from "vitest";

import { apiBase } from "@/lib/url";

describe("apiBase", () => {
  const originalEnv = { ...process.env };

  beforeEach(() => {
    delete process.env.NEXT_PUBLIC_API_URL;
    delete process.env.INTERNAL_API_URL;
  });

  afterEach(() => {
    process.env = { ...originalEnv };
  });

  it("returns the default when no env is set", () => {
    expect(apiBase()).toBe("http://localhost:8000");
  });

  it("strips a single trailing slash", () => {
    process.env.NEXT_PUBLIC_API_URL = "https://api.example.com/";
    expect(apiBase()).toBe("https://api.example.com");
  });

  it("strips multiple trailing slashes", () => {
    process.env.NEXT_PUBLIC_API_URL = "https://api.example.com///";
    expect(apiBase()).toBe("https://api.example.com");
  });

  it("preserves a clean URL unchanged", () => {
    process.env.NEXT_PUBLIC_API_URL = "https://api.example.com";
    expect(apiBase()).toBe("https://api.example.com");
  });
});
