# Good and bad tests

Read when writing or changing a test.

## Good: behavior through the interface

```typescript
test("user can checkout with valid cart", async () => {
  const cart = createCart();
  cart.add(product);
  const result = await checkout(cart, paymentMethod);
  expect(result.status).toBe("confirmed");
});
```

It tests what callers care about, uses the public API only, survives internal refactors, and its name says WHAT, not HOW.

## Bad: implementation details

```typescript
// Asserts on a mock, not on the code
test("checkout calls paymentService.process", async () => {
  const mockPayment = jest.mock(paymentService);
  await checkout(cart, payment);
  expect(mockPayment.process).toHaveBeenCalledWith(cart.total);
});

// Bypasses the interface to verify
test("createUser saves to database", async () => {
  await createUser({ name: "Alice" });
  const row = await db.query("SELECT * FROM users WHERE name = ?", ["Alice"]);
  expect(row).toBeDefined();
});
```

Verify through the interface instead:

```typescript
test("createUser makes user retrievable", async () => {
  const user = await createUser({ name: "Alice" });
  expect((await getUser(user.id)).name).toBe("Alice");
});
```

Red flags: mocking internal collaborators, testing private methods, asserting call counts or order that no caller can see, a name that describes HOW, and a test that breaks on a refactor that keeps behavior the same.

## Two imagined edits

Judge every test against both:

- **Break the behavior.** Return a wrong value, skip an effect, or do it twice. If the test still passes, it proves nothing. The usual causes are a loose assertion, an expected value computed by the code under test, and asserting on data the test built itself.
- **Change the internals.** Keep every observable result and restructure the code. If the test now fails, it is pinned to the implementation.

Keep the tests that catch the first edit and survive the second.

The contract decides. If "an empty cart never charges" is the promise, then "payment client got no call" is behavior. Pair it with a case where the charge does happen, so the test shows it can see a call. The payload an external service receives is behavior. A call to an internal helper is not.

## Expected values

```typescript
// Mirror assertion: the same builder computes both sides, so it is always true
const expected = buildSearchQuery({ tag: "urgent" });
expect(buildSearchQuery({ tag: "urgent" })).toBe(expected);

// Hand-derived literal
expect(buildSearchQuery({ tag: "urgent" })).toBe('tag:"urgent"');
```

Prefer table-driven tests with literal `want` values.

## Change detectors

A test that only an intentional decision can fail fires on every redesign and sleeps through bugs. Examples are `expect(MAX_RETRIES).toBe(5)`, exact error wording that no caller reads, and a grep of a file's text. Test the behavior that depends on the decision instead: a failing call is retried 5 times and the 6th attempt never happens.

Test your code's contract at its boundaries, not the framework's. Trivial getters, constructors and forwarding get a test only when they validate, normalize, default or cause side effects.

## Mutation check before finishing

Mentally mutate the production code. At least one test should fail for each of:

- a wrong constant or argument
- the wrong branch handler
- a missing state change or side effect
- an empty or default return
- missing validation for zero, empty, nil, unauthorized or malformed input

A mutation that nothing catches marks behavior as unprotected, or a test as tautological.
