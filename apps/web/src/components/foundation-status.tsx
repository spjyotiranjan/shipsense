"use client";

import { useEffect, useState } from "react";
import {
  createConnectionCheck,
  type ConnectionState,
} from "../lib/connection-check";

export function FoundationStatus() {
  const [state, setState] = useState<ConnectionState>({ kind: "idle" });
  const [check] = useState(() => createConnectionCheck(setState));
  useEffect(() => {
    void check.run();
    return () => check.cancel();
  }, [check]);
  const pending = state.kind === "loading";
  return (
    <section className="foundation-state" aria-labelledby="foundation-heading">
      <h2 id="foundation-heading">API connection</h2>
      <p>Local development · Synthetic data only</p>
      <p className="connection-status" role="status" aria-atomic="true">
        {state.kind === "idle"
          ? "Connection not checked."
          : pending
            ? "Checking…"
            : state.kind === "connected"
              ? "Connected"
              : state.message}
      </p>
      {state.kind === "connected" && (
        <dl>
          <div>
            <dt>API version</dt>
            <dd>{state.version.version}</dd>
          </div>
          <div>
            <dt>Last checked</dt>
            <dd>
              <time dateTime={state.version.observedAt}>
                {new Date(state.version.observedAt).toLocaleString()}
              </time>
            </dd>
          </div>
        </dl>
      )}
      {state.kind === "unavailable" && state.requestId && (
        <p className="request-reference">
          Request reference: <span>{state.requestId}</span>
        </p>
      )}
      <button
        className="retry-button"
        type="button"
        aria-disabled={pending}
        onClick={() => {
          void check.run();
        }}
      >
        Retry connection
      </button>
      <noscript>
        <p>JavaScript is unavailable. Enable it to check the API connection.</p>
      </noscript>
      <p className="supporting">
        This checks API reachability only. Service readiness and customer health
        are not evaluated. A successful build or deployment does not establish
        recovered service health.
      </p>
    </section>
  );
}
