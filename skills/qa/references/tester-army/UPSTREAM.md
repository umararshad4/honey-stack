# Upstream source

Source: https://github.com/tester-army/e2e
Commit: `1d671f6786b1eff4b43718ddc413b0bfa21abbcb`
Checked: 2026-11-01
Packages at this snapshot: `e2e@0.22.0`, `@e2e-dev/web@0.15.4`.

The three skill directories are vendored from upstream. Their entry files are named `GUIDE.md` to avoid registering duplicate Honey skills; the generator's sibling entry link uses that filename. Other reference content is unchanged. `LICENSE` and `NOTICE` are retained. The installed package's `npx e2e guide <topic>` takes precedence when its version differs.

The runtime is installed in the app being tested, not in Honey's Python runtime.
