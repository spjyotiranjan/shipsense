"use client";

import { useState } from "react";

export function SessionControls() {
  const [pending, setPending] = useState(false);
  const [message, setMessage] = useState("");
  async function signOut() {
    if (pending) return;
    setPending(true);
    setMessage("");
    try {
      const response = await fetch("/api/auth/signout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: "{}",
        cache: "no-store",
        redirect: "error",
        signal: AbortSignal.timeout(5000),
      });
      const value: unknown = await response.json();
      if (
        response.ok &&
        value &&
        typeof value === "object" &&
        "state" in value &&
        value.state === "revoked"
      ) {
        setMessage(
          "Signed out of ShipSense. Your provider account remains separate.",
        );
      } else if (
        response.status === 503 &&
        value &&
        typeof value === "object" &&
        "state" in value &&
        value.state === "revocation_unconfirmed"
      ) {
        setMessage(
          "Browser session cleared. Server sign-out could not be confirmed. Account access remains unavailable.",
        );
      } else {
        setMessage(
          "Sign-out could not be confirmed. Retry clearing this browser session.",
        );
      }
    } catch {
      setMessage(
        "Sign-out could not be confirmed. Retry clearing this browser session.",
      );
    } finally {
      setPending(false);
    }
  }
  return (
    <section
      className="foundation-state"
      aria-labelledby="session-heading"
      aria-busy={pending}
    >
      <h2 id="session-heading">Browser session</h2>
      <button
        className="retry-button"
        type="button"
        onClick={signOut}
        aria-disabled={pending}
      >
        {pending ? "Clearing session…" : "Clear browser session"}
      </button>
      <p role="status" aria-live="polite">
        {message}
      </p>
    </section>
  );
}
