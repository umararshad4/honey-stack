# Refactor candidates

Read on green, after a TDD cycle. Run the tests after every step, and stop refactoring the moment one goes red.

- **Duplication** that must change together: extract a function. Leave harmless near-copies alone; premature abstraction costs more than duplication.
- **A long function doing several unrelated jobs**: split it by job, not by line count. Keep the tests on the public interface.
- **Shallow modules**, where the interface is as complex as the implementation: combine them, or deepen one so a small interface hides more work.
- **Feature envy**: move the logic to where its data lives.
- **Primitive obsession**: introduce a value type where the same validation repeats.
- **Existing code** that the new code shows is wrong or clumsy: fix it if you touched it, otherwise note it.

The refactor step adds no behavior. A new behavior needs a new red test first.
