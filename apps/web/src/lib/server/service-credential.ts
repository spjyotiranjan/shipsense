import { createPrivateKey, randomUUID, sign } from "node:crypto";

export type AuthScope = "session:resolve" | "session:revoke";
export type SigningKey = {
  kid: string;
  privatePem: string;
  status: "active" | "retired";
  notBefore: number;
  notAfter: number;
};

// Called only by the server transport, never exported through a browser DTO.
// Deployment custody is Azure secret management; there is no environment-based
// enablement or fallback development key in this bounded slice.
export function serviceCredential(
  key: SigningKey,
  scope: AuthScope,
  now = Math.floor(Date.now() / 1000),
): string {
  if (
    !["session:resolve", "session:revoke"].includes(scope) ||
    !Number.isSafeInteger(now) ||
    !Number.isSafeInteger(key.notBefore) ||
    !Number.isSafeInteger(key.notAfter) ||
    key.status !== "active" ||
    !/^[A-Za-z0-9_-]{1,64}$/.test(key.kid) ||
    key.notBefore > now ||
    key.notAfter < now + 60
  )
    throw new Error("SERVICE_CREDENTIAL_UNAVAILABLE");
  try {
    const privateKey = createPrivateKey(key.privatePem);
    if (
      privateKey.asymmetricKeyType !== "rsa" ||
      (privateKey.asymmetricKeyDetails?.modulusLength ?? 0) < 2048
    )
      throw new Error();
    const header = { alg: "RS256", typ: "JWT", kid: key.kid };
    const claims = {
      iss: "shipsense-web",
      aud: "shipsense-auth",
      sub: "shipsense-bff",
      scope,
      iat: now,
      nbf: now,
      exp: now + 60,
      jti: randomUUID(),
    };
    const input = [header, claims]
      .map((value) => Buffer.from(JSON.stringify(value)).toString("base64url"))
      .join(".");
    return `${input}.${sign("RSA-SHA256", Buffer.from(input), privateKey).toString("base64url")}`;
  } catch {
    throw new Error("SERVICE_CREDENTIAL_UNAVAILABLE");
  }
}
