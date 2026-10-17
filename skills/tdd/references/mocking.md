# When to mock

Read before adding a mock, fake or test helper.

## Mock at system boundaries only

Mock these:
- external APIs (payment, email, third-party services)
- time and randomness
- databases and the file system, sometimes; prefer a test DB or a temp dir

Use the real thing for your own modules and internal collaborators, and for anything else you control.

## Mock at the right level

Before replacing a method, list its side effects. Mock the slow or external operation below the ones the test depends on, and keep those real.

```typescript
// The mock swallows the config write that duplicate detection reads
vi.mock("ToolCatalog", () => ({ discoverAndCacheTools: vi.fn().mockResolvedValue(undefined) }));

// Mock only the slow server startup; the config write stays real
vi.mock("MCPServerManager");
```

If you are unsure, run the test against the real implementation first and watch what actually has to happen.

## Rules for doubles

- **Assert on the real component, never on the mock.** An assertion that fails when you remove the mock only tests the mock.
- **Mirror the real data completely.** Include every documented field, not only the ones this test reads. Partial mocks pass while integration breaks.
- **Make doubles specific.** Give each branch (success, error, malformed) its own fixture, so the wrong branch can't satisfy the expectation. When arguments or ordering are part of the contract, assert them.
- **Keep test-only code out of production.** A `destroy()` or `reset()` that only tests call belongs in test utilities.
- **Mock setup larger than the test logic** is the signal to switch to an integration test with real components.

## Design for mockability

Pass boundary dependencies in instead of constructing them inside:

```typescript
// Easy to mock
function processPayment(order, paymentClient) {
  return paymentClient.charge(order.total);
}

// Hard to mock
function processPayment(order) {
  return new StripeClient(process.env.STRIPE_KEY).charge(order.total);
}
```

Prefer SDK-style interfaces, with one function per external operation, over one generic fetcher:

```typescript
// Each function mocks with one fixed shape and no conditional logic
const api = {
  getUser: (id) => fetch(`/users/${id}`),
  createOrder: (data) => fetch("/orders", { method: "POST", body: data }),
};
```
