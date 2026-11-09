import assert from "node:assert/strict";
import { test } from "node:test";
import { isVersion, readBoundedJson } from "../src/lib/diagnostic-contract.ts";
import { requestVersion } from "../src/lib/server/api-transport.ts";
import {
  createConnectionCheck,
  type ConnectionState,
} from "../src/lib/connection-check.ts";

const version = () => ({
  service: "shipsense-api",
  version: "0.1.0-dev",
  apiVersion: "v1",
  observedAt: new Date().toISOString(),
});
const json = (body: unknown, status = 200) => Response.json(body, { status });
const upstream: typeof fetch = async (_input, init) =>
  Response.json(version(), {
    headers: {
      "X-Request-ID": new Headers(init?.headers).get("x-request-id")!,
    },
  });

test("version guard rejects wrong shape, bounds, dates and stale evidence", () => {
  assert.ok(isVersion(version()));
  for (const value of [
    null,
    [],
    {},
    { ...version(), extra: true },
    { ...version(), service: "other" },
    { ...version(), apiVersion: "v2" },
    { ...version(), version: "x".repeat(65) },
    { ...version(), version: "<html>" },
    { ...version(), observedAt: "2026-02-30T00:00:00Z" },
    { ...version(), observedAt: new Date(Date.now() - 61_000).toISOString() },
    { ...version(), observedAt: new Date(Date.now() + 6_000).toISOString() },
  ])
    assert.equal(isVersion(value), false);
});

test("bounded JSON rejects invalid content, declared and streamed oversize", async () => {
  for (const response of [
    new Response("<html>"),
    new Response("{}", {
      headers: { "content-type": "application/json", "content-length": "4097" },
    }),
    json("x".repeat(4097)),
    new Response("bad", { headers: { "content-type": "application/json" } }),
  ])
    await assert.rejects(readBoundedJson(response));
});

test("transport fixes destination, correlation, no-store and redirect behavior", async () => {
  let calls = 0;
  const fetcher: typeof fetch = async (input, init) => {
    calls++;
    assert.equal(input, "http://127.0.0.1:8000/api/v1/version");
    assert.equal(init?.cache, "no-store");
    assert.equal(init?.redirect, "error");
    assert.deepEqual([...new Headers(init?.headers).keys()].sort(), [
      "accept",
      "x-request-id",
    ]);
    return upstream(input, init);
  };
  const response = await requestVersion(
    "http://127.0.0.1:8000",
    new AbortController().signal,
    fetcher,
  );
  assert.equal(response.status, 200);
  assert.ok(isVersion(await response.json()));
  assert.equal(response.headers.get("cache-control"), "no-store");
  for (const origin of [
    undefined,
    "https://example.com",
    "http://127.0.0.1:8000/private",
    "ftp://localhost:8000",
  ])
    assert.equal(
      (await requestVersion(origin, new AbortController().signal, fetcher))
        .status,
      502,
    );
  assert.equal(calls, 1);
});

test("network, non-2xx and malformed responses are safe failures", async () => {
  for (const fetcher of [
    async () => {
      throw new Error("private-upstream");
    },
    async () => json({ private: "private-upstream" }, 403),
    async () => json(null),
    async () => json(version()),
    async () => new Response("private-upstream"),
  ]) {
    const result = await requestVersion(
      "http://localhost:8000",
      new AbortController().signal,
      fetcher,
    );
    assert.equal(result.status, 502);
    assert.equal(result.headers.get("cache-control"), "no-store");
    const body = await result.text();
    assert.ok(!body.includes("private-upstream"));
    assert.ok(body.includes(result.headers.get("x-request-id")!));
  }
});

test("five-second deadline aborts upstream and deliberate cancellation stays cancellation", async () => {
  const fetcher: typeof fetch = async (_input, init) =>
    new Promise((_resolve, reject) => {
      init!.signal!.addEventListener(
        "abort",
        () => reject(init!.signal!.reason),
        { once: true },
      );
    });
  // Keep Node alive while AbortSignal.timeout's unreferenced timer runs.
  const keepAlive = setInterval(() => {}, 1000);
  try {
    const start = performance.now();
    const result = await requestVersion(
      "http://localhost:8000",
      new AbortController().signal,
      fetcher,
    );
    assert.equal(result.status, 504);
    assert.equal((await result.json()).error.code, "API_TIMEOUT");
    assert.ok(
      performance.now() - start >= 4900 && performance.now() - start < 7000,
    );
    const controller = new AbortController();
    const pending = requestVersion(
      "http://localhost:8000",
      controller.signal,
      fetcher,
    );
    controller.abort();
    await assert.rejects(pending);
  } finally {
    clearInterval(keepAlive);
  }
});

test("explicit retry clears success, blocks duplicates and recovers without automatic retries", async () => {
  const states: ConnectionState[] = [];
  let resolve!: (value: Response) => void;
  let calls = 0;
  const check = createConnectionCheck(
    (state) => states.push(state),
    async () => {
      calls++;
      return new Promise((done) => {
        resolve = done;
      });
    },
  );
  const first = check.run();
  await check.run();
  assert.equal(calls, 1);
  assert.deepEqual(states, [{ kind: "loading" }]);
  resolve(json(version()));
  await first;
  assert.equal(states.at(-1)?.kind, "connected");
  const second = check.run();
  assert.deepEqual(states.at(-1), { kind: "loading" });
  resolve(
    json({ error: { code: "API_UNAVAILABLE", message: "private" } }, 502),
  );
  await second;
  assert.equal(states.at(-1)?.kind, "unavailable");
  assert.ok(!JSON.stringify(states).includes("private"));
  const third = check.run();
  resolve(json(version()));
  await third;
  assert.equal(states.at(-1)?.kind, "connected");
  assert.equal(calls, 3);
});

test("cancel/unmount and late success or failure cannot overwrite a newer attempt", async () => {
  for (const lateFailure of [false, true]) {
    const states: ConnectionState[] = [];
    const resolvers: Array<{
      resolve: (value: Response) => void;
      reject: (reason: Error) => void;
    }> = [];
    const check = createConnectionCheck(
      (state) => states.push(state),
      async () =>
        new Promise((resolve, reject) => resolvers.push({ resolve, reject })),
    );
    const first = check.run();
    check.cancel();
    const second = check.run();
    resolvers[1].resolve(json(version()));
    await second;
    const count = states.length;
    if (lateFailure) resolvers[0].reject(new Error("late failure"));
    else resolvers[0].resolve(json(version()));
    await first;
    assert.equal(states.length, count);
    assert.equal(states.at(-1)?.kind, "connected");
    const third = check.run();
    check.cancel();
    const cancelledCount = states.length;
    resolvers[2].resolve(json(version()));
    await third;
    assert.equal(states.length, cancelledCount);
  }
});
