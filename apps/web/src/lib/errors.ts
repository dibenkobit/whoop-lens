import type { ApiErrorBody } from "./types";

/**
 * Maps API error codes to human-readable copy for the upload UI.
 * Unknown codes fall back to a generic message plus the server's `code`
 * value so the user has something to include in a bug report.
 */

export type FriendlyError = {
  title: string;
  description: string;
  canRetry: boolean;
};

export function friendlyError(
  body: ApiErrorBody | null,
  httpStatus: number,
): FriendlyError {
  const code = body?.code;

  if (httpStatus >= 500) {
    return {
      title: "Something went wrong on our side",
      description: body?.error_id
        ? `Please open a GitHub issue with error code ${body.error_id}.`
        : "Please try again in a moment. If it keeps failing, open a GitHub issue.",
      canRetry: true,
    };
  }

  switch (code) {
    case "file_too_large":
      return {
        title: "File too large",
        description: `Maximum upload is ${body?.limit_mb ?? 50} MB. Whoop exports are usually a few MB.`,
        canRetry: false,
      };
    case "not_a_zip":
      return {
        title: "That doesn't look like a Whoop export",
        description:
          "We need the .zip file you got from Whoop's Export My Data feature.",
        canRetry: false,
      };
    case "corrupt_zip":
      return {
        title: "Couldn't open the zip",
        description:
          "The file may be corrupted. Try re-downloading it from your Whoop account.",
        canRetry: false,
      };
    case "missing_required_file":
      return {
        title: `Missing ${body?.file ?? "a required file"}`,
        description:
          "Your export is missing one of the required CSVs (physiological_cycles.csv or sleeps.csv). Make sure you uploaded the full export.",
        canRetry: false,
      };
    case "unexpected_schema":
      return {
        title: "Whoop changed their export format",
        description: `The file ${body?.file ?? ""} has columns we don't recognize. Please open a GitHub issue — we'll update the parser.`,
        canRetry: false,
      };
    case "no_data":
      return {
        title: "We couldn't find any data",
        description: `${body?.file ?? "The export"} contains no rows. Make sure your Whoop account has data in the time range you exported.`,
        canRetry: false,
      };
    default:
      return {
        title: "Upload failed",
        description: body?.code
          ? `Server returned code '${body.code}'. Please open a GitHub issue.`
          : "Unknown error. Please try again.",
        canRetry: httpStatus !== 400,
      };
  }
}
