import { execFileSync } from 'node:child_process';

let branch = process.argv[2];
if (!branch) {
  branch = execFileSync('git', ['branch', '--show-current'], { encoding: 'utf8' }).trim();
}

if (branch === 'main') {
  process.exit(0);
}

if (!/^SCRUM-[1-9]\d*-[a-z0-9]+(?:-[a-z0-9]+)*$/.test(branch || '')) {
  console.error(`Invalid branch name: ${branch || '(detached HEAD)'}`);
  console.error('Use SCRUM-<issue number>-<lowercase-description>, for example SCRUM-14-add-quality-hooks.');
  process.exitCode = 1;
}
