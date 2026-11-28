import assert from "node:assert/strict";
import { test } from "node:test";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { TenantProjects } from "../src/components/tenant-projects.ts";

test("tenant project view distinguishes unavailable access from an authorized empty list", () => {
  const unavailable = renderToStaticMarkup(
    createElement(TenantProjects, { view: { state: "unavailable" } }),
  );
  const empty = renderToStaticMarkup(
    createElement(TenantProjects, { view: { state: "ready", projects: [] } }),
  );
  assert.match(unavailable, /Project administration is unavailable/);
  assert.doesNotMatch(unavailable, /No projects/);
  assert.match(empty, /No projects in this tenant/);
});

test("tenant project view renders ownership and lifecycle without exposing internal IDs or write controls", () => {
  const markup = renderToStaticMarkup(
    createElement(TenantProjects, {
      view: {
        state: "ready",
        projects: [
          {
            id: "synthetic-project-id",
            name: "Checkout <test>",
            ownerTeamName: "Platform",
            status: "archived",
          },
        ],
      },
    }),
  );
  assert.match(markup, /<section aria-labelledby="tenant-projects-heading">/);
  assert.match(markup, /<th scope="col">Owner team<\/th>/);
  assert.match(markup, /<th scope="row">Checkout &lt;test&gt;<\/th>/);
  assert.match(markup, /<td>Platform<\/td><td>Archived<\/td>/);
  assert.doesNotMatch(markup, /synthetic-project-id|<button|<form|<a /);
});
