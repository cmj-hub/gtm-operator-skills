// Keep independently installed Python scorers and the canonical contract in step.
import { readFileSync, readdirSync, copyFileSync } from 'node:fs';
import { resolve, dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const source = join(root, 'scripts/shared/scorer_envelope.py');
const canonical = join(root, 'scripts/shared/result-envelope');
const args = process.argv.slice(2);
const sync = args.includes('--sync');
const upstreamIndex = args.indexOf('--upstream');
if (args.some((arg, i) => !['--sync', '--upstream'].includes(arg) && !(upstreamIndex >= 0 && i === upstreamIndex + 1))
    || (upstreamIndex >= 0 && !args[upstreamIndex + 1])) {
  throw new Error('Usage: node scripts/check-shared.mjs [--sync] [--upstream <packages repo>]');
}
const failures = [];
let copies = 0;
function visit(directory) {
  for (const entry of readdirSync(directory, { withFileTypes: true })) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) visit(path);
    else if (entry.name === 'scorer_envelope.py') {
      copies++;
      if (sync) copyFileSync(source, path);
      if (!readFileSync(path).equals(readFileSync(source))) failures.push(path);
    }
  }
}
visit(join(root, 'skills'));
if (copies !== 19) failures.push(`expected 19 installed adapter copies, found ${copies}`);
const pin = JSON.parse(readFileSync(join(canonical, 'pin.json'), 'utf8'));
for (const [name, digest] of Object.entries(pin.files)) {
  const bytes = readFileSync(join(canonical, name));
  if (createHash('sha256').update(bytes).digest('hex') !== digest) failures.push(`canonical ${name} differs from pin`);
  if (upstreamIndex >= 0) {
    const upstream = resolve(args[upstreamIndex + 1], 'packages/result-envelope/src', name);
    if (!bytes.equals(readFileSync(upstream))) failures.push(`canonical ${name} differs from upstream; vendor sync required`);
  }
}
if (failures.length) {
  console.error(failures.join('\n'));
  process.exitCode = 1;
} else console.log(`${copies} installed adapters match; canonical files match ${pin.commit}.`);
