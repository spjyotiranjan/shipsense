import NextAuth from "next-auth";
import { NextRequest } from "next/server";
import {
  bridgeRequest,
  unavailableAuthority,
} from "../../../../lib/server/session-bridge";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

type Context = { params: Promise<{ nextauth: string[] }> };

async function handler(request: NextRequest, context: Context) {
  const { nextauth } = await context.params;
  const action = nextauth.length === 1 ? nextauth[0] : "unavailable";
  return bridgeRequest(
    request,
    action,
    unavailableAuthority,
    process.env.NEXTAUTH_SECRET,
    async (sanitized, options) =>
      NextAuth(options)(new NextRequest(sanitized), context),
    process.env.NEXTAUTH_URL ?? "http://127.0.0.1:3000",
  );
}

export { handler as GET, handler as POST };
