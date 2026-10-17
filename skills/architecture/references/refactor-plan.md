# Refactor plan sections

Hand these to the `plan` skill as the plan's body. Keep file paths in the steps and out of the decision record, where they go stale.

## Problem
The friction, from the developer's side: what is hard to change, test or understand today, and the evidence.

## Preserved behavior
The interface, outputs, side effects, UI, stored data and error modes that must not change, and the check that pins each one.

## Target shape
The deepened module: its interface, what it hides, where the seam sits, its adapters. The caller's usage first, then the types. Link the branch 2 design if one was made.

## Alternatives considered
At least one other shape and why it lost, judged on depth rather than effort.

## Steps
Tiny steps, each leaving the program working and ending with its verify command. Usual order:
1. Characterization tests at the current interface, where coverage is thin.
2. Prefactor: moves and renames that make the change easy, no behavior change.
3. Introduce the new interface beside the old one.
4. Migrate callers in batches, verifying after each batch.
5. Delete the old interface, its adapters and the tests that pinned its internals, in the same wave.

## Testing decisions
Which interface the tests cross, what a good test asserts here (observable behavior only), and existing tests to copy the style of.

## Out of scope
What this refactor deliberately leaves alone.
