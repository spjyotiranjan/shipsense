import { createElement as element } from "react";
import type { components } from "../../../../packages/contracts/src/generated";

type Project = components["schemas"]["Project"];
type ProjectRow = Pick<Project, "id" | "name" | "status"> & {
  readonly ownerTeamName: string;
};

type TenantProjectsView =
  | { readonly state: "unavailable" }
  | { readonly state: "ready"; readonly projects: readonly ProjectRow[] };

const statusLabels: Record<Project["status"], string> = {
  active: "Active",
  suspended: "Suspended",
  archived: "Archived",
};

/** Presentation only. Ready rows must come from an authorized, tenant-scoped
 * server read. No such runtime read or route is wired by this component. */
export function TenantProjects({ view }: { view: TenantProjectsView }) {
  return element(
    "section",
    { "aria-labelledby": "tenant-projects-heading" },
    element("h2", { id: "tenant-projects-heading" }, "Tenant projects"),
    view.state === "unavailable"
      ? element("p", null, "Project administration is unavailable.")
      : view.projects.length === 0
        ? element("p", null, "No projects in this tenant.")
        : element(
            "table",
            null,
            element("caption", null, "Project ownership and lifecycle"),
            element(
              "thead",
              null,
              element(
                "tr",
                null,
                element("th", { scope: "col" }, "Project"),
                element("th", { scope: "col" }, "Owner team"),
                element("th", { scope: "col" }, "Status"),
              ),
            ),
            element(
              "tbody",
              null,
              view.projects.map((project) =>
                element(
                  "tr",
                  { key: project.id },
                  element("th", { scope: "row" }, project.name),
                  element("td", null, project.ownerTeamName),
                  element("td", null, statusLabels[project.status]),
                ),
              ),
            ),
          ),
  );
}
