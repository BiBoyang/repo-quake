import { appendFile, readFile, writeFile } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import { settleStagedTraces } from './node_modules/e2e/dist/cache/context.js';

const APP = dirname(fileURLToPath(import.meta.url));
const ROOT = dirname(dirname(APP));
const RESULTS = join(ROOT, 'results');
const LEDGER = join(ROOT, 'execution-ledger.jsonl');
const cells = [
  { id: 'C0', behavior: 'saved', expected: 'saved' },
  { id: 'C1', behavior: 'undefined', expected: 'not-written' },
  { id: 'T1', behavior: 'throw', expected: 'not-written' },
];
const hash = (bytes) => createHash('sha256').update(bytes).digest('hex');
async function readJson(path) { return JSON.parse(await readFile(path, 'utf8')); }
try { await readFile(LEDGER); throw new Error('execution ledger exists; retries forbidden'); }
catch (error) { if (error.code !== 'ENOENT') throw error; }
const card = await readJson(join(ROOT, 'experiment-card.json'));
if (card.budget.max_runs !== cells.length || card.arms.map((arm) => arm.id).join(',') !== cells.map((cell) => cell.id).join(',')) throw new Error('card/cell mismatch');
if (hash(await readFile(join(APP, 'package-lock.json'))) !== card.target.source_sha256) throw new Error('target pin changed');
if (hash(await readFile(join(ROOT, 'task-contract.txt'))) !== card.task.prompt_sha256) throw new Error('task contract changed');
const manifest = await readJson(join(ROOT, 'fixture-manifest.json'));
for (const [path, expected] of Object.entries(manifest.files)) {
  if (hash(await readFile(join(ROOT, path))) !== expected) throw new Error(`fixture changed: ${path}`);
}
for (const cell of cells) {
  await appendFile(LEDGER, JSON.stringify({ id: cell.id, at: new Date().toISOString() }) + '\n');
  const calls = [];
  const context = {
    mode: 'read-write',
    store: {
      async read(keyHash) { calls.push({ op: 'read', keyHash }); return { status: 'miss' }; },
      async write(keyHash, payload) {
        calls.push({ op: 'write', keyHash, behavior: cell.behavior, payload });
        if (cell.behavior === 'throw') throw new Error('EACCES: deterministic write fault');
        return cell.behavior === 'saved' ? { bytes: 128 } : undefined;
      },
    },
    staged: [{
      kind: 'write', keyHash: 'a'.repeat(64), stepIndex: 0,
      trace: { actions: [], executor: { name: 'contract-probe', version: '1.0.0' }, summary: 'verified', startPath: '/' },
    }],
  };
  let thrown = null;
  let outcomes;
  try {
    outcomes = await settleStagedTraces(context, { lastVerifiedStepIndex: 1, implicatesUnconfirmed: true });
  } catch (error) { thrown = String(error); }
  const actual = outcomes?.get(0) ?? null;
  const result = {
    id: cell.id, behavior: cell.behavior, expected: cell.expected, actual,
    contained: thrown === null, matchesPreregisteredExpectation: thrown === null && actual === cell.expected,
    calls, stagedAfter: context.staged.length,
  };
  await writeFile(join(RESULTS, `${cell.id}.json`), JSON.stringify(result, null, 2) + '\n');
  if ((cell.id === 'C0' || cell.id === 'C1') && !result.matchesPreregisteredExpectation) throw new Error(`${cell.id} control failed; matrix stopped`);
}
const results = [];
for (const cell of cells) results.push(await readJson(join(RESULTS, `${cell.id}.json`)));
await writeFile(join(RESULTS, 'matrix.json'), JSON.stringify(results, null, 2) + '\n');
console.log(JSON.stringify(results.map(({ id, expected, actual, contained, matchesPreregisteredExpectation }) => ({ id, expected, actual, contained, matchesPreregisteredExpectation })), null, 2));
