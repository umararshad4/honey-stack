# Condition-based waiting

Trimmed from obra/superpowers 7.0.0 `skills/systematic-debugging/condition-based-waiting.md` (MIT, Jesse Vincent).

Flaky tests often guess at timing with fixed sleeps. They pass on a fast machine and fail under load or in CI. Wait for the condition you actually care about.

```typescript
// Guessing
await new Promise(r => setTimeout(r, 50));
expect(getResult()).toBeDefined();

// Waiting for the condition
await waitFor(() => getResult() !== undefined, 'result to be set');
expect(getResult()).toBeDefined();
```

## Helper

```typescript
async function waitFor<T>(
  condition: () => T | undefined | null | false,
  description: string,
  timeoutMs = 5000,
): Promise<T> {
  const start = Date.now();
  while (true) {
    const result = condition();          // read fresh state every poll
    if (result) return result;
    if (Date.now() - start > timeoutMs) {
      throw new Error(`Timeout waiting for ${description} after ${timeoutMs}ms`);
    }
    await new Promise(r => setTimeout(r, 10));
  }
}
```

Use the framework's built-in when it has one (Testing Library `waitFor`, Playwright auto-waiting `expect`, `pytest` polling helpers).

| Waiting for | Condition |
|---|---|
| An event | `events.find(e => e.type === 'DONE')` |
| A state | `machine.state === 'ready'` |
| A count | `items.length >= 5` |
| A file | `fs.existsSync(path)` |

Poll around every 10 ms, always with a timeout and a message that names what was awaited, and call the getter inside the loop so the state isn't stale.

## When a fixed delay is right

Only when the behavior under test is itself timed (debounce, throttle, tick intervals). First wait for the triggering condition, then wait a duration derived from the known timing, and comment why:

```typescript
await waitForEvent(manager, 'TOOL_STARTED');
await new Promise(r => setTimeout(r, 200)); // 2 ticks at the tool's 100ms interval
```
