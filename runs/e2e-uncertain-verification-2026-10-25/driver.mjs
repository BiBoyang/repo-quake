import { spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import { createWriteStream } from 'node:fs';
import {
  appendFile, cp, mkdir, readFile, readdir, rm, stat, writeFile,
} from 'node:fs/promises';
import { dirname, join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = dirname(fileURLToPath(import.meta.url));
const APP = join(ROOT, 'fixtures', 'app');
const RESULTS = join(ROOT, 'results');
const RUNTIME = join(ROOT, 'runtime');
const SEED = join(RUNTIME, 'cache-seed');
const LEDGER = join(ROOT, 'execution-ledger.jsonl');
const MAX_CELL_MS = 90_000;
const cells = [
  { id: 'U1', item: 'Uncertain 007', alias: 'ordinary', copySeed: true, uncertainTap: true },
  { id: 'N1', item: 'Negative 008', alias: 'ordinary', copySeed: true },
];

function sha256(bytes) { return createHash('sha256').update(bytes).digest('hex'); }
async function fileHash(path) { return sha256(await readFile(path)); }
async function exists(path) { try { await stat(path); return true; } catch { return false; } }
async function json(path) { return JSON.parse(await readFile(path, 'utf8')); }
async function writeJson(path, value) { await writeFile(path, JSON.stringify(value, null, 2) + '\n', 'utf8'); }
async function sleep(ms) { return new Promise((resolveSleep) => setTimeout(resolveSleep, ms)); }

async function verifyFrozenInputs() {
  const card = await json(join(ROOT, 'experiment-card.json'));
  if (card.budget.max_runs !== cells.length) throw new Error('cell count differs from frozen budget');
  const cardIds = card.arms.map((arm) => arm.id).join(',');
  if (cardIds !== cells.map((cell) => cell.id).join(',')) throw new Error('cell order differs from frozen card');
  if (await fileHash(join(APP, 'package-lock.json')) !== card.target.source_sha256) throw new Error('target pin hash changed');
  if (await fileHash(join(ROOT, 'task-contract.txt')) !== card.task.prompt_sha256) throw new Error('task contract hash changed');
  const manifest = await json(join(ROOT, 'fixture-manifest.json'));
  for (const [path, expected] of Object.entries(manifest.files)) {
    if (await fileHash(join(ROOT, path)) !== expected) throw new Error(`fixture changed after freeze: ${path}`);
  }
  if (await exists(LEDGER)) throw new Error('execution ledger already exists; retries are forbidden under this card');
}

async function cacheManifest(directory) {
  const out = {};
  if (!await exists(directory)) return out;
  const names = (await readdir(directory)).filter((name) => name.endsWith('.json')).sort();
  for (const name of names) out[name] = await fileHash(join(directory, name));
  return out;
}
function agentStep(report) {
  return report?.run?.results?.flatMap((result) => result.attempts ?? [])
    .flatMap((attempt) => attempt.steps ?? []).find((step) => step.kind === 'agent');
}
async function baselineIsValid(cell, cacheAfter) {
  if (!await exists(join(RESULTS, `${cell.id}.report.json`))) return false;
  const report = await json(join(RESULTS, `${cell.id}.report.json`));
  const events = await json(join(RESULTS, `${cell.id}.events.json`));
  const dom = await json(join(RESULTS, `${cell.id}.dom.json`));
  const calls = (await readFile(join(RESULTS, `${cell.id}.executor.jsonl`), 'utf8'))
    .trim().split('\n').filter(Boolean).map(JSON.parse).filter((event) => event.kind === 'call');
  return report.run.summary.passed === 1 && report.run.summary.failed === 0
    && events.filter((event) => event.type === 'save-committed' && event.item === cell.item).length === 1
    && dom.status === `Saved ${cell.item}` && dom.input === cell.item
    && calls.length === 1 && Object.keys(cacheAfter).length === 1
    && agentStep(report)?.cache?.write === 'saved';
}

async function waitFor(url, attempts = 100) {
  let last;
  for (let index = 0; index < attempts; index += 1) {
    try { const response = await fetch(url); if (response.ok) return; last = new Error(String(response.status)); }
    catch (error) { last = error; }
    await sleep(100);
  }
  throw new Error(`service did not become ready: ${url}: ${last}`);
}
async function stopChild(child) {
  if (!child || child.exitCode !== null || child.signalCode !== null) return;
  child.kill('SIGTERM');
  for (let index = 0; index < 30 && child.exitCode === null && child.signalCode === null; index += 1) await sleep(100);
  if (child.exitCode === null && child.signalCode === null) child.kill('SIGKILL');
}
async function execute(cell) {
  await appendFile(LEDGER, JSON.stringify({ id: cell.id, at: new Date().toISOString() }) + '\n', 'utf8');
  await fetch('http://127.0.0.1:4173/reset', { method: 'POST' });
  const cacheDir = join(RUNTIME, `cache-${cell.id}`);
  await rm(cacheDir, { recursive: true, force: true });
  if (cell.copySeed) await cp(SEED, cacheDir, { recursive: true });
  else await mkdir(cacheDir, { recursive: true });
  const cacheBefore = await cacheManifest(cacheDir);
  await writeJson(join(RESULTS, `${cell.id}.cache-before.json`), cacheBefore);
  for (const suffix of ['report.json', 'dom.json', 'executor.jsonl', 'store.jsonl', 'fault.jsonl']) {
    await rm(join(RESULTS, `${cell.id}.${suffix}`), { force: true });
  }
  await rm(join(APP, '.e2e', 'report.json'), { force: true });
  const env = {
    ...process.env,
    HOME: join(RUNTIME, 'home'),
    E2E_TELEMETRY_DISABLED: '1',
    DO_NOT_TRACK: '1',
    E2E_UPDATE_CHECK_DISABLED: '1',
    E2E_RUN_ID: cell.id,
    E2E_ITEM_VALUE: cell.item,
    E2E_ALIAS_VALUE: cell.alias,
    E2E_ROUTE: cell.route ?? '/',
    E2E_CACHE_MODE: cell.cacheMode ?? 'read-write',
    E2E_CACHE_DIR: cacheDir,
    E2E_CALLS_LOG: join(RESULTS, `${cell.id}.executor.jsonl`),
    E2E_DOM_OUTPUT: join(RESULTS, `${cell.id}.dom.json`),
    E2E_STORE_LOG: join(RESULTS, `${cell.id}.store.jsonl`),
    E2E_FAULT_LOG: join(RESULTS, `${cell.id}.fault.jsonl`),
    E2E_STORE_FAULT: cell.storeFault ? 'write-throw' : '0',
    E2E_UNCERTAIN_TAP: cell.uncertainTap ? '1' : '0',
  };
  if (cell.ci) env.CI = '1'; else delete env.CI;
  const args = ['node_modules/e2e/dist/cli/bin.js', 'run', 'tests/workflow.e2e.ts'];
  if (cell.noCache) args.push('--no-cache');
  const startedAt = new Date().toISOString();
  const child = spawn(process.execPath, args, { cwd: APP, env, stdio: ['ignore', 'pipe', 'pipe'] });
  let stdout = ''; let stderr = '';
  child.stdout.on('data', (chunk) => { stdout += chunk; });
  child.stderr.on('data', (chunk) => { stderr += chunk; });
  const timer = setTimeout(() => child.kill('SIGKILL'), MAX_CELL_MS);
  const outcome = await new Promise((resolveRun, rejectRun) => {
    child.once('error', rejectRun);
    child.once('close', (code, signal) => resolveRun({ code, signal }));
  }).finally(() => clearTimeout(timer));
  await writeFile(join(RESULTS, `${cell.id}.log`), stdout + stderr, 'utf8');
  await writeFile(join(RESULTS, `${cell.id}.exitcode`), String(outcome.code) + '\n', 'utf8');
  if (await exists(join(APP, '.e2e', 'report.json'))) {
    await cp(join(APP, '.e2e', 'report.json'), join(RESULTS, `${cell.id}.report.json`));
  }
  const events = await (await fetch('http://127.0.0.1:4173/events')).json();
  await writeJson(join(RESULTS, `${cell.id}.events.json`), events);
  const cacheAfter = await cacheManifest(cacheDir);
  await writeJson(join(RESULTS, `${cell.id}.cache-after.json`), cacheAfter);
  if (cell.id === 'C0') {
    const names = Object.keys(cacheAfter);
    if (names.length === 1) await cp(join(cacheDir, names[0]), join(RESULTS, 'C0.cache-entry.json'));
  }
  await writeJson(join(RESULTS, `${cell.id}.receipt.json`), {
    id: cell.id, startedAt, finishedAt: new Date().toISOString(), ...outcome,
    item: cell.item, route: cell.route ?? '/', noCache: cell.noCache === true,
    ci: cell.ci === true, storeFault: cell.storeFault === true, uncertainTap: cell.uncertainTap === true,
  });
  return { cell, cacheAfter };
}

let server; let chrome;
try {
  await verifyFrozenInputs();
  await mkdir(RESULTS, { recursive: true });
  await mkdir(join(RUNTIME, 'home'), { recursive: true });
  server = spawn(process.execPath, [join(APP, 'server.mjs')], { cwd: APP, stdio: ['ignore', 'pipe', 'pipe'] });
  server.stdout.pipe(createWriteStream(join(RESULTS, 'server.log')));
  server.stderr.pipe(createWriteStream(join(RESULTS, 'server-error.log')));
  chrome = spawn('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', [
    '--headless=new', '--remote-debugging-port=9222', `--user-data-dir=${join(RUNTIME, 'chrome-profile')}`,
    '--no-first-run', '--no-default-browser-check', '--disable-background-networking', '--disable-component-update',
    '--no-proxy-server', 'about:blank',
  ], { env: { ...process.env, HOME: join(RUNTIME, 'home') }, stdio: ['ignore', 'pipe', 'pipe'] });
  chrome.stdout.pipe(createWriteStream(join(RESULTS, 'chrome.log')));
  chrome.stderr.pipe(createWriteStream(join(RESULTS, 'chrome-error.log')));
  await waitFor('http://127.0.0.1:4173/events');
  await waitFor('http://127.0.0.1:9222/json/version');
  const seedManifest = await json(join(ROOT, 'seed-manifest.json'));
  const seedNames = Object.keys(seedManifest);
  if (seedNames.length !== 1) throw new Error('focused seed must contain exactly one entry');
  await rm(SEED, { recursive: true, force: true });
  await mkdir(SEED, { recursive: true });
  await cp(join(ROOT, 'seed-entry.json'), join(SEED, seedNames[0]));
  if (await fileHash(join(SEED, seedNames[0])) !== seedManifest[seedNames[0]]) throw new Error('focused seed hash mismatch');
  for (const cell of cells) {
    const { cacheAfter } = await execute(cell);
    if (cell.id === 'C0') {
      if (!await baselineIsValid(cell, cacheAfter)) throw new Error('C0 baseline invalid; matrix stopped before treatment cells');
      await rm(SEED, { recursive: true, force: true });
      await cp(join(RUNTIME, 'cache-C0'), SEED, { recursive: true });
      await writeJson(join(RESULTS, 'seed.cache-before.json'), await cacheManifest(SEED));
    }
  }
  await writeJson(join(ROOT, 'driver-complete.json'), { completedAt: new Date().toISOString(), executions: cells.length });
  console.log(`Completed ${cells.length} frozen executions; evidence: ${relative(process.cwd(), RESULTS)}`);
} finally {
  await stopChild(chrome);
  await stopChild(server);
}
