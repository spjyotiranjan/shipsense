import type { components, paths } from "./generated.js";

// Compile-time proof that consumers use the API-generated response contract.
export type FoundationResponse =
  paths["/foundation"]["get"]["responses"][200]["content"]["application/json"];
export const localFoundation: FoundationResponse = {
  service: "shipsense-api",
  mode: "local-foundation",
};

export type VersionResponse =
  paths["/api/v1/version"]["get"]["responses"][200]["content"]["application/json"];
export type ApiError =
  paths["/api/v1/version"]["get"]["responses"][422]["content"]["application/json"];

// Schema-only foundation: no identity directory endpoint exists yet.
export type IdentityContract = components["schemas"]["IdentityContract"];
export type RoleGrant = components["schemas"]["RoleGrant"];
