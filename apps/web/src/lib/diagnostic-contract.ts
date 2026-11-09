import type {
  ApiError,
  VersionResponse,
} from "../../../../packages/contracts/src/consumption";

export type { ApiError, VersionResponse };

function record(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

// The generated FastAPI types remain canonical. These guards enforce their
// constraints at runtime; freshness is an additional diagnostic requirement.
export function isVersion(
  value: unknown,
  now = Date.now(),
): value is VersionResponse {
  if (
    !record(value) ||
    Object.keys(value).sort().join() !== "apiVersion,observedAt,service,version"
  )
    return false;
  if (
    value.service !== "shipsense-api" ||
    value.apiVersion !== "v1" ||
    typeof value.version !== "string" ||
    !/^[A-Za-z0-9._-]{1,64}$/.test(value.version) ||
    typeof value.observedAt !== "string"
  )
    return false;
  const match =
    /^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(?:\.\d{1,6})?(?:Z|\+00:00)$/.exec(
      value.observedAt,
    );
  const time = Date.parse(value.observedAt);
  return (
    !!match &&
    Number.isFinite(time) &&
    new Date(time).toISOString().slice(0, 19) === match[1] &&
    time <= now + 5_000 &&
    time >= now - 60_000
  );
}

export async function readBoundedJson(response: Response): Promise<unknown> {
  if (
    response.headers.get("content-type")?.split(";")[0].trim() !==
    "application/json"
  ) {
    await response.body?.cancel();
    throw new Error("Invalid diagnostic content");
  }
  const length = response.headers.get("content-length");
  if (length && (!/^\d+$/.test(length) || Number(length) > 4096)) {
    await response.body?.cancel();
    throw new Error("Invalid diagnostic size");
  }
  const reader = response.body?.getReader();
  if (!reader) throw new Error("Missing diagnostic body");
  let size = 0;
  const chunks: Uint8Array[] = [];
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      size += value.byteLength;
      if (size > 4096) throw new Error("Invalid diagnostic size");
      chunks.push(value);
    }
    const body = new Uint8Array(size);
    let offset = 0;
    for (const chunk of chunks) {
      body.set(chunk, offset);
      offset += chunk.byteLength;
    }
    return JSON.parse(
      new TextDecoder("utf-8", { fatal: true }).decode(body),
    ) as unknown;
  } finally {
    await reader.cancel().catch(() => undefined);
    reader.releaseLock();
  }
}
