import type { Browser, BrowserLease, BrowserProvider, BrowserRequest } from '@e2e-dev/web';
import type { JsonValue } from 'e2e';
import { readFile } from 'node:fs/promises';
import { delimiter } from 'node:path';
import { setTimeout as delay } from 'node:timers/promises';

let leases = 0;
// `web({ browser: webmcpBrowsers })`: each worker slot attaches to its own browser started by
// scripts/run-webmcp.mjs, so every browser has one CDP client. On a shared browser, each worker's
// Playwright also attaches to every other worker's pages. The launcher closes and deletes them.
export const webmcpBrowsers: BrowserProvider = {
  name: 'honey-webmcp',
  async acquire({ env, signal, log }: BrowserRequest): Promise<BrowserLease> {
    const files = (env.HONEY_WEBMCP_PORT_FILES ?? process.env.HONEY_WEBMCP_PORT_FILES ?? '')
      .split(delimiter).filter(Boolean);
    if (!files.length) throw new Error('Run this target through scripts/run-webmcp.mjs');
    const lease = leases++;
    if (lease === files.length) {
      log(`more worker slots than ${files.length} WebMCP browser(s); pass --workers to scripts/run-webmcp.mjs so each worker gets its own`);
    }
    return { id: `honey-webmcp-${lease + 1}`, cdpEndpoint: await endpoint(files[lease % files.length], signal) };
  },
  async release() { /* The launcher owns these browsers. */ },
};

// The launcher starts e2e before its browsers are ready; wait for Chromium's own port file.
async function endpoint(file: string, signal: AbortSignal) {
  const deadline = Date.now() + 15_000;
  for (;;) {
    signal.throwIfAborted();
    try {
      const port = Number((await readFile(file, 'utf8')).split('\n')[0]);
      if (Number.isInteger(port) && port > 0) return `http://127.0.0.1:${port}`;
    } catch (error) {
      // Not written yet, or (on Windows) still open for writing.
      if (!['ENOENT', 'EBUSY'].includes((error as { code?: string }).code ?? '')) throw error;
    }
    if (Date.now() > deadline) throw new Error('WebMCP browser did not become ready within 15s');
    await delay(10, undefined, { signal });
  }
}

type Call = { name: string; input: JsonValue };
type WebMCPResult = {
  status: 'available' | 'unavailable' | 'no-tools' | 'called';
  tools: { name: string; description: string; inputSchema: JsonValue; annotations: JsonValue }[];
  name: string | null;
  result: JsonValue;
};
type Evaluation = { discovery: WebMCPResult | null; results: WebMCPResult[] };

async function evaluateCalls(browser: Browser, calls: readonly Call[] | null, batch: boolean) {
  return browser.evaluate(async (request): Promise<Evaluation> => {
    type Tool = { name: string; description?: string; inputSchema?: JsonValue; annotations?: JsonValue; window?: Window };
    type Context = {
      getTools?: () => Tool[] | Promise<Tool[]>;
      executeTool?: (tool: Tool, input: JsonValue) => unknown | Promise<unknown>;
    };
    const context = (document as Document & { modelContext?: Context }).modelContext
      ?? (navigator as Navigator & { modelContext?: Context }).modelContext;
    if (!isSecureContext || !context?.getTools || !context.executeTool) {
      if (request.calls) throw new Error('WebMCP unavailable: do not replace a required tool check with a pass');
      return { discovery: { status: 'unavailable', tools: [], name: null, result: null }, results: [] };
    }
    const ownTools = async () => (await context.getTools!()).filter(tool => !('window' in tool) || tool.window === window);
    if (!request.calls) {
      const tools = await ownTools();
      return { discovery: {
        status: tools.length ? 'available' : 'no-tools', name: null, result: null,
        tools: tools.map(tool => ({ name: tool.name, description: tool.description ?? '',
          inputSchema: tool.inputSchema ?? null, annotations: tool.annotations ?? null })),
      }, results: [] };
    }
    const url = location.href;
    const results: WebMCPResult[] = [];
    for (const [index, call] of request.calls.entries()) {
      try {
        if (request.batch && location.href !== url) throw new Error('Page changed; stop the batch');
        // Refresh the registry without another host/browser round trip.
        const tool = (await ownTools()).find(tool => tool.name === call.name);
        if (!tool) throw new Error(`WebMCP tool unavailable in current document: ${call.name}`);
        const raw = await context.executeTool(tool, call.input);
        let result = raw;
        if (typeof raw === 'string') { try { result = JSON.parse(raw); } catch { /* Plain text is valid. */ } }
        if (result && typeof result === 'object' && 'isError' in result && result.isError === true)
          throw new Error(`WebMCP tool reported failure: ${call.name}`);
        results.push({ status: 'called', tools: [], name: call.name, result: (result ?? null) as JsonValue });
        if (request.batch && location.href !== url) throw new Error('Page changed; stop the batch');
      } catch (error) {
        if (!request.batch) throw error;
        throw new Error(`WebMCP batch stopped at call ${index + 1} (${call.name}); earlier writes may have completed. Verify state before retrying. ${String(error)}`);
      }
    }
    return { discovery: null, results };
  }, { calls, batch });
}

// Invokes existing page tools; never registers or emulates them.
export async function webmcp(browser: Browser, call?: Call): Promise<WebMCPResult> {
  const result = await evaluateCalls(browser, call ? [call] : null, false);
  return call ? result.results[0] : result.discovery!;
}

// Only for reviewed fixture calls that stay on one page. Executes sequentially.
// Stops at the first error; a batch is not a transaction and is never retried here.
export async function webmcpBatch(browser: Browser, calls: readonly Call[]): Promise<WebMCPResult[]> {
  if (!calls.length) return [];
  return (await evaluateCalls(browser, calls, true)).results;
}
