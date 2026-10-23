import { readFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';

const messagePath = process.argv[2];
if (!messagePath) {
  console.error('Commit message file is required.');
  process.exitCode = 1;
} else {
  const subject = readFileSync(messagePath, 'utf8').split(/\r?\n/, 1)[0];
  const key = /^SCRUM-[1-9]\d*\b/.exec(subject)?.[0];
  if (!key) {
    console.error('Commit subject must start with a Jira key, for example: SCRUM-14 Add lint hooks');
    process.exitCode = 1;
  } else {
    const branch = execFileSync('git', ['branch', '--show-current'], { encoding: 'utf8' }).trim();
    if (branch !== 'main' && !branch.startsWith(`${key}-`)) {
      console.error(`Commit key ${key} must match the branch key in ${branch || '(detached HEAD)'}.`);
      process.exitCode = 1;
    }
  }
}
