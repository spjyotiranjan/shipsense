import assert from "node:assert/strict";
import { generateKeyPairSync, randomBytes } from "node:crypto";
import { createRequire } from "node:module";
import { test } from "node:test";
import { decode, encode } from "next-auth/jwt";
import {
  bridgeOptions,
  bridgeRequest,
  clampCookies,
  cookieName,
  cookieToken,
  deadline,
  nowSeconds,
  sessionCookies,
  unavailableAuthority,
  type SessionAuthority,
} from "../src/lib/server/session-bridge.ts";
import { serviceCredential } from "../src/lib/server/service-credential.ts";
import { apiSessionAuthority } from "../src/lib/server/api-session-authority.ts";

const secret = randomBytes(32).toString("base64url");
const handle = randomBytes(32).toString("base64url");
const snapshot = () => ({
  createdAt: nowSeconds() - 500,
  lastActivityAt: nowSeconds() - 100,
  absoluteExpiresAt: nowSeconds() + 400,
  idleExpiresAt: nowSeconds() + 500,
});
const canonical = () => ({ handle, ...snapshot() });
const request = (cookie?: string, headers?: HeadersInit) =>
  new Request("https://shipsense.test/api/auth/session", {
    headers: { ...(cookie ? { cookie } : {}), ...headers },
  });
const authority: SessionAuthority = {
  async resolve() {
    return snapshot();
  },
  async revoke() {},
};

// Actual pinned library API handler, using public exports. App Router wiring is
// additionally checked through the built Next server; fixtures never enable it.
const NextAuth = createRequire(import.meta.url)("next-auth").default;
async function library(
  request: Request,
  options: ReturnType<typeof bridgeOptions>,
): Promise<Response> {
  assert.equal(request.headers.get("authorization"), null);
  const headers = new Headers();
  let status = 200;
  let body: unknown;
  const res = {
    status(value: number) {
      status = value;
      return res;
    },
    getHeader(name: string) {
      return name.toLowerCase() === "set-cookie"
        ? headers.getSetCookie()
        : headers.get(name);
    },
    setHeader(name: string, value: string | string[]) {
      headers.delete(name);
      for (const entry of Array.isArray(value) ? value : [value])
        headers.append(name, entry);
    },
    send(value: unknown) {
      body = value;
    },
    json(value: unknown) {
      body = value;
    },
    end() {},
  };
  await NextAuth(
    {
      method: "GET",
      query: { nextauth: ["session"] },
      cookies: Object.fromEntries(sessionCookies(request)),
      headers: Object.fromEntries(request.headers),
    },
    res,
    options,
  );
  return new Response(typeof body === "string" ? body : JSON.stringify(body), {
    status,
    headers,
  });
}

test("cookie-only extraction rejects duplicate, mixed, gapped and malformed chunks", async () => {
  const encrypted = await encode({ secret, token: canonical(), maxAge: 400 });
  assert.equal(
    await cookieToken(
      request(undefined, { Authorization: `Bearer ${encrypted}` }),
      secret,
    ),
    null,
  );
  assert.equal(
    (await cookieToken(request(`${cookieName}=${encrypted}`), secret))?.handle,
    handle,
  );
  const split = Math.floor(encrypted.length / 2);
  assert.equal(
    (
      await cookieToken(
        request(
          `${cookieName}.1=${encrypted.slice(split)}; ${cookieName}.0=${encrypted.slice(0, split)}`,
        ),
        secret,
      )
    )?.handle,
    handle,
  );
  for (const cookie of [
    `${cookieName}=a; ${cookieName}=b`,
    `${cookieName}=a; ${cookieName}.0=b`,
    `${cookieName}.1=a`,
    `${cookieName}.bad=a`,
    `${cookieName}.8=a`,
    `${cookieName}suffix=a`,
    `${cookieName}=bad%00`,
    "x".repeat(32769),
  ])
    assert.throws(() => sessionCookies(request(cookie)));
  await assert.rejects(
    cookieToken(
      request(`${cookieName}=${encrypted}`),
      randomBytes(32).toString("hex"),
    ),
  );
});

test("absolute and idle expiry reject malformed, forged deadlines and expired envelopes", async () => {
  const token = canonical();
  assert.equal(deadline(token), token.absoluteExpiresAt);
  for (const change of [
    { absoluteExpiresAt: token.createdAt + 901 },
    { idleExpiresAt: token.lastActivityAt + 601 },
    { createdAt: true },
    { lastActivityAt: nowSeconds() + 1 },
    { idleExpiresAt: nowSeconds() },
  ])
    assert.throws(() => deadline({ ...token, ...change } as typeof token));
  const expired = await encode({
    secret,
    token: { ...token, idleExpiresAt: nowSeconds() - 1 },
    maxAge: 400,
  });
  await assert.rejects(
    cookieToken(request(`${cookieName}=${expired}`), secret),
  );
});

test("actual NextAuth session renewal bounds JWE, public DTO and cookie expiration", async () => {
  const token = canonical();
  const encrypted = await encode({
    secret,
    token: {
      ...token,
      accessToken: "never-public",
      email: "private@example.invalid",
    },
    maxAge: 400,
  });
  const response = await bridgeRequest(
    request(`${cookieName}=${encrypted}`, { Authorization: "Bearer ignored" }),
    "session",
    {
      ...authority,
      async resolve() {
        return token;
      },
    },
    secret,
    library,
  );
  assert.equal(response.status, 200);
  const body = await response.json();
  assert.deepEqual(body, {
    expires: new Date(token.absoluteExpiresAt * 1000).toISOString(),
  });
  assert.equal(response.headers.get("cache-control"), "no-store");
  const renewed = response.headers
    .getSetCookie()
    .find((cookie) => cookie.startsWith(cookieName + "="))!;
  const value = renewed.slice(renewed.indexOf("=") + 1, renewed.indexOf(";"));
  const decoded = await decode({ secret, token: value });
  assert.ok(
    decoded &&
      typeof decoded.exp === "number" &&
      decoded.exp <= token.absoluteExpiresAt,
  );
  assert.equal(decoded.accessToken, undefined);
  assert.match(renewed, /HttpOnly/i);
  assert.match(renewed, /Secure/i);
  assert.match(renewed, /SameSite=Lax/i);
  assert.doesNotMatch(renewed, /Max-Age=/);
  assert.equal(
    renewed.match(/Expires=([^;]+)/)?.[1],
    new Date(token.absoluteExpiresAt * 1000).toUTCString(),
  );
});

test("chunk cleanup, deletion and outgoing chunk expiry retain security attributes", async () => {
  const token = canonical();
  // Older oversized cookie may contain irrelevant claims. They are discarded.
  const encrypted = await encode({
    secret,
    token: { ...token, padding: "x".repeat(5000) },
    maxAge: 400,
  });
  const cookie = `${cookieName}.0=${encrypted.slice(0, 3900)}; ${cookieName}.1=${encrypted.slice(3900)}`;
  const response = await bridgeRequest(
    request(cookie),
    "session",
    {
      ...authority,
      async resolve() {
        return token;
      },
    },
    secret,
    library,
  );
  assert.equal(response.status, 200);
  for (const name of [`${cookieName}.0`, `${cookieName}.1`])
    assert.ok(
      response.headers
        .getSetCookie()
        .some(
          (entry) => entry.startsWith(`${name}=;`) && /Max-Age=0/i.test(entry),
        ),
    );
  const chunks = new Response(null, {
    headers: [
      [
        "Set-Cookie",
        `${cookieName}.0=aaa; Path=/; HttpOnly; Secure; SameSite=Lax; Expires=Fri, 01 Jan 2100 00:00:00 GMT`,
      ],
      [
        "Set-Cookie",
        `${cookieName}.1=bbb; Path=/; HttpOnly; Secure; SameSite=Lax`,
      ],
      [
        "Set-Cookie",
        `${cookieName}.2=; Max-Age=0; Path=/; HttpOnly; Secure; SameSite=Lax`,
      ],
    ],
  });
  clampCookies(chunks, token.absoluteExpiresAt);
  assert.equal(chunks.headers.getSetCookie().length, 3);
  for (const entry of chunks.headers.getSetCookie().slice(0, 2)) {
    assert.match(entry, /HttpOnly; Secure; SameSite=Lax/);
    assert.doesNotMatch(entry, /Max-Age=/);
  }
  assert.match(chunks.headers.getSetCookie()[2], /Max-Age=0/);
});

test("idle deadline bounds renewal and configured origin survives an internal URL rewrite", async () => {
  const token = { ...canonical(), idleExpiresAt: nowSeconds() + 100 };
  const encrypted = await encode({ secret, token, maxAge: 100 });
  const port = {
    ...authority,
    async resolve() {
      return token;
    },
  };
  const response = await bridgeRequest(
    request(`${cookieName}=${encrypted}`),
    "session",
    port,
    secret,
    library,
  );
  assert.equal(response.status, 200);
  assert.deepEqual(await response.json(), {
    expires: new Date(token.idleExpiresAt * 1000).toISOString(),
  });
  const logout = new Request("http://localhost:3000/api/auth/signout", {
    method: "POST",
    headers: {
      origin: "https://shipsense.test",
      "content-type": "application/json",
      cookie: `${cookieName}=${encrypted}`,
      "x-forwarded-host": "attacker.invalid",
    },
  });
  const result = await bridgeRequest(
    logout,
    "signout",
    port,
    secret,
    library,
    "https://shipsense.test",
  );
  assert.equal(result.status, 200);
  assert.deepEqual(await result.json(), { state: "revoked" });
});

test("valid cookie without canonical authority fails closed, including immutable expiry drift", async () => {
  const encrypted = await encode({ secret, token: canonical(), maxAge: 400 });
  for (const port of [
    unavailableAuthority,
    {
      ...authority,
      async resolve() {
        return { ...snapshot(), createdAt: nowSeconds() - 499 };
      },
    },
  ]) {
    const response = await bridgeRequest(
      request(`${cookieName}=${encrypted}`),
      "session",
      port,
      secret,
      library,
    );
    assert.equal(response.status, 503);
    assert.deepEqual(await response.json(), { state: "unavailable" });
    assert.equal(response.headers.getSetCookie().length, 9);
    assert.ok(
      response.headers
        .getSetCookie()
        .every((entry) => entry.includes("Max-Age=0")),
    );
  }
});

test("signout confirms canonical revoke first, clears cookies on failure and rejects cross-origin requests", async () => {
  const encrypted = await encode({ secret, token: canonical(), maxAge: 400 });
  const logout = (origin = "https://shipsense.test") =>
    new Request("https://shipsense.test/api/auth/signout", {
      method: "POST",
      headers: {
        origin,
        "content-type": "application/json",
        cookie: `${cookieName}=${encrypted}`,
      },
    });
  for (const [port, state, status] of [
    [authority, "revoked", 200],
    [unavailableAuthority, "revocation_unconfirmed", 503],
  ] as const) {
    const response = await bridgeRequest(
      logout(),
      "signout",
      port,
      secret,
      library,
    );
    assert.equal(response.status, status);
    assert.deepEqual(await response.json(), { state });
    assert.equal(response.headers.getSetCookie().length, 9);
  }
  assert.equal(
    (
      await bridgeRequest(
        logout("https://attacker.invalid"),
        "signout",
        authority,
        secret,
        library,
      )
    ).status,
    403,
  );
  assert.equal(
    (await bridgeRequest(request(), "signout", authority, secret, library))
      .status,
    503,
  );
  assert.equal(
    (await bridgeRequest(request(), "signin", authority, secret, library))
      .status,
    503,
  );
});

test("server transport authenticates only auth operations, rejects redirects, outages and leaked fields", async () => {
  const { privateKey } = generateKeyPairSync("rsa", { modulusLength: 2048 });
  const key = {
    kid: "active",
    privatePem: privateKey.export({ format: "pem", type: "pkcs8" }).toString(),
    status: "active" as const,
    notBefore: nowSeconds() - 1,
    notAfter: nowSeconds() + 1000,
  };
  const credential = serviceCredential(key, "session:resolve");
  assert.equal(
    JSON.parse(Buffer.from(credential.split(".")[0], "base64url").toString())
      .alg,
    "RS256",
  );
  assert.throws(() =>
    serviceCredential({ ...key, status: "retired" }, "session:resolve"),
  );
  const port = apiSessionAuthority(
    "http://127.0.0.1:8000",
    key,
    async (input, init) => {
      assert.equal(
        input,
        "http://127.0.0.1:8000/internal/v1/auth/session/resolve",
      );
      assert.equal(init?.redirect, "error");
      assert.equal(init?.cache, "no-store");
      assert.ok(
        new Headers(init?.headers).get("authorization")?.startsWith("Bearer "),
      );
      return Response.json(snapshot(), { headers: { "X-Request-ID": "test" } });
    },
  );
  await port.resolve(handle, "test");
  for (const response of [
    Response.json(
      { ...snapshot(), providerToken: "private" },
      { headers: { "X-Request-ID": "test" } },
    ),
    Response.json(snapshot()),
    Response.json({}, { status: 503 }),
  ]) {
    const broken = apiSessionAuthority(
      "http://127.0.0.1:8000",
      key,
      async () => response,
    );
    await assert.rejects(
      broken.resolve(handle, "test"),
      /AUTHORITY_UNAVAILABLE/,
    );
    await assert.rejects(broken.revoke(handle, "test"));
  }
  assert.throws(() => apiSessionAuthority("https://attacker.invalid", key));
});
