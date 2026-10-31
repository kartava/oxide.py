# oxide.py — Spec

## Problem Statement

A Python developer who wants an absent value or an expected failure in a function's type has no library that works on every type checker. `rustedpy/result` is archived, and its `result.is_ok()` methods narrow nothing. `returns` needs a mypy plugin, so its pyright support is weaker. The developer cannot rely on `match` or `if` to narrow both branches on mypy, pyright, ty and pyrefly alike, and a library with one maintainer can stop at any release.

## Solution

The `oxide` package gives an Option (a Some or Nothing) and a Result (an Ok or an Err), in the terms of [CONTEXT.md](../CONTEXT.md). Each is a closed union, so `match`, `isinstance` and `if result:` narrow both branches on all four checkers, with no plugin and no config. A do function replaces Rust's `?`, and `@catch` turns the expected exceptions of a raising function into an Err. The codebase stays small, pins its tools, and CI tests it on Python 3.11 to 3.15.

## User Stories

1. As a caller, I want to return `Ok(value)` or `Err(error)` from a function annotated `Result[T, E]`, so that each caller sees the failure in the type.
2. As a caller, I want to return `Some(value)` or `Nothing()` from a function annotated `Option[T]`, so that an absent value differs from `Some(None)`.
3. As a caller, I want `match` on `Ok`/`Err` and `Some`/`Nothing` to narrow each branch, and `assert_never` to report a missing case, so that I handle every variant.
4. As a caller, I want `isinstance` and `if result:` to narrow both branches, so that a short check also gives the right type.
5. As a caller, I want `unwrap`, `expect`, `unwrap_or` and `unwrap_or_else`, so that I get the value, a default, or an `UnwrapError` that keeps the original exception.
6. As a caller, I want `map`, `map_err`, `and_then`, `or_else`, `flatten` and `transpose`, so that I change a value or an error without unpacking the variant.
7. As a caller, I want `ok`, `err`, `ok_or`, `ok_or_else`, `from_optional` and `to_optional`, so that I move between Option, Result and `T | None`.
8. As a caller, I want a do function in which `yield from result.try_()` returns early on an Err, so that I write the steps in order and the checker verifies the error union.
9. As a caller, I want `@catch(ValueError)` on a function that raises, so that its expected exceptions become an Err and every other exception propagates.
10. As a caller with a list of Results, I want `collect` and `partition`, so that I get all values or the first Err, or the values and the errors apart.
11. As a caller, I want `is_ok()`, `is_err()`, `is_some()` and `is_nothing()`, so that a call such as `filter(lambda result: result.is_ok(), results)` works.
12. As a caller, I want variants that compare, hash, print and pickle, so that they work in tests, sets, caches and multiprocessing.
13. As a caller who runs mypy, pyright, ty or pyrefly, I want the package's inline types, so that my checker needs no plugin and no config.
14. As a caller, I want to install the package from GitHub on Python 3.11 to 3.15, so that I can use it before any release.
15. As a reader of the repo, I want a README with install steps, one sample and the three narrowing styles, so that I can start without reading the code.
16. As a contributor, I want one pinned dev group, the pre-commit hook and CI on each PR, so that my change passes the same checks on every supported Python.

## Implementation Decisions

[option-and-result.md](option-and-result.md) is the design. Its API section holds the signatures, and its Key Decisions section holds each reason.

| Decision | Source |
|---|---|
| The package `oxide` (distribution `oxide.py`) has the private modules `_core`, `_do` and `_catch`, and `__init__` re-exports the 13 public names with `__all__`. | Key Decisions: Names, Modules |
| `Result` and `Option` are union aliases of four `@final` classes, and `value` and `error` are read-only properties over slots. | Key Decisions: Structure, Attributes |
| `Nothing()` returns one instance. | [adr/0002](adr/0002-nothing-is-a-final-class-singleton.md) |
| The methods are the set in the design's API section, and nothing outside it. | Key Decisions: Methods; [CLAUDE.md](../CLAUDE.md) |
| The documented narrowing styles are `match`, `isinstance` and `if result:`. Truthiness tests the variant, not the content. The `is_*()` methods return `bool` and narrow nothing. | Key Decisions: Narrowing styles, Query methods |
| A method call on a union resolves on both variants, so `result.and_then(function)` accumulates the error types. | design: API |
| A do function takes Results only, and an Option enters it through `ok_or`. `do` raises `TypeError` for a function that is not a generator function. | [adr/0001](adr/0001-do-function-with-try-replaces-question-mark.md); design: Do functions |
| `catch` takes 1 to 3 exception types bound to `Exception`, and raises `TypeError` for none, `Exception` or `BaseException`. | Key Decisions: `catch` |
| A failed unwrap raises `UnwrapError` with a Rust-style message, `from` the error when the error is an exception. There is no `Panic`. | design: Errors; Key Decisions: `UnwrapError`, Bugs |
| `collect` takes Results only. | Key Decisions: `collect` |
| The variants support `==`, `hash`, `repr` and default pickling, and have no `__iter__`. | design: Runtime behavior |
| The minimum Python is 3.11, with old TypeVar syntax, and `typing_extensions` is a dependency below 3.12 only. | Key Decisions: Minimum Python, Dependencies |
| The build backend is `hatchling` with a `src/oxide/` layout, `py.typed` and version `0.1.0`. | Key Decisions: Packaging |
| `[dependency-groups] dev` pins Ruff, pre-commit, pytest and the four checkers. Each install upgrades pip first, because `--group` needs pip 25.1. | design: Packaging and CI |
| `ci.yml` runs pytest on 3.11 to 3.15, and a `check` job runs pre-commit and the four checkers at target 3.11. | Key Decisions: CI |
| `CLAUDE.md` changes three lines: the status line, the dev-tools install line and the Ruff `rev` line. | design: Design Gate |

## Testing Decisions

- Each test imports from `oxide` only, never from a private module.
- `tests/test_result.py` and `tests/test_option.py` test each method on each variant, the `UnwrapError` messages and `raise from`, equality, hash, `repr`, pickle, and the `Nothing` instance.
- `tests/test_do.py` tests the early return on an Err, the Ok value at the end, the error union, and the `TypeError` for a function that is not a generator function.
- `tests/test_catch.py` tests the conversion of each listed type, the propagation of other exceptions, the kept signature, and the `TypeError` cases.
- `tests/test_narrowing.py` runs each documented style on Result and Option, and holds an `assert_type` in each branch. The checkers prove it statically, and pytest runs it.
- The four checkers report zero errors on `src/` and `tests/` at target 3.11. A committed negative case would break that rule, so the repo holds none. Each checker reports a missing `match` case and a wrong Err type.
- No test asserts the type of a lambda passed to a method on a union, because ty 0.0.95 types that lambda as `Unknown`.
- The repo has no prior tests. The design's Narrowing styles table is the reference for `test_narrowing.py`.

## Out of Scope

- A PyPI upload, a GitHub release and version `1.0.0`.
- Async variants, `Panic`, a pydantic extra, a benchmark and a migration guide from `rustedpy/result`.
- `sum`, `product`, ordering, `copy.replace` and iteration over a variant.
- `TypeIs` free functions, do functions for Option, and `collect` for Option.

## Further Notes

- The research doc "Designing a Rust-style Result/Option library for Python" stays untracked, so this spec names it without a link.
- Python 3.10 is past its end of life (2026-10-01). When 3.11 reaches its end of life on 2027-10-31, Ruff's `UP046` and `UP047` rules can move the code to PEP 695 syntax.
