import { decode, encode, type JWT } from "next-auth/jwt";
import type { NextAuthOptions } from "next-auth";

export type Snapshot = {
  createdAt: number;
  lastActivityAt: number;
  absoluteExpiresAt: number;
  idleExpiresAt: number;
};
export interface SessionAuthority {
  resolve(handle: string, correlationId: string): Promise<Snapshot>;
  revoke(handle: string, correlationId: string): Promise<void>;
}

export const unavailableAuthority: SessionAuthority = {
  async resolve() {
    throw new Error("AUTHORITY_UNAVAILABLE");
  },
  async revoke() {
    throw new Error("AUTHORITY_UNAVAILABLE");
  },
};

export const cookieName = "__Host-shipsense.session-token";
const cookiePattern = /^__Host-shipsense\.session-token(?:\.([0-7]))?$/;
export const nowSeconds = () => Math.floor(Date.now() / 1000);

export function deadline(value: Snapshot, now = nowSeconds()): number {
  const fields = [
    "createdAt",
    "lastActivityAt",
    "absoluteExpiresAt",
    "idleExpiresAt",
  ] as const;
  if (
    fields.some(
      (name) => !Number.isSafeInteger(value[name]) || value[name] < 0,
    ) ||
    value.createdAt > value.lastActivityAt ||
    value.lastActivityAt > now ||
    value.absoluteExpiresAt <= value.createdAt ||
    value.absoluteExpiresAt > value.createdAt + 900 ||
    value.idleExpiresAt <= value.lastActivityAt ||
    value.idleExpiresAt > value.lastActivityAt + 600
  )
    throw new Error("SESSION_DENIED");
  const expires = Math.min(value.absoluteExpiresAt, value.idleExpiresAt);
  if (expires <= now) throw new Error("SESSION_DENIED");
  return expires;
}

// Strict cookie extraction avoids NextAuth getToken's bearer fallback and its
// prefix matching of arbitrary cookie names. Reject duplicate/mixed/gapped chunks.
export function sessionCookies(request: Request): Map<string, string> {
  const raw = request.headers.get("cookie") ?? "";
  if (raw.length > 32768) throw new Error("SESSION_DENIED");
  const result = new Map<string, string>();
  for (const entry of raw.split(";")) {
    const index = entry.indexOf("=");
    if (index < 0) continue;
    const name = entry.slice(0, index).trim();
    if (!name.startsWith(cookieName)) continue;
    const value = entry.slice(index + 1).trim();
    if (
      !cookiePattern.test(name) ||
      result.has(name) ||
      !/^[A-Za-z0-9_.-]+$/.test(value)
    )
      throw new Error("SESSION_DENIED");
    result.set(name, value);
  }
  if (result.has(cookieName) && result.size !== 1)
    throw new Error("SESSION_DENIED");
  if (!result.has(cookieName))
    for (let i = 0; i < result.size; i++)
      if (!result.has(`${cookieName}.${i}`)) throw new Error("SESSION_DENIED");
  return result;
}

function snapshot(token: JWT): Snapshot {
  // Runtime validation is deliberate: encrypted input still crosses a boundary.
  return {
    createdAt: token.createdAt as number,
    lastActivityAt: token.lastActivityAt as number,
    absoluteExpiresAt: token.absoluteExpiresAt as number,
    idleExpiresAt: token.idleExpiresAt as number,
  };
}

export async function cookieToken(
  request: Request,
  secret: string,
): Promise<JWT | null> {
  const cookies = sessionCookies(request);
  const token = [...cookies.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([, value]) => value)
    .join("");
  if (!token) return null;
  const decoded = await decode({ token, secret });
  if (
    !decoded ||
    typeof decoded.exp !== "number" ||
    !Number.isSafeInteger(decoded.exp) ||
    decoded.exp! <= nowSeconds() ||
    typeof decoded.handle !== "string" ||
    !/^[A-Za-z0-9_-]{43}$/.test(decoded.handle)
  )
    throw new Error("SESSION_DENIED");
  deadline(snapshot(decoded));
  return decoded;
}

export function bridgeOptions(secret: string, canonical: JWT): NextAuthOptions {
  return {
    secret,
    providers: [],
    session: { strategy: "jwt", maxAge: 900 },
    cookies: {
      sessionToken: {
        name: cookieName,
        options: { httpOnly: true, secure: true, sameSite: "lax", path: "/" },
      },
    },
    jwt: {
      async encode(params) {
        const token = params.token;
        if (!token) throw new Error("SESSION_DENIED");
        const expires = deadline(snapshot(token));
        // Encryption and authenticated decoding remain pinned-library managed.
        const encrypted = await encode({
          ...params,
          maxAge: expires - nowSeconds(),
        });
        const checked = await decode({ ...params, token: encrypted });
        if (
          !checked ||
          typeof checked.exp !== "number" ||
          !Number.isSafeInteger(checked.exp) ||
          checked.exp! > expires ||
          checked.exp! <= nowSeconds()
        )
          throw new Error("SESSION_DENIED");
        return encrypted;
      },
      async decode(params) {
        const token = await decode(params);
        if (!token) return null;
        if (
          typeof token.exp !== "number" ||
          !Number.isSafeInteger(token.exp) ||
          token.exp <= nowSeconds()
        )
          throw new Error("SESSION_DENIED");
        deadline(snapshot(token));
        return token;
      },
    },
    callbacks: {
      async signIn() {
        return false;
      },
      async jwt() {
        return canonical;
      },
      async session() {
        return {
          expires: new Date(deadline(snapshot(canonical)) * 1000).toISOString(),
        };
      },
    },
    logger: { error() {}, warn() {}, debug() {} },
    debug: false,
  };
}

export function clearSessionCookies(
  request: Request,
  response: Response,
): void {
  // Delete all bounded known chunk names even when malformed input cannot parse.
  // Preserve __Host attributes; no Domain attribute is ever emitted.
  void request;
  for (const name of [
    cookieName,
    ...Array.from({ length: 8 }, (_, i) => `${cookieName}.${i}`),
  ])
    response.headers.append(
      "Set-Cookie",
      `${name}=; Path=/; Max-Age=0; HttpOnly; Secure; SameSite=Lax`,
    );
}

export function clampCookies(response: Response, expires: number): void {
  const cookies = response.headers.getSetCookie();
  response.headers.delete("Set-Cookie");
  for (const cookie of cookies) {
    const name = cookie.slice(0, cookie.indexOf("="));
    if (!cookiePattern.test(name) || /;\s*Max-Age=0(?:;|$)/i.test(cookie)) {
      response.headers.append("Set-Cookie", cookie);
      continue;
    }
    const attributes = cookie
      .replace(/;\s*Expires=[^;]*/gi, "")
      .replace(/;\s*Max-Age=[^;]*/gi, "");
    response.headers.append(
      "Set-Cookie",
      `${attributes}; Expires=${new Date(expires * 1000).toUTCString()}`,
    );
  }
}

type LibraryHandler = (
  request: Request,
  options: NextAuthOptions,
) => Promise<Response>;

export async function bridgeRequest(
  request: Request,
  action: string,
  authority: SessionAuthority,
  secret: string | undefined,
  library: LibraryHandler,
  expectedOrigin = new URL(request.url).origin,
): Promise<Response> {
  const correlation = crypto.randomUUID();
  function reply(state: string, status: number): Response {
    return Response.json(
      { state },
      {
        status,
        headers: { "Cache-Control": "no-store", "X-Request-ID": correlation },
      },
    );
  }
  const signout = action === "signout" && request.method === "POST";
  if (
    signout &&
    (request.headers.get("origin") !== expectedOrigin ||
      request.headers.get("content-type") !== "application/json")
  )
    return reply("denied", 403);
  if (!signout && !(action === "session" && request.method === "GET"))
    return reply("unavailable", 503);
  let token: JWT | null;
  try {
    if (!secret || secret.length < 32) throw new Error();
    token = await cookieToken(request, secret);
  } catch {
    const response = reply(
      signout ? "revocation_unconfirmed" : "unavailable",
      503,
    );
    clearSessionCookies(request, response);
    return response;
  }
  if (signout) {
    let confirmed = false;
    try {
      if (token) {
        await authority.revoke(token.handle as string, correlation);
        confirmed = true;
      }
    } catch {
      /* Cookie deletion is not durable revocation confirmation. */
    }
    const response = reply(
      confirmed ? "revoked" : "revocation_unconfirmed",
      confirmed ? 200 : 503,
    );
    clearSessionCookies(request, response);
    return response;
  }
  if (!token) return reply("signed_out", 200);
  try {
    const canonical = await authority.resolve(
      token.handle as string,
      correlation,
    );
    deadline(canonical);
    // Creation/absolute expiry are immutable; an old cookie cannot acquire a
    // fresh lifetime, even if a broken authority returns a different session.
    if (
      canonical.createdAt !== token.createdAt ||
      canonical.absoluteExpiresAt !== token.absoluteExpiresAt
    )
      throw new Error();
    const expires = Math.min(deadline(canonical), deadline(snapshot(token)));
    const bounded = {
      handle: token.handle,
      ...canonical,
      idleExpiresAt: expires,
    };
    const headers = new Headers(request.headers);
    headers.delete("authorization");
    const sanitized = new Request(request, { headers });
    const response = await library(sanitized, bridgeOptions(secret!, bounded));
    if (!response.ok) throw new Error();
    const body: unknown = await response.clone().json();
    if (
      !body ||
      typeof body !== "object" ||
      Object.keys(body).join(",") !== "expires" ||
      (body as { expires: unknown }).expires !==
        new Date(expires * 1000).toISOString()
    )
      throw new Error();
    clampCookies(response, expires);
    response.headers.set("Cache-Control", "no-store");
    response.headers.set("X-Request-ID", correlation);
    return response;
  } catch {
    const response = reply("unavailable", 503);
    clearSessionCookies(request, response);
    return response;
  }
}
