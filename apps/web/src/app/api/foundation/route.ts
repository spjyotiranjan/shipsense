import { getVersion } from "../../../lib/server/api-client";

export const dynamic = "force-dynamic";

export async function GET(request: Request): Promise<Response> {
  const started = performance.now();
  const response = await getVersion(request.signal);
  console.info(
    JSON.stringify({
      route: "/api/foundation",
      status: response.status,
      requestId: response.headers.get("x-request-id"),
      elapsedMs: Math.round(performance.now() - started),
    }),
  );
  return response;
}
