// Agent-driven QA benchmark: the same exploratory flow through agent-browser and Playwright MCP.
// Measures wall time, tool calls and the text an agent must read (chars, ~tokens = chars/4).
import { spawn, execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { mkdirSync, writeFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const run = promisify(execFile);
const ROUNDS = Number(process.env.ROUNDS ?? 5);
const out = join(here, '.out', new Date().toISOString().replace(/[:.]/g, '-'));
mkdirSync(out, { recursive: true });

function startServer() {
  return new Promise((resolve, reject) => {
    const p = spawn(process.execPath, [join(here, '../webmcp/benchmark/server.mjs')]);
    p.stdout.on('data', d => { const m = /APP_URL=(\S+)/.exec(String(d)); if (m) resolve({ p, url: m[1] }); });
    p.on('error', reject);
  });
}

// Find a ref for `role "name"` in either tool's snapshot text.
function ref(snapshot, role, name) {
  const line = snapshot.split('\n').find(l => l.includes(`${role} "${name}"`) && /ref=e\d+/.test(l));
  if (!line) throw new Error(`no ${role} "${name}" in snapshot:\n${snapshot}`);
  return /ref=(e\d+)/.exec(line)[1];
}

// The flow: open, inspect, create a High task, verify, complete it, search, screenshot.
async function flow(t) {
  let s = await t.open();
  s = await t.snapshot(s);
  await t.click(ref(s, 'button', 'New task'), 'New task');
  s = await t.snapshot();
  await t.fill(ref(s, 'textbox', 'Title'), 'Title', 'Ship report');
  await t.select(ref(s, 'combobox', 'Priority'), 'Priority', 'High');
  await t.click(ref(s, 'button', 'Save task'), 'Save task');
  s = await t.snapshot();
  if (!s.includes('Ship report')) throw new Error('task not created');
  await t.click(ref(s, 'checkbox', 'Complete Ship report'), 'Complete Ship report');
  await t.fill(ref(s, 'searchbox', 'Search tasks'), 'Search tasks', 'Ship');
  s = await t.snapshot();
  if (s.includes('Plan sprint')) throw new Error('search did not filter');
  await t.screenshot();
}

function agentBrowser(url, session, shot, full) {
  const bin = join(here, 'node_modules/.bin/agent-browser');
  const stats = { calls: 0, chars: 0 };
  const ab = async (...args) => {
    stats.calls++;
    const { stdout } = await run(bin, [...args, '--session', session], { maxBuffer: 1 << 24 });
    stats.chars += stdout.length;
    return stdout;
  };
  return {
    stats,
    open: () => ab('open', url),
    snapshot: () => full ? ab('snapshot') : ab('snapshot', '-i'),
    click: r => ab('click', '@' + r),
    fill: (r, _n, v) => ab('fill', '@' + r, v),
    select: (r, _n, v) => ab('select', '@' + r, v),
    screenshot: () => ab('screenshot', shot),
    close: () => run(bin, ['close', '--session', session]).catch(() => {}),
  };
}

function playwrightMcp(url, shot) {
  const p = spawn(join(here, 'node_modules/.bin/playwright-mcp'), ['--headless', '--isolated', '--output-dir', dirname(shot)], { stdio: ['pipe', 'pipe', 'inherit'] });
  const pending = new Map(); let id = 0; let buf = '';
  p.stdout.on('data', d => {
    buf += d; let i;
    while ((i = buf.indexOf('\n')) >= 0) {
      const msg = JSON.parse(buf.slice(0, i)); buf = buf.slice(i + 1);
      pending.get(msg.id)?.(msg); pending.delete(msg.id);
    }
  });
  const rpc = (method, params) => new Promise((res, rej) => {
    const n = ++id; pending.set(n, m => m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result));
    p.stdin.write(JSON.stringify({ jsonrpc: '2.0', id: n, method, params }) + '\n');
  });
  const stats = { calls: 0, chars: 0 };
  const call = async (name, args = {}) => {
    stats.calls++;
    const r = await rpc('tools/call', { name, arguments: args });
    const text = r.content.filter(c => c.type === 'text').map(c => c.text).join('\n');
    if (r.isError) throw new Error(text);
    stats.chars += text.length;
    return text;
  };
  return {
    stats,
    init: async () => {
      await rpc('initialize', { protocolVersion: '2025-06-18', capabilities: {}, clientInfo: { name: 'bench', version: '0' } });
      p.stdin.write(JSON.stringify({ jsonrpc: '2.0', method: 'notifications/initialized' }) + '\n');
    },
    open: () => call('browser_navigate', { url }),
    // Actions link the snapshot as a file in this version, so the agent asks for it inline.
    snapshot: () => call('browser_snapshot'),
    click: (ref, element) => call('browser_click', { target: ref, element }),
    fill: (ref, element, text) => call('browser_type', { target: ref, element, text }),
    select: (ref, element, v) => call('browser_select_option', { target: ref, element, values: [v] }),
    screenshot: () => call('browser_take_screenshot', { filename: shot }),
    close: async () => { await call('browser_close').catch(() => {}); p.kill(); },
  };
}

async function measure(mode, url, round) {
  const shot = join(out, `${mode}-${round}.png`);
  const t0 = performance.now();
  const t = mode === 'playwright-mcp' ? playwrightMcp(url, shot) : agentBrowser(url, `bench-${process.pid}-${mode}-${round}`, shot, mode === 'agent-browser-full');
  try {
    await t.init?.();
    await flow(t);
  } finally { await t.close(); }
  return { mode, round, ms: Math.round(performance.now() - t0), ...t.stats };
}

const { p: server, url } = await startServer();
const results = [];
try {
  for (let round = 0; round <= ROUNDS; round++) {
    const modes = ['agent-browser', 'agent-browser-full', 'playwright-mcp'];
    const order = modes.map((_, i) => modes[(i + round) % modes.length]); // rotate order each round
    for (const mode of order) {
      const r = await measure(mode, url, round);
      if (round > 0) results.push(r); // round 0 is warm-up
      console.log(round ? '' : '(warm-up)', JSON.stringify(r));
    }
  }
} finally { server.kill(); }

const median = a => { const s = [...a].sort((x, y) => x - y); return s[s.length >> 1]; };
const summary = Object.fromEntries(['agent-browser', 'agent-browser-full', 'playwright-mcp'].map(m => {
  const rs = results.filter(r => r.mode === m);
  return [m, { runs: rs.length, medianMs: median(rs.map(r => r.ms)), minMs: Math.min(...rs.map(r => r.ms)), maxMs: Math.max(...rs.map(r => r.ms)), calls: rs[0].calls, chars: median(rs.map(r => r.chars)), approxTokens: Math.round(median(rs.map(r => r.chars)) / 4) }];
}));
writeFileSync(join(out, 'summary.json'), JSON.stringify({ results, summary }, null, 2));
console.table(summary);
