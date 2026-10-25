import { appendFile } from 'node:fs/promises';
import { deterministicExecutor } from './executor.mjs';
import { auditedWeb } from './uncertain-engine.mjs';

const failingStore = {
  writable: true,
  async read(keyHash) {
    await appendFile(process.env.E2E_STORE_LOG, JSON.stringify({ op: 'read', keyHash, result: 'miss' }) + '\n', 'utf8');
    return { status: 'miss' };
  },
  async write(keyHash, payload) {
    await appendFile(process.env.E2E_STORE_LOG, JSON.stringify({ op: 'write', keyHash, payload, result: 'throw-EACCES' }) + '\n', 'utf8');
    throw new Error('EACCES: deterministic cache write fault');
  },
};

const mode = process.env.E2E_CACHE_MODE ?? 'read-write';
const cache = process.env.E2E_STORE_FAULT === 'write-throw'
  ? { mode: 'read-write', store: failingStore, strict: false }
  : {
      ...(mode === 'default' ? {} : { mode }),
      dir: process.env.E2E_CACHE_DIR,
      strict: false,
    };

export default {
  projectId: 'e2e-semantic-commit-audit',
  targets: [{ engine: auditedWeb(), app: { url: 'http://127.0.0.1:4173' } }],
  agents: { default: { executor: deterministicExecutor } },
  cache,
  workers: 1,
  retries: 0,
  timeout: 60000,
  launchTimeout: 60000,
};
