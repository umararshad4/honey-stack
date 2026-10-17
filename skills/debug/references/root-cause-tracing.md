# Root cause tracing

Trimmed from obra/superpowers 7.0.0 `skills/systematic-debugging/root-cause-tracing.md` (MIT, Jesse Vincent).

Bugs often surface deep in the call stack: `git init` in the wrong directory, a file written to the wrong place, a database opened with the wrong path. The fix belongs where the bad value originated, not where it blew up.

## Trace backward

1. **Symptom**: `Error: git init failed in ~/project/packages/core`
2. **Immediate cause**: the code that directly fails.
   ```typescript
   await execFileAsync('git', ['init'], { cwd: projectDir });
   ```
3. **Who called it, with what?**
   ```
   WorktreeManager.createSessionWorktree(projectDir, sessionId)
     ← Session.initializeWorkspace()
     ← Session.create()
     ← test: Project.create()
   ```
4. **Follow the value up.** `projectDir = ''`. An empty `cwd` resolves to `process.cwd()`, which is the source tree.
5. **Find the origin.**
   ```typescript
   const context = setupCoreTest();              // returns { tempDir: '' } until beforeEach runs
   Project.create('name', context.tempDir);      // read at module load, before beforeEach
   ```

Root cause: a top-level read of a value initialised later. Fix: make `tempDir` a getter that throws if read before `beforeEach`. Then add layer checks so the same class of bug can't recur (`defense-in-depth.md`).

## When you can't trace by reading

Log just before the dangerous operation, not after it fails, with the context and a stack:

```typescript
async function gitInit(directory: string) {
  console.error('[DEBUG-a4f2] git init', {
    directory,
    cwd: process.cwd(),
    nodeEnv: process.env.NODE_ENV,
    stack: new Error().stack,
  });
  await execFileAsync('git', ['init'], { cwd: directory });
}
```

```bash
npm test 2>&1 | grep '\[DEBUG-a4f2\]'
```

- In tests, write to stderr (`console.error`); a logger may be silenced.
- Read the stacks for test file names, the triggering line, and the pattern (same test? same argument?).

## When you don't know which test causes it

If an artifact (a stray `.git`, a temp file, a mutated fixture) appears during the suite, bisect the test files:

```bash
bash scripts/find-polluter.sh '.git' 'src/**/*.test.ts'
```

It runs test files one at a time and stops at the first one that creates the artifact.
