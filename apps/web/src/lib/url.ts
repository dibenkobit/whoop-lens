/**
 * Resolves the backend API base URL.
 *
 * In the browser, reads NEXT_PUBLIC_API_URL (baked at build time).
 * On the server, allows an optional INTERNAL_API_URL override for
 * server-to-server calls on the same private network (e.g., Railway internal),
 * falling back to NEXT_PUBLIC_API_URL.
 */
export function apiBase(): string {
  const raw =
    typeof window === "undefined"
      ? (process.env.INTERNAL_API_URL ??
          process.env.NEXT_PUBLIC_API_URL ??
          "http://localhost:8000")
      : (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000");
  return raw.replace(/\/+$/, "");
}
