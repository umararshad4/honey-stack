// Copy into the application's scripts directory. Run from its package root:
//   node scripts/run-webmcp.mjs run --target webmcp --workers 2
// e2e starts at once; while it loads, one isolated WebMCP-enabled Chromium boots per worker.
// The target's `webmcpBrowsers` provider (tests/helpers/webmcp.ts) gives each worker slot its own browser.
import { spawn } from 'node:child_process';
import { existsSync, readFileSync } from 'node:fs';
import { mkdtemp, rm } from 'node:fs/promises';
import module, { createRequire } from 'node:module';
import { availableParallelism, tmpdir } from 'node:os';
import { delimiter, dirname, join } from 'node:path';
import { setTimeout as delay } from 'node:timers/promises';

// Playwright 1.64.1's Chromium automation and headless switches, without its Edge-only entries:
// the browser e2e's ordinary local target gets. Chromium's sandbox stays on.
const DISABLED_FEATURES = [
  'AvoidUnnecessaryBeforeUnloadCheckSync', 'DestroyProfileOnBrowserClose', 'DialMediaRouteProvider',
  'GlobalMediaControls', 'HttpsUpgrades', 'LensOverlay', 'MediaRouter', 'PaintHolding',
  'ThirdPartyStoragePartitioning', 'BlockOriginHeaderModificationOnRedirect',
  'AvoidCorsURLLoaderRestartOnRedirect', 'Translate', 'AutoDeElevate', 'OptimizationHints',
  'NetworkTimeServiceQuerying', 'AimEnabled',
];
const SWITCHES = [
  '--disable-field-trial-config', '--disable-background-networking', '--disable-background-timer-throttling',
  '--disable-backgrounding-occluded-windows', '--disable-back-forward-cache', '--disable-breakpad',
  '--disable-client-side-phishing-detection', '--disable-component-extensions-with-background-pages',
  '--disable-component-update', '--no-default-browser-check', '--disable-default-apps', '--disable-dev-shm-usage',
  '--disable-extensions', `--disable-features=${DISABLED_FEATURES.join(',')}`, '--allow-pre-commit-input',
  '--disable-hang-monitor', '--disable-ipc-flooding-protection', '--disable-popup-blocking',
  '--disable-prompt-on-repost', '--disable-renderer-backgrounding', '--force-color-profile=srgb',
  '--metrics-recording-only', '--no-first-run', '--password-store=basic', '--use-mock-keychain',
  '--no-service-autorun', '--export-tagged-pdf', '--disable-search-engine-choice-screen', '--disable-infobars',
  '--disable-sync', '--enable-unsafe-swiftshader', '--hide-scrollbars', '--mute-audio',
  '--blink-settings=primaryHoverType=2,availableHoverTypes=2,primaryPointerType=4,availablePointerTypes=4',
  '--enable-features=WebMCP,CDPScreenshotNewSurface',
  '--remote-debugging-address=127.0.0.1', '--remote-debugging-port=0',
];

const args = process.argv.slice(2);
if (!args.length) throw new Error('Usage: node scripts/run-webmcp.mjs <e2e CLI arguments>');
const require = createRequire(join(process.cwd(), 'package.json'));
// The engine's own Playwright, whose browsers `npx @e2e-dev/web install chromium` installs.
const engine = (() => { try { return createRequire(require.resolve('@e2e-dev/web')); } catch { return require; } })();
const env = { ...process.env };
// Node's compile cache for e2e and its workers; NODE_DISABLE_COMPILE_CACHE=1 opts out.
const cache = module.enableCompileCache?.();
if (cache?.directory) env.NODE_COMPILE_CACHE ??= cache.directory;

// One browser per e2e worker: --workers, else e2e's own default (one in CI, half the cores locally).
const workers = (index => index < 0 ? undefined
  : args[index].includes('=') ? args[index].split('=')[1] : args[index + 1])(
  args.findIndex(arg => arg === '--workers' || arg.startsWith('--workers=')));
const ci = !['', '0', 'false', undefined].includes(process.env.CI?.trim().toLowerCase());
const count = Math.min(availableParallelism(), Math.max(1, Math.trunc(Number(
  process.env.HONEY_WEBMCP_BROWSERS ?? workers ?? (ci ? 1 : Math.floor(availableParallelism() / 2)))) || 1));
const profiles = await Promise.all(Array.from({ length: count }, () => mkdtemp(join(tmpdir(), 'honey-webmcp-'))));
const browsers = [];
let runner;
let stopping = false;
let failure;
const alive = child => child.pid !== undefined && child.exitCode === null && child.signalCode === null;
const exited = child => alive(child) ? new Promise(resolve => child.once('exit', resolve)) : Promise.resolve();
const stop = () => { stopping = true; runner?.kill('SIGTERM'); for (const browser of browsers) browser.kill('SIGTERM'); };
// Every repeat is forwarded: e2e escalates from interrupt to forced teardown, and the launcher
// stays alive to delete its profiles.
for (const signal of ['SIGINT', 'SIGTERM', 'SIGHUP']) process.on(signal, stop);
try {
  runner = spawn(process.execPath, [e2eCli(), ...args], {
    stdio: 'inherit',
    env: { ...env, HONEY_WEBMCP_PORT_FILES: profiles.map(profile => join(profile, 'DevToolsActivePort')).join(delimiter) },
  });
  const done = new Promise((resolve, reject) => {
    runner.once('error', reject);
    runner.once('exit', (code, signal) => resolve(signal ? 1 : code ?? 1));
  });
  const { executable, headless } = chromiumBuild();
  for (const profile of profiles) {
    // No startup page: e2e opens each test's page in its own context.
    const browser = spawn(executable, [headless, ...SWITCHES, `--user-data-dir=${profile}`, '--no-startup-window'], {
      stdio: ['ignore', 'ignore', 'inherit'],
    });
    browsers.push(browser);
    // A browser that cannot start, or stops mid-run, ends the run instead of leaving e2e waiting.
    browser.once('error', error => { failure ??= error; stop(); });
    browser.once('exit', () => { if (!stopping) { failure ??= new Error('A WebMCP browser stopped before e2e finished'); stop(); } });
  }
  const code = await done;
  if (failure) throw failure;
  process.exitCode = stopping ? 1 : code;
} finally {
  stop();
  const running = browsers.filter(alive);
  if (running.length) {
    const deadline = new AbortController();
    try {
      await Promise.race([Promise.all(running.map(exited)), delay(2000, undefined, { signal: deadline.signal })]);
    } finally {
      // A lost Promise.race does not cancel its timer; release it after a prompt exit.
      deadline.abort();
    }
    await Promise.all(running.filter(alive).map(browser => { browser.kill('SIGKILL'); return exited(browser); }));
  }
  // e2e stops on SIGTERM; a SIGKILL would orphan the app process it started.
  if (runner) await exited(runner);
  await Promise.all(profiles.map(profile => rm(profile, { recursive: true, force: true, maxRetries: 10 })
    .catch(error => console.error(`run-webmcp: could not remove ${profile}: ${error.message}`))));
}

function e2eCli() {
  for (let dir = dirname(require.resolve('e2e')); ; dir = dirname(dir)) {
    const file = join(dir, 'package.json');
    if (existsSync(file)) {
      const manifest = JSON.parse(readFileSync(file, 'utf8'));
      if (manifest.name === 'e2e') return join(dir, manifest.bin.e2e);
    }
    if (dirname(dir) === dir) throw new Error('Cannot find the e2e package');
  }
}

// Playwright's headless build, which its own headless launches use. The registry lookup is internal,
// so a moved API falls back to the public full-Chromium path. HONEY_WEBMCP_HEADLESS=new forces that.
function chromiumBuild() {
  if (process.env.HONEY_WEBMCP_HEADLESS !== 'new') {
    try {
      const { registry } = engine('playwright-core/lib/coreBundle').registry;
      const shell = registry.findExecutable('chromium-headless-shell').executablePath();
      if (shell && existsSync(shell)) return { executable: shell, headless: '--headless' };
    } catch { /* Fall back below. */ }
  }
  return { executable: engine('playwright-core').chromium.executablePath(), headless: '--headless=new' };
}
