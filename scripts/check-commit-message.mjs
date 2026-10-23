import { readFileSync } from 'node:fs';

const messagePath = process.argv[2];
if (!messagePath) {
  console.error('Commit message file is required.');
  process.exitCode = 1;
} else {
  const subject = readFileSync(messagePath, 'utf8').split(/\r?\n/, 1)[0];
  if (!/^SCRUM-[1-9]\d*\b/.test(subject)) {
    console.error('Commit subject must start with a Jira key, for example: SCRUM-14 Add lint hooks');
    process.exitCode = 1;
  }
}
