import { readFile, writeFile } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = dirname(fileURLToPath(import.meta.url));
const RESULTS = join(ROOT, 'results');
const cells = [
  { id: 'C0', item: 'Alpha 001' }, { id: 'C1', item: 'Beta 002' },
  { id: 'C2', item: 'Gamma 003' }, { id: 'W1', item: 'Delta 004', route: '/other' },
  { id: 'P1', item: 'Collision' }, { id: 'R1', item: 'Echo 005' },
  { id: 'F1', item: 'Flush 006' }, { id: 'U1', item: 'Uncertain 007' },
  { id: 'N1', item: 'Negative 008' },
];
async function json(path, fallback = null) {
  try { return JSON.parse(await readFile(path, 'utf8')); } catch { return fallback; }
}
async function lines(path) {
  try { const text = await readFile(path, 'utf8'); return text.trim().split('\n').filter(Boolean).map(JSON.parse); }
  catch { return []; }
}
function agentStep(report) {
  return report?.run?.results?.flatMap((result) => result.attempts ?? [])
    .flatMap((attempt) => attempt.steps ?? []).find((step) => step.kind === 'agent');
}
function normalize(value, item) {
  if (typeof value === 'string') return value.split(item).join('{item}');
  if (Array.isArray(value)) return value.map((entry) => normalize(entry, item));
  if (value && typeof value === 'object') {
    return Object.fromEntries(Object.entries(value)
      .filter(([key]) => !['at', 'sequence'].includes(key))
      .map(([key, entry]) => [key, normalize(entry, item)]));
  }
  return value;
}
function check(list, name, pass, actual) { list.push({ name, pass: pass === true, actual }); }

const matrix = [];
for (const cell of cells) {
  const prefix = join(RESULTS, cell.id);
  const [report, receipt, events, dom, cacheBefore, cacheAfter] = await Promise.all([
    json(`${prefix}.report.json`), json(`${prefix}.receipt.json`), json(`${prefix}.events.json`, []),
    json(`${prefix}.dom.json`), json(`${prefix}.cache-before.json`, {}), json(`${prefix}.cache-after.json`, {}),
  ]);
  const executor = await lines(`${prefix}.executor.jsonl`);
  const store = await lines(`${prefix}.store.jsonl`);
  const faults = await lines(`${prefix}.fault.jsonl`);
  const calls = executor.filter((event) => event.kind === 'call');
  const cache = agentStep(report)?.cache;
  const commits = events.filter((event) => event.type === 'save-committed');
  const requests = events.filter((event) => event.type === 'save-request');
  const checks = [];
  check(checks, 'primary-report-present', report !== null, receipt?.reportPresent ?? Boolean(report));
  check(checks, 'one-current-commit', commits.length === 1 && commits[0]?.item === cell.item, commits);
  check(checks, 'one-current-request', requests.length === 1 && requests[0]?.item === cell.item, requests);
  check(checks, 'no-cross-cell-side-effect', [...commits, ...requests].every((event) => event.item === cell.item), [...requests, ...commits]);
  check(checks, 'final-dom-current-item', dom?.status === `Saved ${cell.item}` && dom?.input === cell.item && dom?.items?.join('|') === cell.item, dom);
  check(checks, 'expected-route', dom?.path === (cell.route ?? '/'), dom?.path);
  if (cell.id === 'C0') {
    check(checks, 'C0-one-live-call', calls.length === 1, calls.length);
    check(checks, 'C0-no-entry', cache?.mode === 'missed' && cache?.reason === 'no-entry', cache);
    check(checks, 'C0-saved', cache?.write === 'saved' && Object.keys(cacheAfter).length === 1, { cache, entries: Object.keys(cacheAfter).length });
  }
  if (['C1', 'N1'].includes(cell.id)) {
    check(checks, `${cell.id}-zero-live-calls`, calls.length === 0, calls.length);
    check(checks, `${cell.id}-full-replay`, cache?.mode === 'self-finalized' && cache?.replayedActions === 2, cache);
    check(checks, `${cell.id}-kept`, cache?.write === 'kept', cache?.write);
  }
  if (cell.id === 'C2') {
    check(checks, 'C2-one-live-call', calls.length === 1, calls.length);
    check(checks, 'C2-cache-off', agentStep(report) !== undefined && cache === undefined, cache);
  }
  if (cell.id === 'W1') {
    check(checks, 'W1-wrong-context', cache?.mode === 'missed' && cache?.reason === 'wrong-context', cache);
    check(checks, 'W1-live-recovery', calls.length === 1 && report?.run?.summary?.passed === 1, { calls: calls.length, summary: report?.run?.summary });
  }
  if (cell.id === 'P1') {
    check(checks, 'P1-one-live-call', calls.length === 1, calls.length);
    check(checks, 'P1-collision-reported', cache?.notRecorded === 'param-collision', cache);
    check(checks, 'P1-no-entry-written', Object.keys(cacheAfter).length === 0, cacheAfter);
  }
  if (cell.id === 'R1') {
    check(checks, 'R1-ci', report?.run?.environment?.ci === true, report?.run?.environment?.ci);
    check(checks, 'R1-zero-live-calls', calls.length === 0, calls.length);
    check(checks, 'R1-full-replay', cache?.mode === 'self-finalized' && cache?.replayedActions === 2, cache);
    check(checks, 'R1-byte-identical-cache', JSON.stringify(cacheBefore) === JSON.stringify(cacheAfter), { before: cacheBefore, after: cacheAfter });
  }
  if (cell.id === 'F1') {
    const ops = store.map((entry) => entry.op);
    check(checks, 'F1-write-fault-delivered', ops.includes('read') && ops.at(-1) === 'write' && store.at(-1)?.result === 'throw-EACCES', store.map((entry) => ({ op: entry.op, result: entry.result })));
    check(checks, 'F1-one-live-call', calls.length === 1, calls.length);
  }
  if (cell.id === 'U1') {
    check(checks, 'U1-action-uncertain', cache?.mode === 'missed' && cache?.reason === 'action-uncertain', cache);
    check(checks, 'U1-handoff-names-tap', calls.length === 1 && calls[0]?.replayedPrefix?.stopReason === 'action-uncertain' && calls[0]?.replayedPrefix?.uncertainAction?.includes('tap'), calls.map((call) => call.replayedPrefix));
    check(checks, 'U1-fault-after-real-tap-once', faults.length === 1 && faults[0]?.fault === 'commit-then-ACTION_MAY_HAVE_COMMITTED', faults);
    check(checks, 'U1-verified-not-repeated', executor.some((event) => event.kind === 'verification' && event.result === 'committed-once-not-repeated'), executor);
  }
  matrix.push({
    id: cell.id,
    exitCode: receipt?.code,
    reportStatus: report?.run?.summary,
    cache,
    ci: report?.run?.environment?.ci,
    executorCalls: calls.length,
    executor,
    storeOps: store.map((entry) => ({ op: entry.op, result: entry.result })),
    faultDeliveries: faults.length,
    cacheWritePresent: cache !== undefined && Object.hasOwn(cache, 'write'),
    normalizedEvents: normalize(events, cell.item),
    normalizedDom: normalize(dom, cell.item),
    matchesPreregisteredExpectation: checks.every((entry) => entry.pass),
    checks,
  });
}
const byId = Object.fromEntries(matrix.map((row) => [row.id, row]));
const semanticArms = ['C0', 'C1', 'C2'];
const reference = JSON.stringify({ events: byId.C0?.normalizedEvents, dom: byId.C0?.normalizedDom });
const semanticDifferential = semanticArms.map((id) => ({
  id,
  equalToC0: JSON.stringify({ events: byId[id]?.normalizedEvents, dom: byId[id]?.normalizedDom }) === reference,
  events: byId[id]?.normalizedEvents,
  dom: byId[id]?.normalizedDom,
}));
await writeFile(join(RESULTS, 'matrix.json'), JSON.stringify(matrix, null, 2) + '\n', 'utf8');
await writeFile(join(RESULTS, 'semantic-differential.json'), JSON.stringify(semanticDifferential, null, 2) + '\n', 'utf8');
console.log(JSON.stringify({
  cells: matrix.map((row) => ({ id: row.id, matches: row.matchesPreregisteredExpectation, failedChecks: row.checks.filter((check) => !check.pass).map((check) => check.name) })),
  semanticDifferential: semanticDifferential.map((row) => ({ id: row.id, equalToC0: row.equalToC0 })),
}, null, 2));
