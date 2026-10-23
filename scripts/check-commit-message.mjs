import { readFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { jiraKeyFrom } from './jira-key.mjs';

const messagePath = process.argv[2];
if (!messagePath) {
  console.error('Commit message file is required.');
  process.exitCode = 1;
} else {
  const message = readFileSync(messagePath, 'utf8');
  const key = jiraKeyFrom(message);
  if (!key) {
    console.error('Commit message must include a Jira key, for example: Add lint hooks for SCRUM-14');
    process.exitCode = 1;
  } else {
    const branch = execFileSync('git', ['branch', '--show-current'], { encoding: 'utf8' }).trim();
    if (branch !== 'main' && jiraKeyFrom(branch) !== key) {
      console.error(`Commit key ${key} must match the branch key in ${branch || '(detached HEAD)'}.`);
      process.exitCode = 1;
    }
  }
}
