import { FoundationStatus } from "../components/foundation-status";

const boundaries = [
  {
    name: "Web",
    responsibility: "Presentation and the web-facing backend layer.",
  },
  {
    name: "API",
    responsibility: "Canonical contracts, permissions and domain behavior.",
  },
  {
    name: "Worker",
    responsibility: "Background processing and verification jobs.",
  },
] as const;

export default function FoundationPage() {
  return (
    <div className="shell">
      <header className="site-header">
        <a
          className="brand"
          href="#main-content"
          aria-label="ShipSense, main content"
        >
          ShipSense
        </a>
        <span className="mode-label">Local development</span>
      </header>
      <main id="main-content" tabIndex={-1}>
        <h1>Developer foundation</h1>
        <p className="intro">
          A starting point for connecting delivery evidence, investigating
          failures and reviewing governed proposals.
        </p>

        <FoundationStatus />
        <p>
          <a href="/sign-in">Sign in</a>
        </p>

        <section className="boundaries" aria-labelledby="boundaries-heading">
          <h2 id="boundaries-heading">Application boundaries</h2>
          <ul className="boundary-list">
            {boundaries.map(({ name, responsibility }) => (
              <li key={name}>
                <h3>{name}</h3>
                <p>{responsibility}</p>
              </li>
            ))}
          </ul>
        </section>
      </main>
      <footer className="site-footer">
        ShipSense · Developer foundation · No production actions
      </footer>
    </div>
  );
}
