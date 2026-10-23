import { execFileSync } from 'node:child_process';
import { jiraKeyFrom } from './jira-key.mjs';

let branch = process.argv[2];
if (!branch) {
  branch = execFileSync('git', ['branch', '--show-current'], { encoding: 'utf8' }).trim();
}

if (branch === 'main') {
  process.exit(0);
}

if (!jiraKeyFrom(branch || '')) {
  console.error(`Invalid branch name: ${branch || '(detached HEAD)'}`);
  console.error('Include a Jira key anywhere in the branch name, for example feature/SCRUM-14-add-quality-hooks.');
  process.exitCode = 1;
}