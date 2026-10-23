const jiraKeyPattern = /(?:^|[^A-Za-z0-9])(SCRUM-[1-9]\d*)(?![A-Za-z0-9])/;

export function jiraKeyFrom(text) {
  return jiraKeyPattern.exec(text)?.[1] ?? null;
}
