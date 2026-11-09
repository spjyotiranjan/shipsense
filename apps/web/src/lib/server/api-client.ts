import "server-only";
import { requestVersion } from "./api-transport";

export function getVersion(signal: AbortSignal): Promise<Response> {
  return requestVersion(process.env.SHIPSENSE_API_ORIGIN, signal);
}
