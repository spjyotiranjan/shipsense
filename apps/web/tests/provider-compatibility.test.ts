import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { test } from "node:test";

const require = createRequire(import.meta.url);

// Observations of the pinned factories only: no exchange, provider request,
// account linking, or evidence that the remote providers accept any option.
const options = {};

test("pinned Google defaults include state and PKCE but not nonce", () => {
  const google = require("next-auth/providers/google").default(options);
  assert.equal(google.idToken, true);
  assert.deepEqual(google.checks, ["pkce", "state"]);
});

test("pinned GitHub factory does not declare PKCE or ID-token verification", () => {
  const github = require("next-auth/providers/github").default(options);
  assert.equal(github.checks, undefined);
  assert.equal(github.idToken, undefined);
  assert.equal(typeof github.userinfo.request, "function");
});
