import {
  isVersion,
  readBoundedJson,
  type ApiError,
} from "../diagnostic-contract.ts";

export const failureMessages = {
  API_UNAVAILABLE: "The API is unavailable. Retry the connection.",
  API_TIMEOUT: "The API took too long to respond. Retry the connection.",
  UPSTREAM_CONTRACT_INVALID:
    "The API returned an invalid response. Retry the connection.",
} as const;

export async function requestVersion(
  origin: string | undefined,
  signal: AbortSignal,
  fetcher: typeof fetch = fetch,
): Promise<Response> {
  const requestId = crypto.randomUUID();
  const headers = { "Cache-Control": "no-store", "X-Request-ID": requestId };
  function failure(
    code: keyof typeof failureMessages,
    status: number,
  ): Response {
    const body: ApiError = {
      error: {
        code,
        message: failureMessages[code],
        requestId,
        retryable: true,
      },
    };
    return Response.json(body, { status, headers });
  }
  // This credential-free profile deliberately allows only the documented local
  // API. A deployment origin requires an explicit deployment configuration policy.
  if (origin !== "http://127.0.0.1:8000" && origin !== "http://localhost:8000")
    return failure("API_UNAVAILABLE", 502);
  const deadline = AbortSignal.timeout(5_000);
  const combined = AbortSignal.any([signal, deadline]);
  try {
    const response = await fetcher(`${origin}/api/v1/version`, {
      cache: "no-store",
      redirect: "error",
      headers: { "X-Request-ID": requestId, Accept: "application/json" },
      signal: combined,
    });
    if (!response.ok) {
      await response.body?.cancel();
      return failure("API_UNAVAILABLE", 502);
    }
    let body: unknown;
    try {
      body = await readBoundedJson(response);
    } catch {
      combined.throwIfAborted();
      return failure("UPSTREAM_CONTRACT_INVALID", 502);
    }
    combined.throwIfAborted();
    if (!isVersion(body) || response.headers.get("x-request-id") !== requestId)
      return failure("UPSTREAM_CONTRACT_INVALID", 502);
    return Response.json(body, { headers });
  } catch {
    if (signal.aborted) throw signal.reason;
    return failure(
      deadline.aborted ? "API_TIMEOUT" : "API_UNAVAILABLE",
      deadline.aborted ? 504 : 502,
    );
  }
}
