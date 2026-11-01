// Repeated, matched functional QA benchmark. Expected product failures stay failures.
import { spawn } from 'node:child_process';
import { performance } from 'node:perf_hooks';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import assert from 'node:assert/strict';

const here = dirname(fileURLToPath(import.meta.url));
const project = resolve(here, '..');
const output = resolve(here, '.e2e', new Date().toISOString().replaceAll(':', '-'));
await mkdir(output, { recursive: true });
const server = spawn(process.execPath, [resolve(here, 'server.mjs')], { stdio: ['ignore', 'pipe', 'inherit'] });
const url = await new Promise((resolveURL, reject) => {
  const timer = setTimeout(() => reject(new Error('Fixture startup timed out')), 5000);
  server.once('error', error => { clearTimeout(timer); reject(error); });
  server.once('exit', code => { clearTimeout(timer); reject(new Error(`Fixture exited ${code}`)); });
  server.stdout.once('data', data => {
    clearTimeout(timer);
    const match = String(data).match(/APP_URL=(http:\/\/127\.0\.0\.1:\d+)/);
    if (!match) reject(new Error('Fixture did not publish its URL')); else resolveURL(match[1]);
  });
});

const failures = new Set();
for (const viewport of ['desktop', 'mobile']) {
  for (const title of [
    'form preserves High priority and Unicode title',
    'form preserves Low priority and Unicode title',
    'saved tasks persist after reload',
    'completion persists after reload',
    'Escape closes the dialog',
  ]) failures.add(`${viewport}: ${title}`);
}
failures.add('mobile: page fits the viewport');

const rows = [];
let reference;
try {
  for (let pair = -1; pair < 5; pair++) {
    for (const mode of pair % 2 === 0 ? ['ui', 'webmcp'] : ['webmcp', 'ui']) {
      const label = `${pair < 0 ? 'warmup' : `pair-${pair}`}-${mode}`;
      const runOutput = resolve(output, label);
      const started = performance.now();
      const child = spawn(process.execPath, [
        resolve(project, '../../skills/qa/assets/webmcp/run.mjs'),
        'run', '--config', resolve(here, 'e2e.config.ts'), '--retries', '0', '--workers', '1', '--output', runOutput,
      ], { cwd: project, env: { ...process.env, APP_URL: url, SETUP_MODE: mode, E2E_TELEMETRY_DISABLED: '1' }, stdio: ['ignore', 'pipe', 'pipe'] });
      const chunks = [];
      child.stdout.on('data', data => chunks.push(data));
      child.stderr.on('data', data => chunks.push(data));
      const exitCode = await new Promise((resolveExit, reject) => {
        child.once('error', reject);
        child.once('exit', code => resolveExit(code));
      });
      const wallMs = performance.now() - started;
      await writeFile(resolve(output, `${label}.log`), Buffer.concat(chunks));
      const report = JSON.parse(await readFile(resolve(runOutput, 'report.json'), 'utf8')).run;
      const selected = report.results.filter(result => result.selected);
      assert.equal(selected.length, 24, `${label}: every case must run at both viewports`);
      assert.equal(exitCode, 1, `${label}: seeded product defects must fail the runner`);
      assert.equal(report.summary.flaky, 0);
      assert.equal(report.summary.skipped, 0);
      assert.equal(report.errors.length, 0);
      const outcomes = selected.map(result => ({
        name: `${result.targetId}: ${result.titlePath.at(-1)}`, status: result.status,
      })).sort((a, b) => a.name.localeCompare(b.name));
      const actualFailures = new Set(outcomes.filter(result => result.status === 'failed').map(result => result.name));
      assert.deepEqual(actualFailures, failures, `${label}: missing bug or unexpected failure`);
      for (const result of outcomes) assert.equal(result.status, failures.has(result.name) ? 'failed' : 'passed');
      if (reference) assert.deepEqual(outcomes, reference, `${label}: mode changed coverage/outcomes`);
      else reference = outcomes;
      const runnerMs = new Date(report.finishedAt) - new Date(report.startedAt);
      const row = { pair, mode, wallMs, runnerMs, summary: report.summary, report: resolve(runOutput, 'report.json') };
      if (pair >= 0) rows.push(row);
      console.log(`${label}: ${Math.round(wallMs)}ms wall, ${runnerMs}ms runner, 13 passed / 11 expected failures; exact defect parity`);
    }
  }
  const percentile = (values, p) => [...values].sort((a, b) => a - b)[Math.ceil(p * values.length) - 1];
  const summary = Object.fromEntries(['ui', 'webmcp'].map(mode => [mode,
    Object.fromEntries(['wallMs', 'runnerMs'].map(key => [key,
      Object.fromEntries([['p50', .5], ['p95', .95], ['p99', .99]].map(([name, p]) => [name,
        percentile(rows.filter(row => row.mode === mode).map(row => row[key]), p)])),
    ])),
  ]));
  await writeFile(resolve(output, 'summary.json'), JSON.stringify({
    scope: '24 cases, both viewports, identical assertions/timeouts/artifacts, 5 measured pairs plus excluded warm-up pair, alternating order, fresh browser per run, no model calls; wall includes launcher startup, runner does not.',
    rows, summary, outcomes: reference,
  }, null, 2));
  console.log(JSON.stringify({ output, summary }, null, 2));
} finally {
  server.kill('SIGTERM');
}
