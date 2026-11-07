const boundaries = [
  { name: "Web", responsibility: "Presentation and the web-facing backend layer." },
  { name: "API", responsibility: "Canonical contracts, permissions and domain behavior." },
  { name: "Worker", responsibility: "Background processing and verification jobs." },
] as const;

export default function FoundationPage() {
  return (
    <div className="shell">
      <header className="site-header">
        <a className="brand" href="#main-content" aria-label="ShipSense, main content">ShipSense</a>
        <span className="mode-label">Local development</span>
      </header>
      <main id="main-content" tabIndex={-1}>
        <h1>Developer foundation</h1>
        <p className="intro">A starting point for connecting delivery evidence, investigating failures and reviewing governed proposals.</p>

        <section className="foundation-state" aria-labelledby="foundation-heading">
          <h2 id="foundation-heading">The web foundation is in place</h2>
          <p>This is a static local shell. No service, provider or customer data is connected.</p>
          <dl>
            <div><dt>API connection</dt><dd>Not connected in this slice</dd></div>
            <div><dt>Service health</dt><dd>Not evaluated</dd></div>
          </dl>
          <p className="supporting">A successful build or deployment does not establish recovered service health.</p>
        </section>

        <section className="boundaries" aria-labelledby="boundaries-heading">
          <h2 id="boundaries-heading">Application boundaries</h2>
          <ul className="boundary-list">
            {boundaries.map(({ name, responsibility }) => (
              <li key={name}><h3>{name}</h3><p>{responsibility}</p></li>
            ))}
          </ul>
        </section>

        <section className="next-step" aria-labelledby="next-heading">
          <h2 id="next-heading">Next: verify the API connection</h2>
          <p>The health and version integration follows in SCRUM-16. Connection checks and retry controls will appear when that integration is available.</p>
        </section>
      </main>
      <footer className="site-footer">ShipSense · Developer foundation · No production actions</footer>
    </div>
  );
}
