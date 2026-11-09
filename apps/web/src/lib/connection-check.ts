import {
  isVersion,
  readBoundedJson,
  type VersionResponse,
} from "./diagnostic-contract.ts";

export type ConnectionState =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "connected"; version: VersionResponse }
  | { kind: "unavailable"; message: string; requestId?: string };

const safeMessages: Record<string, string> = {
  API_UNAVAILABLE: "The API is unavailable. Retry the connection.",
  API_TIMEOUT: "The API took too long to respond. Retry the connection.",
  UPSTREAM_CONTRACT_INVALID:
    "The API returned an invalid response. Retry the connection.",
};

// The attempt identity protects state even when a transport ignores abort.
export function createConnectionCheck(
  publish: (state: ConnectionState) => void,
  fetcher: typeof fetch = fetch,
) {
  let current: AbortController | undefined;
  let attempt = 0;
  return {
    async run() {
      if (current) return;
      const controller = new AbortController();
      current = controller;
      const identity = ++attempt;
      publish({ kind: "loading" });
      try {
        const response = await fetcher("/api/foundation", {
          cache: "no-store",
          signal: AbortSignal.any([
            controller.signal,
            AbortSignal.timeout(7_000),
          ]),
        });
        const body = await readBoundedJson(response);
        if (controller.signal.aborted || identity !== attempt) return;
        if (response.ok && isVersion(body))
          publish({ kind: "connected", version: body });
        else {
          const reference = response.headers.get("x-request-id");
          // Never render upstream messages, even from a same-origin error.
          const code =
            typeof body === "object" &&
            body !== null &&
            "error" in body &&
            typeof body.error === "object" &&
            body.error !== null &&
            "code" in body.error &&
            typeof body.error.code === "string"
              ? body.error.code
              : "";
          publish({
            kind: "unavailable",
            message:
              safeMessages[code] ??
              "The connection could not be verified. Retry the connection.",
            ...(reference && /^[A-Za-z0-9_-]{1,64}$/.test(reference)
              ? { requestId: reference }
              : {}),
          });
        }
      } catch {
        if (!controller.signal.aborted && identity === attempt)
          publish({
            kind: "unavailable",
            message:
              "The connection could not be verified. Retry the connection.",
          });
      } finally {
        if (identity === attempt) current = undefined;
      }
    },
    cancel() {
      attempt++;
      current?.abort();
      current = undefined;
    },
  };
}
