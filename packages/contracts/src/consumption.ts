import type { paths } from "./generated.js";

// Compile-time proof that consumers use the API-generated response contract.
export type FoundationResponse = paths["/foundation"]["get"]["responses"][200]["content"]["application/json"];
export const localFoundation: FoundationResponse = { service: "shipsense-api", mode: "local-foundation" };
