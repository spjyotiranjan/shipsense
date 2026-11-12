import { SessionControls } from "../../components/session-controls";
import Link from "next/link";

export default function SignInPage() {
  return (
    <main id="main-content" className="shell sign-in" tabIndex={-1}>
      <h1>Sign in to ShipSense</h1>
      <p role="status">Sign-in is currently unavailable.</p>
      <p>
        Google, GitHub and email sign-in will be available after secure account
        and session setup is complete. No account access is available yet.
      </p>
      <Link href="/">Return to ShipSense</Link>
      <SessionControls />
    </main>
  );
}
