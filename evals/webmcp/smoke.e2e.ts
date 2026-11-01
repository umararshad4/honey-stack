import assert from 'node:assert/strict';
import { test } from '@e2e-dev/web';
import { expect } from 'e2e';
import { webmcp, webmcpBatch } from '../../skills/qa/assets/webmcp/webmcp';

test('native tools and visible controls agree', async ({ app, browser, screen }) => {
  await app.open('/');
  await expect(screen.getByRole('heading', 'WebMCP counter')).toBeVisible();
  const tools = await webmcp(browser);
  if (tools.status === 'unavailable') {
    assert.equal(process.env.HONEY_WEBMCP_PORT_FILES, undefined);
  } else {
    assert.equal(tools.status, 'available');
    assert(tools.tools?.some(tool => tool.name === 'increment'));
    const call = await webmcp(browser, { name: 'increment', input: { amount: 2 } });
    assert.equal(call.status, 'called');
    assert.deepEqual(call.result, { content: [{ type: 'text', text: '2' }] });
    await expect(screen.getByRole('status')).toHaveText('2');
    // Reset state to isolate the actual control test from tool setup.
    await browser.reload();
  }
  await screen.getByRole('button', 'Increment').tap();
  await expect(screen.getByRole('status')).toHaveText('1');
  await app.screenshot('native-and-ui');
});

test('tool failures and invalid inputs cannot pass', { skip: !process.env.HONEY_WEBMCP_PORT_FILES && 'Requires the WebMCP target' }, async ({ app, browser }) => {
  await app.open('/');
  const discovery = await webmcp(browser);
  assert.equal(discovery.status, 'available');
  await assert.rejects(webmcp(browser, { name: 'missing', input: {} }), /unavailable/);
  await assert.rejects(webmcp(browser, { name: 'failure', input: {} }), /reported failure/);
  await assert.rejects(webmcp(browser, { name: 'throws', input: {} }));
  await assert.rejects(webmcp(browser, { name: 'increment', input: { amount: -1 } }));
});

test('navigation invalidates tool discovery', async ({ app, browser }) => {
  await app.open('/');
  const before = await webmcp(browser);
  await browser.goto('/empty');
  const after = await webmcp(browser);
  assert.equal(after.status, before.status === 'unavailable' ? 'unavailable' : 'no-tools');
  await assert.rejects(webmcp(browser, { name: 'increment', input: { amount: 1 } }), /unavailable/);
});

test('batch preserves order and stops after failure or navigation', { skip: !process.env.HONEY_WEBMCP_PORT_FILES && 'Requires the WebMCP target' }, async ({ app, browser, screen }) => {
  await app.open('/');
  const results = await webmcpBatch(browser, [
    { name: 'increment', input: { amount: 1 } },
    { name: 'increment', input: { amount: 2 } },
  ]);
  assert.equal(results.length, 2);
  await expect(screen.getByRole('status')).toHaveText('3');
  await assert.rejects(webmcpBatch(browser, [
    { name: 'increment', input: { amount: 4 } },
    { name: 'failure', input: {} },
    { name: 'increment', input: { amount: 100 } },
  ]), /call 2/);
  await expect(screen.getByRole('status')).toHaveText('7');
  await assert.rejects(webmcpBatch(browser, [
    { name: 'navigate', input: {} },
    { name: 'increment', input: { amount: 100 } },
  ]), /Page changed/);
  await expect(screen.getByRole('status')).toHaveText('7');
});
