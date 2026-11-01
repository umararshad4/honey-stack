import { test, afterEach } from '@e2e-dev/web';
import { expect, type Screen } from 'e2e';
import type { Browser } from '@e2e-dev/web';
import { webmcp, webmcpBatch } from '../../../skills/qa/assets/webmcp/webmcp';

const mode = process.env.SETUP_MODE;
if (mode !== 'ui' && mode !== 'webmcp') throw new Error('SETUP_MODE must be ui or webmcp');

async function createThroughUI(screen: Screen, title: string, priority = 'Normal') {
  await screen.getByRole('button', 'New task').tap();
  await screen.getByLabel('Title').fill(title);
  await screen.getByLabel('Priority').selectOption(priority);
  await screen.getByRole('button', 'Save task').tap();
}

// Only this fixture helper differs between modes. Acceptance actions stay below.
async function givenTasks(browser: Browser, screen: Screen, prefix = 'Seed') {
  if (mode === 'webmcp') {
    const capability = await webmcp(browser);
    expect(capability.status).toBe('available');
    expect(capability.tools.some(tool => tool.name === 'create_task')).toBe(true);
    const results = await webmcpBatch(browser, Array.from({ length: 8 }, (_, index) => ({
      name: 'create_task', input: { title: `${prefix} task ${index}`, priority: 'Normal' },
    })));
    expect(results.length).toBe(8);
  } else {
    for (let index = 0; index < 8; index++) {
      await createThroughUI(screen, `${prefix} task ${index}`);
    }
  }
  // Identical independent fixture-state assertions in both modes.
  await expect(screen.getByRole('listitem')).toHaveCount(9);
  for (let index = 0; index < 8; index++) {
    await expect(screen.getByText(`${prefix} task ${index}`)).toBeVisible();
  }
}

afterEach(async ({ app }) => { await app.screenshot('end-state'); });

for (const priority of ['Normal', 'High', 'Low']) {
  test(`form preserves ${priority} priority and Unicode title`, async ({ app, screen }) => {
    await app.open('/');
    const title = `${priority} café 日本語`;
    await createThroughUI(screen, title, priority);
    await expect(screen.getByText(title)).toBeVisible();
    await expect(screen.getByRole('listitem').filter({ hasText: title })).toContainText(`Priority: ${priority}`);
  });
}

test('saved tasks persist after reload', async ({ app, browser, screen }) => {
  await app.open('/'); await givenTasks(browser, screen);
  await browser.reload();
  await expect(screen.getByText('Seed task 7')).toBeVisible();
});

test('completion persists after reload', async ({ app, browser, screen }) => {
  await app.open('/');
  await screen.getByRole('checkbox', 'Complete Plan sprint').check();
  await expect(screen.getByRole('checkbox', 'Complete Plan sprint')).toBeChecked();
  await browser.reload();
  await expect(screen.getByRole('checkbox', 'Complete Plan sprint')).toBeChecked();
});

test('search filters and clears results', async ({ app, browser, screen }) => {
  await app.open('/'); await givenTasks(browser, screen);
  await screen.getByLabel('Search tasks').fill('task 7');
  await expect(screen.getByRole('listitem')).toHaveCount(1);
  await expect(screen.getByText('Seed task 7')).toBeVisible();
  await screen.getByLabel('Search tasks').fill('no-such-task');
  await expect(screen.getByRole('listitem')).toHaveCount(0);
  await screen.getByLabel('Search tasks').fill('');
  await expect(screen.getByRole('listitem')).toHaveCount(9);
});

test('search supports Unicode', async ({ app, browser, screen }) => {
  await app.open('/'); await givenTasks(browser, screen, '日本語');
  await screen.getByLabel('Search tasks').fill('日本語 task 3');
  await expect(screen.getByRole('listitem')).toHaveCount(1);
  await expect(screen.getByText('日本語 task 3')).toBeVisible();
});

test('checkbox completes and uncompletes a task', async ({ app, browser, screen }) => {
  await app.open('/'); await givenTasks(browser, screen);
  const checkbox = screen.getByRole('checkbox', 'Complete Seed task 7');
  await checkbox.check(); await expect(checkbox).toBeChecked();
  await checkbox.uncheck(); await expect(checkbox).not.toBeChecked();
});

test('Cancel closes without creating a task', async ({ app, screen }) => {
  await app.open('/');
  await screen.getByRole('button', 'New task').tap();
  await screen.getByLabel('Title').fill('Discard me');
  await screen.getByRole('button', 'Cancel').tap();
  await expect(screen.getByRole('dialog')).toBeHidden();
  await expect(screen.getByRole('listitem')).toHaveCount(1);
});

test('Escape closes the dialog', async ({ app, browser, screen }) => {
  await app.open('/');
  await screen.getByRole('button', 'New task').tap();
  await browser.keyboard.press('Escape');
  await expect(screen.getByRole('dialog')).toBeHidden();
});

test('empty title is rejected by the form', async ({ app, screen }) => {
  await app.open('/');
  await screen.getByRole('button', 'New task').tap();
  await screen.getByRole('button', 'Save task').tap();
  await expect(screen.getByRole('dialog')).toBeVisible();
  await expect(screen.getByRole('listitem')).toHaveCount(1);
});

test('page fits the viewport', async ({ app, browser }) => {
  await app.open('/');
  const geometry = await browser.evaluate(() => ({ width: innerWidth, scroll: document.documentElement.scrollWidth }));
  expect(geometry.scroll).toBeLessThanOrEqual(geometry.width);
});
