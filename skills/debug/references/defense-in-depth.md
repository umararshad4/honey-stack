# Defense in depth

Trimmed from obra/superpowers 7.0.0 `skills/systematic-debugging/defense-in-depth.md` (MIT, Jesse Vincent).

Use after the root cause is fixed, when the bad value could reach the same place through other paths: other callers, a refactor, a mock that skips the entry check. One check fixes the bug; a check at each layer the data crosses makes the class of bug impossible.

## The layers

1. **Entry point**: reject obviously invalid input at the API boundary.
   ```typescript
   function createProject(name: string, workingDirectory: string) {
     if (!workingDirectory?.trim()) throw new Error('workingDirectory cannot be empty');
     if (!existsSync(workingDirectory)) throw new Error(`workingDirectory does not exist: ${workingDirectory}`);
     // ...
   }
   ```
2. **Business logic**: check that the data makes sense for this operation.
   ```typescript
   if (!projectDir) throw new Error('projectDir required for workspace initialization');
   ```
3. **Environment guard**: refuse dangerous operations in contexts where they never belong.
   ```typescript
   if (process.env.NODE_ENV === 'test' && !resolve(directory).startsWith(resolve(tmpdir()))) {
     throw new Error(`Refusing git init outside temp dir during tests: ${directory}`);
   }
   ```
4. **Forensic signal**: a log with context and stack right before the operation, for when the other layers miss.

## Applying it

1. Trace the data flow from origin to the failing operation.
2. List every point it passes through.
3. Add the check that belongs at each point. Guards go at real boundaries; internal code can trust its own types.
4. Test each layer by bypassing the one before it and confirming the next one catches it.

In the source session, each of the four layers caught a case the others missed: a different code path skipped entry validation, mocks skipped the business check, and a platform edge case needed the environment guard.
