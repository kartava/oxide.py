# Nothing is a `@final` class with one instance

The variant of an Option with no value is `@final class Nothing`, and `Nothing()` always returns the same instance. The pattern is `case Nothing():`, the same text as the constructor call, and `match` and `isinstance` narrow both branches on mypy, pyright, ty and pyrefly.

## Considered Options

- **An enum member, such as `_NothingType.NOTHING`.** Rejected: outside `match`, pyrefly narrows to the enum class and not to the member, and the pattern needs an import of a private name.
- **A `NOTHING` constant next to the class.** Rejected: it adds a second spelling, and `option is NOTHING` narrows only one branch, on some checkers.
- **Python's `None`.** Rejected: `Some(None)` must stay a Some (see [CONTEXT.md](../../CONTEXT.md)), so the variant needs its own type.
