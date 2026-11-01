import assert from 'node:assert/strict';
import { execFile } from 'node:child_process';
import { mkdtemp, readFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { promisify } from 'node:util';
import { afterAll, beforeAll, test } from 'e2e';

const execute = promisify(execFile);
const cli = resolve('../../bin/honey');
let python: string;
let temporary: string;
let fixture: { thread: string; keyword: string; request: string; response: string } | undefined;

beforeAll(async () => {
  python = process.env.HONEY_PYTHON ?? (await execute('python3', ['-c', 'import sys; print(sys.executable)'])).stdout.trim();
  temporary = await mkdtemp(join(tmpdir(), 'honey-delta-e2e-'));
  if (process.env.HONEY_DELTA_QA_FIXTURE) {
    fixture = JSON.parse(await readFile(process.env.HONEY_DELTA_QA_FIXTURE, 'utf8'));
  }
});

afterAll(async () => {
  if (temporary) await rm(temporary, { recursive: true, force: true });
});

async function honey(args: string[], env: NodeJS.ProcessEnv = {}) {
  const options = { timeout: 60_000, maxBuffer: 2 * 1024 * 1024,
    env: { ...process.env, HONEY_HOME: join(temporary, 'home'), HONEY_NO_AUTOUPDATE: '1', ...env } };
  try {
    const result = await execute(python, [cli, 'delta', ...args], options);
    return { code: 0, ...result };
  } catch (error) {
    const result = error as Error & { code: number | string; stdout: string; stderr: string };
    if (typeof result.code !== 'number') throw error;
    return { code: result.code, stdout: result.stdout, stderr: result.stderr };
  }
}

test('readiness distinguishes an optional dependency from an authenticated account', async () => {
  const result = await honey(['status']);
  assert.equal(result.code, 0, result.stderr);
  const status = JSON.parse(result.stdout);
  assert.equal(typeof status.ready, 'boolean');
  if (fixture) assert.equal(status.ready, true);
  if (status.ready) {
    assert.match(status.version, /^\d+\.\d+\.\d+$/);
    assert.equal(typeof status.login, 'string');
    assert(status.login.length > 0);
  } else {
    assert(['not_installed', 'unsupported_version', 'signed_out', 'signing_in'].includes(status.reason));
  }
});

test('missing Delta leaves the local handoff fallback available', async () => {
  const result = await honey(['status'], { PATH: temporary });
  assert.equal(result.code, 0);
  const status = JSON.parse(result.stdout);
  assert.equal(status.ready, false);
  assert.equal(status.reason, 'not_installed');
});

test('missing Delta cannot masquerade as an empty search', async () => {
  const result = await honey(['search', 'decision'], { PATH: temporary });
  assert.equal(result.code, 1);
  assert.equal(JSON.parse(result.stdout).error, 'not_installed');
});

test('foreign links and option-like references are rejected before invoking Delta', async () => {
  for (const reference of ['https://example.invalid/join/thread_test', '--help', 'thread_a/../b']) {
    const result = await honey(['read', '--', reference], { PATH: temporary });
    assert.equal(result.code, 2);
    assert.equal(result.stdout, '');
    assert.doesNotMatch(result.stderr, /Traceback/);
  }
});

test('invalid and oversized windows are rejected before invoking Delta', async () => {
  for (const window of ['0-1', '3-2', '1-21']) {
    const result = await honey(['read', 'thread_test', '--messages', window], { PATH: temporary });
    assert.equal(result.code, 2);
    assert.equal(result.stdout, '');
  }
});

test('a live unmatched query is a successful empty result', async () => {
  test.skip(!fixture, 'Run tests/qa_delta.py --live to prepare a private synthetic thread');
  const result = await honey(['search', `${fixture!.keyword}-no-match`, '--limit', '1']);
  assert.equal(result.code, 0, result.stderr);
  assert.deepEqual(JSON.parse(result.stdout), { source: 'delta', threads: [] });
});

test('live search and bounded reads preserve synthetic history without inventing a share link', async () => {
  test.skip(!fixture, 'Run tests/qa_delta.py --live to prepare a private synthetic thread');
  const search = await honey(['search', fixture!.keyword, '--scope', 'messages', '--limit', '5']);
  assert.equal(search.code, 0, search.stderr);
  const matches = JSON.parse(search.stdout);
  assert.equal(matches.source, 'delta');
  assert(matches.threads.some((thread: { id: string }) => thread.id === fixture!.thread));

  const first = await honey(['read', fixture!.thread]);
  assert.equal(first.code, 0, first.stderr);
  const firstMessage = JSON.parse(first.stdout);
  assert.equal(firstMessage.thread, fixture!.thread);
  assert.equal(firstMessage.url, null);
  assert.equal(firstMessage.messages, '1-1');
  assert(JSON.stringify(firstMessage.transcript).includes(fixture!.request));
  assert(!JSON.stringify(firstMessage.transcript).includes(fixture!.response));

  const full = await honey(['read', fixture!.thread, '--messages', '1-2']);
  assert.equal(full.code, 0, full.stderr);
  const history = JSON.parse(full.stdout);
  assert.equal(history.thread, fixture!.thread);
  assert.equal(history.url, null);
  assert(JSON.stringify(history.transcript).includes(fixture!.request));
  assert(JSON.stringify(history.transcript).includes(fixture!.response));
});
