import { readBoundedJson } from "../diagnostic-contract.ts";
import { serviceCredential, type SigningKey } from "./service-credential.ts";
import {
  deadline,
  type SessionAuthority,
  type Snapshot,
} from "./session-bridge.ts";

// Explicit composition only. Runtime currently uses unavailableAuthority.
// A deployed origin/credential source requires its own accepted configuration.
export function apiSessionAuthority(
  origin: string,
  key: SigningKey,
  fetcher: typeof fetch = fetch,
): SessionAuthority {
  if (origin !== "http://127.0.0.1:8000")
    throw new Error("AUTHORITY_UNAVAILABLE");
  async function call(
    handle: string,
    correlationId: string,
    action: "resolve" | "revoke",
  ): Promise<unknown> {
    try {
      if (
        !/^[A-Za-z0-9_-]{43}$/.test(handle) ||
        !/^[A-Za-z0-9_-]{1,64}$/.test(correlationId)
      )
        throw new Error();
      const response = await fetcher(
        `${origin}/internal/v1/auth/session/${action}`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${serviceCredential(key, `session:${action}`)}`,
            "Content-Type": "application/json",
            "X-Request-ID": correlationId,
          },
          body: JSON.stringify({ handle }),
          signal: AbortSignal.timeout(3000),
          cache: "no-store",
          redirect: "error",
        },
      );
      if (
        !response.ok ||
        response.headers.get("x-request-id") !== correlationId
      ) {
        await response.body?.cancel();
        throw new Error();
      }
      return await readBoundedJson(response);
    } catch {
      throw new Error("AUTHORITY_UNAVAILABLE");
    }
  }
  return {
    async resolve(handle, correlationId) {
      const value = await call(handle, correlationId, "resolve");
      if (
        !value ||
        typeof value !== "object" ||
        Array.isArray(value) ||
        Object.keys(value).sort().join(",") !==
          "absoluteExpiresAt,createdAt,idleExpiresAt,lastActivityAt"
      )
        throw new Error("AUTHORITY_UNAVAILABLE");
      const snapshot = value as Snapshot;
      deadline(snapshot);
      return snapshot;
    },
    async revoke(handle, correlationId) {
      const value = await call(handle, correlationId, "revoke");
      if (
        !value ||
        typeof value !== "object" ||
        Object.keys(value).join(",") !== "state" ||
        (value as { state: unknown }).state !== "revoked"
      )
        throw new Error("AUTHORITY_UNAVAILABLE");
    },
  };
}
