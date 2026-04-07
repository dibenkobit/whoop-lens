import type {
  ApiErrorBody,
  ShareCreateResponse,
  WhoopReport,
} from "./types";
import { apiBase } from "./url";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly body: ApiErrorBody | null,
  ) {
    super(`API error ${status}`);
  }
}

/**
 * POST /analyze — upload a Whoop export ZIP and get a WhoopReport.
 * Pass an AbortSignal to cancel on unmount.
 */
export async function analyzeZip(
  file: File,
  signal?: AbortSignal,
): Promise<WhoopReport> {
  const form = new FormData();
  form.append("file", file);
  const resp = await fetch(`${apiBase()}/analyze`, {
    method: "POST",
    body: form,
    signal,
  });
  if (!resp.ok) {
    let body: ApiErrorBody | null = null;
    try {
      body = (await resp.json()) as ApiErrorBody;
    } catch {
      body = null;
    }
    throw new ApiError(resp.status, body);
  }
  return (await resp.json()) as WhoopReport;
}

/**
 * POST /share — freeze a report as a shareable 30-day snapshot.
 */
export async function createShare(
  report: WhoopReport,
): Promise<ShareCreateResponse> {
  const resp = await fetch(`${apiBase()}/share`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ report }),
  });
  if (!resp.ok) {
    let body: ApiErrorBody | null = null;
    try {
      body = (await resp.json()) as ApiErrorBody;
    } catch {
      body = null;
    }
    throw new ApiError(resp.status, body);
  }
  return (await resp.json()) as ShareCreateResponse;
}

/**
 * GET /r/{id} — fetch a previously-shared report. Used from a Server Component.
 * Returns null on 404 (expired or missing).
 */
export async function getSharedReport(id: string): Promise<WhoopReport | null> {
  const resp = await fetch(`${apiBase()}/r/${encodeURIComponent(id)}`, {
    cache: "no-store",
  });
  if (resp.status === 404) return null;
  if (!resp.ok) {
    throw new ApiError(resp.status, null);
  }
  return (await resp.json()) as WhoopReport;
}
