# Architecture vocabulary

Use these terms exactly in every suggestion. Consistent words are what make two suggestions comparable.

## Glossary

- **Module**: anything with an interface and an implementation, at any scale (function, class, package, slice across tiers). Avoid: unit, component, service.
- **Interface**: everything a caller must know to use the module correctly: types, plus invariants, ordering, error modes, required configuration, performance. Avoid: API, signature (they name only the type-level surface).
- **Implementation**: the code inside a module.
- **Depth**: behavior a caller or test can exercise per unit of interface it must learn. **Deep**: small interface, much behavior. **Shallow**: interface nearly as complex as the implementation.
- **Seam**: a place where behavior can change without editing that place; where an interface lives. Avoid: boundary.
- **Adapter**: a concrete thing that fills an interface at a seam. Names a role, not a size.
- **Leverage**: what callers gain from depth: more capability per unit of interface learned.
- **Locality**: what maintainers gain from depth: change, bugs and verification concentrate in one place.

## Principles

- Depth belongs to the interface. A deep module may be built from small parts; they just aren't in its interface.
- **Deletion test**: delete the module in your head. Complexity vanishes → pass-through. Complexity reappears in N callers → it earns its keep.
- **The interface is the test surface.** If tests must reach past it, the module is the wrong shape.
- **One adapter = a hypothetical seam. Two adapters = a real one.**
- A deep module is not a deep call chain. A chain scatters understanding across layers; a deep module concentrates it.
- Testable shapes accept their dependencies, return results instead of mutating, and keep the surface small.

## Dependency categories

The category decides how the deepened module is tested across its seam.

1. **In-process** (pure computation, in-memory state): merge and test through the new interface. No adapter.
2. **Local-substitutable** (PGLite for Postgres, in-memory filesystem): test with the stand-in. The seam stays internal.
3. **Remote but owned** (your own services over the network): a port at the seam; HTTP/queue adapter in production, in-memory adapter in tests.
4. **True external** (Stripe, Twilio): inject it as a port; tests use a mock adapter.

## Red flags

- **Shallow module**: callers coordinate several methods for one operation; options expose internal stages; learning the interface doesn't spare learning the implementation.
- **Pass-through layer**: forwards the same arguments to a method of the same shape. Wrappers with one caller, adapters with one implementation. Inline them.
- **Information leakage**: one representation, policy or protocol detail known in several modules, so a change needs coordinated edits. Wire and storage types re-exported publicly count.
- **Temporal decomposition**: modules split by execution order (load, validate, transform, save) instead of by the knowledge they own.
- **Split ownership**: more than one module writes the same state or keeps its own copy. Give each piece of state one owner.
- **Two ways to do one task**: the next contributor copies whichever they find first. Keep one; migrate callers; delete the rest.
- **Importable internals**: if outside code can import them, they are part of the interface. Make the import fail the build.
- **Hand-synced lists**: several places list the same items. Derive the others from one, or fail the build when they disagree.
- **Wide mutable scope**: prefer returns over mutation, locals over fields, fields over module state, module state over globals. Derive instead of sync.

## Tests: replace, don't layer

Once tests exist at the deepened interface, delete the old tests on the shallow modules. Assert observable outcomes through the interface. A test that must change when the implementation changes is testing past the interface.
