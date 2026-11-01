import assert from 'node:assert/strict';
import { execFile } from 'node:child_process';
import { mkdtemp, readFile, rm, writeFile, mkdir } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join, resolve, delimiter } from 'node:path';
import { promisify } from 'node:util';
import { afterAll, beforeAll, test } from 'e2e';

const execute = promisify(execFile);
type Fixture = {
  thread: string; keyword: string; source: string; external_id: string; live: boolean;
  messages: { number: number; role: string; buffer: string; tool_calls: unknown[] }[];
  decisions: { ttl: string; cache: string; rollback: string };
};
let fixture: Fixture;
let temporary: string;
let python: string;
let counter = 0;
let cli: string;

beforeAll(async () => {
  const file = process.env.HONEY_DELTA_COMPARE_FIXTURE;
  assert(file, 'Run tests/qa_delta_compare.py to prepare the controlled fixture');
  fixture = JSON.parse(await readFile(file, 'utf8'));
  temporary = await mkdtemp(join(tmpdir(), 'honey-delta-acceptance-'));
  python = process.env.HONEY_PYTHON ?? (await execute('python3', ['-c', 'import sys; print(sys.executable)'])).stdout.trim();
  cli = join(process.env.HONEY_DELTA_CANDIDATE_ROOT ?? resolve('../..'), 'bin/honey');
});

afterAll(async () => { if (temporary) await rm(temporary, { recursive: true, force: true }); });

async function honey(args: string[], env: NodeJS.ProcessEnv = {}) {
  const options = { timeout: 120_000, maxBuffer: 3 * 1024 * 1024,
    env: { ...process.env, HONEY_HOME: join(temporary, 'home'), HONEY_NO_AUTOUPDATE: '1', ...env } };
  try {
    return { code: 0, ...(await execute(python, [cli, 'delta', ...args], options)) };
  } catch (error) {
    const result = error as Error & { code: number | string; stdout: string; stderr: string };
    if (typeof result.code !== 'number') throw error;
    return { code: result.code, stdout: result.stdout, stderr: result.stderr };
  }
}

async function fake(scenario = 'normal') {
  const log = join(temporary, `calls-${++counter}.jsonl`);
  await writeFile(log, '');
  return { HONEY_DELTA_FAKE_SCENARIO: scenario, HONEY_DELTA_CALL_LOG: log,
    PATH: `${process.env.HONEY_DELTA_FAKE_BIN}${delimiter}${process.env.PATH ?? ''}` };
}

async function project() {
  const path = await mkdtemp(join(temporary, 'project-'));
  await execute('git', ['init', '-q', path]);
  await writeFile(join(path, 'app.txt'), 'original application state\n');
  await execute('git', ['-C', path, 'add', 'app.txt']);
  await execute('git', ['-C', path, '-c', 'user.name=Honey QA', '-c', 'user.email=qa@example.invalid',
    'commit', '-qm', 'Synthetic QA baseline']);
  return path;
}

test('recall finds the late accepted decision with exact message provenance', async () => {
  const result = await honey(['recall', fixture.keyword, 'ttl', 'decision', '--max-chars', '12000'], await fake());
  assert.equal(result.code, 0, result.stderr);
  const data = JSON.parse(result.stdout);
  assert.equal(data.status, 'found');
  assert.equal(data.thread, fixture.thread);
  assert(JSON.stringify(data.transcript).includes(fixture.decisions.ttl));
  assert(!JSON.stringify(data.transcript).includes('initial proposal is 300 seconds, pending investigation'));
  assert(data.transcript.some((message: { number: number }) => message.number === 38));
  assert(result.stdout.trimEnd().length <= 12000);
});

test('ambiguous search returns candidates without attributing a decision to either', async () => {
  const result = await honey(['recall', 'decision'], await fake('ambiguous'));
  assert.equal(result.code, 0, result.stderr);
  const data = JSON.parse(result.stdout);
  assert.equal(data.status, 'ambiguous');
  assert.equal(data.threads.length, 2);
  assert(!data.transcript?.length);
});

test('stale summaries never become accepted historical facts or full transcript dumps', async () => {
  const result = await honey(['summary', fixture.thread], await fake());
  assert.equal(result.code, 0, result.stderr);
  const data = JSON.parse(result.stdout);
  assert.equal(data.summary, null);
  assert.equal(data.summary_state, 'stale');
  assert.equal(data.message_count, 40);
  assert(!result.stdout.includes('STALE_SUMMARY_SENTINEL'));
  assert(!result.stdout.includes(fixture.messages[0].buffer.trim()));
});

test('large message and tool output is bounded and explicitly marked truncated', async () => {
  const result = await honey(['read', fixture.thread, '--messages', '1-1', '--max-chars', '4000'], await fake('huge'));
  assert.equal(result.code, 0, result.stderr);
  assert.equal(JSON.parse(result.stdout).truncated, true);
  assert(result.stdout.trimEnd().length <= 4000, `Returned ${result.stdout.trimEnd().length} characters`);
});

test('nonretryable access failure keeps its safe code without leaking raw diagnostics', async () => {
  const env = await fake('denied');
  const result = await honey(['search', 'decision'], env);
  assert.equal(result.code, 1);
  const data = JSON.parse(result.stdout);
  assert.equal(data.error, 'not_visible');
  assert.equal(data.retryable, false);
  assert(!`${result.stdout}${result.stderr}`.includes('SENTINEL_SECRET'));
  assert.equal((await readFile(env.HONEY_DELTA_CALL_LOG, 'utf8')).trim().split('\n').length, 1);
});

test('explicitly retryable temporary failure recovers with one bounded retry', async () => {
  const env = await fake('retryable');
  const result = await honey(['search', 'decision'], env);
  assert.equal(result.code, 0, result.stderr);
  assert.equal(JSON.parse(result.stdout).threads[0].id, fixture.thread);
  assert.equal((await readFile(env.HONEY_DELTA_CALL_LOG, 'utf8')).trim().split('\n').length, 2);
});

test('authenticated local history with queued upload is never reported cloud-ready', async () => {
  const root = await project();
  const result = await honey(['status', '--project', root, '--thread', fixture.thread,
    '--source', fixture.source, '--external-id', fixture.external_id], await fake());
  assert.equal(result.code, 0, result.stderr);
  const data = JSON.parse(result.stdout);
  assert.equal(data.ready, true);
  assert.equal(data.readiness.history_readable, true);
  assert.equal(data.readiness.cloud_uploaded, false);
  assert.equal(data.cloud.state, 'queued');
  assert.equal(data.capture.configured, false);
});

test('invalid native byte offsets fail instead of returning a guessed excerpt', async () => {
  const result = await honey(['recall', fixture.keyword, 'ttl', '--thread', fixture.thread], await fake('bad_offsets'));
  assert.equal(result.code, 1);
  assert.equal(JSON.parse(result.stdout).error, 'invalid_response');
});

test('capture preview writes nothing and explicit apply preserves unrelated settings', async () => {
  const root = await project();
  const env = await fake();
  const args = ['setup', '--project', root, '--mode', 'private', '--organization', 'org_synthetic'];
  const preview = await honey(args, env);
  assert.equal(preview.code, 0, preview.stderr);
  assert.equal(JSON.parse(preview.stdout).applied, false);
  await assert.rejects(readFile(join(root, '.delta/settings.json')));
  await mkdir(join(root, '.delta'));
  await writeFile(join(root, '.delta/settings.json'), JSON.stringify({ editor: { font_size: 17 } }));
  const applied = await honey([...args, '--apply'], env);
  assert.equal(applied.code, 0, applied.stderr);
  assert.equal(JSON.parse(applied.stdout).applied, true);
  const settings = JSON.parse(await readFile(join(root, '.delta/settings.json'), 'utf8'));
  assert.deepEqual(settings.editor, { font_size: 17 });
  assert.equal(settings.threads.mode, 'private');
  assert.equal(settings.threads.organization, 'org_synthetic');
  await execute('git', ['-C', root, 'check-ignore', '--quiet', '.delta/settings.json']);
  assert.equal((await readFile(env.HONEY_DELTA_CALL_LOG, 'utf8')).length, 0, 'Setup must not upload or invoke Delta');
});

test('capture refuses to overwrite invalid policy', async () => {
  const root = await project();
  await mkdir(join(root, '.delta'));
  await writeFile(join(root, '.delta/settings.json'), '{ invalid existing config');
  const result = await honey(['setup', '--project', root, '--mode', 'manual', '--apply'], await fake());
  assert.equal(result.code, 1);
  assert.equal(await readFile(join(root, '.delta/settings.json'), 'utf8'), '{ invalid existing config');
});

test('real handoff attach and restore preserve the human summary and detect changed evidence', async () => {
  const root = await project();
  const env = await fake();
  const file = join(temporary, 'handoff.md');
  const evidence = join(temporary, 'qa-result.json');
  const human = '# Handoff\n\n## Goal\nFinish token recovery.\n\n## Decisions\n' + fixture.decisions.ttl + '\n\n## Next steps\nVerify the current source.\n';
  await writeFile(file, human);
  await writeFile(evidence, '{"passed":true}\n');
  const attached = await honey(['attach', file, fixture.thread, '--project', root, '--messages', '37-39',
    '--source', fixture.source, '--external-id', fixture.external_id, '--evidence', evidence], env);
  assert.equal(attached.code, 0, attached.stderr);
  assert((await readFile(file, 'utf8')).startsWith(human));
  const restored = await honey(['restore', file, '--project', root], env);
  assert.equal(restored.code, 0, restored.stderr);
  const initial = JSON.parse(restored.stdout);
  assert.equal(initial.git.head_matches, true);
  assert.equal(initial.git.branch_matches, true);
  assert.equal(initial.git.worktree_matches, true);
  assert.equal(initial.history.available, true);
  assert(initial.local_handoff.includes('Finish token recovery.'));
  assert.equal(initial.evidence[0].status, 'unchanged');
  await writeFile(join(root, 'app.txt'), 'changed after the handoff\n');
  await writeFile(evidence, '{"passed":false}\n');
  const drift = await honey(['restore', file, '--project', root], env);
  assert.equal(drift.code, 0, drift.stderr);
  const changed = JSON.parse(drift.stdout);
  assert.equal(changed.git.worktree_matches, false);
  assert.equal(changed.evidence[0].status, 'changed');
  const absent = await honey(['restore', file, '--project', root], { ...env, PATH: '/usr/bin:/bin' });
  assert.equal(absent.code, 0, absent.stderr);
  const fallback = JSON.parse(absent.stdout);
  assert.equal(fallback.history.available, false);
  assert(fallback.local_handoff.includes('Finish token recovery.'));
});

test('live native Delta recall recovers the exact late decision', async () => {
  test.skip(!fixture.live, 'Requires --live; deterministic tests do not prove native Delta retrieval');
  const result = await honey(['recall', fixture.keyword, 'ttl', 'decision', '--scope', 'messages']);
  assert.equal(result.code, 0, result.stderr);
  const data = JSON.parse(result.stdout);
  assert.equal(data.thread, fixture.thread);
  assert(JSON.stringify(data.transcript).includes(fixture.decisions.ttl));
  assert(data.transcript.some((message: { number: number }) => message.number === 38));
});

test('live native Delta status keeps cloud readiness tied to the observed upload state', async () => {
  test.skip(!fixture.live, 'Requires --live; cloud state cannot be inferred from a fake CLI');
  const result = await honey(['status', '--thread', fixture.thread,
    '--source', fixture.source, '--external-id', fixture.external_id]);
  assert.equal(result.code, 0, result.stderr);
  const data = JSON.parse(result.stdout);
  assert.equal(data.readiness.history_readable, true);
  assert.equal(data.readiness.cloud_uploaded, data.cloud.state === 'uploaded');
  if (data.cloud.state === 'queued') assert.equal(data.cloud.url, null);
});
