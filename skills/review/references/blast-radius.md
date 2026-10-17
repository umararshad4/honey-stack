# Blast radius

Read for "what could this break", "blast radius of X", or a small diff you don't trust.

A write-up that sounds right is worth nothing, because it reads as convincing whether or not it is true. Find the one or two facts the change's safety rests on, and prove them.

## Proof ladder

For each load-bearing fact, climb as far as is cheap and say where you stopped:

1. Asserted. Worth nothing on its own.
2. Pointed at: a real `file:line`, or the library's own source at the pinned version.
3. Walked: you traced the failure step by step and it does not reach.
4. Ran: a script or test calls the real code and fails loudly if you are wrong.
5. Reproduced in the running app.

Step 4 is usually one small script that imports the same library version the app ships and calls the exact function you are worried about.

## Steps

1. **Read the change.** Look at the symbols it adds, changes and deletes, and at what it now does differently, including what the diff does not spell out. Pull the PR and commit messages for intent.
2. **Find the one fact.** Most risky-looking changes are safe because of a single fact, such as "this call only drops cache entries that are already dead". If that fact holds, most risks clear at once. Spend your time here, not on a long list of maybes.
3. **Look where grep stops:**
   - library source at the pinned version, and any local patch
   - timing: microtasks, teardown and unmount order, retries
   - data contracts: JSON an API returns, a DB column, a wire format, another language reading the same bytes
   - feature flags and environment differences
   - code several hops downstream, and new enum values reaching old `switch` statements
4. **Rate each risk honestly** by its real chance and real cost. Cite a real `file:line`. A search that finds nothing is still an answer. Never invent a caller or an API.
5. **Prove the one fact.** Write the script or test, run it, and paste what happened.

## Report

- **What it does:** what changed, including the non-obvious part.
- **Safe because:** the one fact, the ladder step it reached, and the proof. Write `unproven` if you couldn't prove it.
- **Risks:** for each, how it breaks, `file:line`, likelihood, cost, and how to check it.
- **Cleared:** what you checked and why it is fine.
- **Before merge:** the cheapest test or repro that would catch the real bug, including the script you wrote.
