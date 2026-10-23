import { execFileSync } from 'node:child_process';

const paths = execFileSync('git', ['diff', '--cached', '--name-only', '--diff-filter=ACM', '-z', '--', '*.md']);
const files = paths.toString('utf8').split('\0').filter(Boolean);
let failures = 0;

for (const file of files) {
  const content = execFileSync('git', ['show', `:${file}`]).toString('utf8');
  const lines = content.split(/\r?\n/);
  for (let index = 0; index < lines.length; index += 1) {
    if (/[\t ]+$/.test(lines[index])) {
      console.error(`${file}:${index + 1}: trailing whitespace`);
      failures += 1;
    }
  }
  if (content.length > 0 && !content.endsWith('\n')) {
    console.error(`${file}: missing final newline`);
    failures += 1;
  }
}

if (failures > 0) process.exitCode = 1;
else console.log(`Markdown lint passed (${files.length} staged file(s)).`);
