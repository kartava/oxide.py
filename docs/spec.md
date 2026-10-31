# oxide.py — Spec

## Problem Statement

A Python developer who wants an absent value or an expected failure in a function's type has no library that works on every type checker. [`rustedpy/result`](https://github.com/rustedpy/result) is archived, and its `result.is_ok()` methods narrow nothing. `returns` needs a mypy plugin, so its pyright support is weaker. The developer cannot rely on `match` or `if` to narrow both branches on mypy, pyright, ty and pyrefly alike, and a library with one maintainer can stop at any release.

## Solution

The `oxide` package gives an Option (a Some or Nothing) and a Result (an Ok or an Err), in the terms of [CONTEXT.md](../CONTEXT.md). Each is a closed union, so `match` and `isinstance` narrow both branches on all four checkers, with no plugin and no config. A do function replaces Rust's `?`, and `@catch` turns the expected exceptions of a raising function into an Err. The codebase stays small, pins its tools, and CI tests it on Python 3.11 to 3.15. PyPI serves each version, so a caller pins one.

## User Stories

1. As a caller, I want to return `Ok(value)` or `Err(error)` from a function annotated `Result[T, E]`, so that each caller sees the failure in the type.
2. As a caller, I want to return `Some(value)` or `Nothing()` from a function annotated `Option[T]`, so that an absent value differs from `Some(None)`.
3. As a caller, I want `match` on `Ok`/`Err` and `Some`/`Nothing` to narrow each branch, and `assert_never` to report a missing case, so that I handle every variant.
4. As a caller, I want `isinstance` to narrow both branches and `bool()` on a variant to raise, so that a one-line `isinstance` gives the right type and `if result:` cannot hide a bug.
5. As a caller, I want `unwrap`, `expect`, `unwrap_or` and `unwrap_or_else`, so that I get the value, a default, or an `UnwrapError` that keeps the original exception.
6. As a caller, I want `map`, `map_err`, `and_then`, `or_else`, `flatten` and `transpose`, so that I change a value or an error without unpacking the variant.
7. As a caller, I want `ok`, `err`, `ok_or`, `ok_or_else`, `from_optional` and `to_optional`, so that I move between Option, Result and `T | None`.
8. As a caller, I want a do function in which `yield from result.try_()` returns early on an Err, so that I write the steps in order and the checker verifies the error union.
9. As a caller, I want `@catch(ValueError)` on a function that raises, so that its expected exceptions become an Err and every other exception propagates.
10. As a caller with a list of Results, I want `collect` and `partition`, so that I get all values or the first Err, or the values and the errors apart.
11. As a caller, I want `is_ok()`, `is_err()`, `is_some()` and `is_nothing()`, so that a call such as `filter(lambda result: result.is_ok(), results)` works.
12. As a caller, I want variants that compare, hash, print and pickle, so that they work in tests, sets, caches and multiprocessing.
13. As a caller who runs mypy, pyright, ty or pyrefly, I want the package's inline types, so that my checker needs no plugin and no config.
14. As a caller, I want to install a pinned version from PyPI on Python 3.11 to 3.15, so that a new commit on `main` cannot change my code.
15. As a reader of the repo, I want a README with install steps, one sample and the two narrowing styles, so that I can start without reading the code.
16. As a contributor, I want one pinned dev group, the pre-commit hook and CI on each PR, so that my change passes the same checks on every supported Python.
17. As a user of [`rustedpy/result`](https://github.com/rustedpy/result), I want a README table that maps its API to `oxide`, so that I can migrate my code.
18. As a caller, I want a GitHub release for each version, with notes and the sdist and the wheel, so that I see what changed before I upgrade.
19. As the maintainer, I want a tag push to build, upload and release a version after my approval, so that each release runs the same steps and no wrong version reaches PyPI.

## Implementation Decisions

[option-and-result.md](option-and-result.md) is the design. Its API section holds the signatures, and its Key Decisions section holds each reason.

| Decision | Source |
|---|---|
| The package `oxide` (distribution `oxide.py`) has the private modules `_core`, `_do` and `_catch`, and `__init__` re-exports the 13 public names with `__all__`. | Key Decisions: Names, Modules |
| `Result` and `Option` are union aliases of four `@final` classes, and `value` and `error` are read-only properties over slots. | Key Decisions: Structure, Attributes |
| `Nothing()` returns one instance. | [adr/0002](adr/0002-nothing-is-a-final-class-singleton.md) |
| The methods are the set in the design's API section, and nothing outside it. | Key Decisions: Methods; [CLAUDE.md](../CLAUDE.md) |
| The documented narrowing styles are `match` and `isinstance`. A variant has no truth value: `bool()` raises `TypeError`. The `is_*()` methods return `bool` and narrow nothing. | Key Decisions: Narrowing styles, Query methods; [adr/0003](adr/0003-variants-have-no-truth-value.md) |
| A method call on a union resolves on both variants, so `result.and_then(function)` accumulates the error types. | design: API |
| A do function takes Results only, and an Option enters it through `ok_or`. `do` raises `TypeError` for a function that is not a generator function, and for a yield of a value other than an Err. | [adr/0001](adr/0001-do-function-with-try-replaces-question-mark.md); design: Do functions; Key Decisions: Runtime checks |
| `catch` takes 1 to 3 exception types bound to `Exception`, and raises `TypeError` for none, for `Exception`, and for a value that is not a subclass of `Exception`. | Key Decisions: `catch`, Runtime checks |
| A failed unwrap raises `UnwrapError` with a Rust-style message, `from` the error when the error is an exception. There is no `Panic`. | design: Errors; Key Decisions: `UnwrapError`, Bugs |
| `collect` takes Results only. | Key Decisions: `collect` |
| The variants support `==`, `hash`, `repr` and pickle protocol 2 or later, and have no `__iter__`. `Nothing` stays one instance at every protocol. | design: Runtime behavior |
| The minimum Python is 3.11, with old TypeVar syntax, and `typing_extensions` is a dependency below 3.12 only. | Key Decisions: Minimum Python, Dependencies |
| The build backend is `hatchling` with a `src/oxide/` layout and `py.typed`. | Key Decisions: Packaging |
| Only `pyproject.toml` names the version. The metadata adds `description`, `authors`, the classifiers and three URLs, and the sdist holds `src/` and `tests/`. | [release.md](release.md), Key Decisions: Version source, Version in docs, Metadata, sdist content |
| A push of a `v*` tag runs `release.yml`. `build` stops when the tag is not `v` + `version`, then builds the sdist and the wheel. `publish` uploads them through trusted publishing, after the maintainer approves in environment `pypi`. `github-release` then creates the release with generated notes and both files. | [release.md](release.md), Key Decisions: Trigger, Upload, Approval, Tag check, GitHub release |
| The README installs with `pip install oxide.py`, and links to the narrowing tests by an absolute URL. | [release.md](release.md), Key Decisions: README test link |
| `[dependency-groups] dev` pins Ruff, pre-commit, pytest and the four checkers. Each install upgrades pip first, because `--group` needs pip 25.1. | design: Packaging and CI |
| `ci.yml` imports `oxide` from a venv with only the package and runs pytest on 3.11 to 3.15, and a `check` job runs pre-commit and the four checkers at target 3.11. | Key Decisions: CI |
| `CLAUDE.md` changes the status line, the commands and the hook pin rule. | design: Design Gate |

## Testing Decisions

- Each test imports from `oxide` only, never from a private module.
- `tests/test_result.py` and `tests/test_option.py` test each method on each variant, the `UnwrapError` messages and `raise from`, equality, hash, `repr`, pickle, the `TypeError` from `bool()`, and the `Nothing` instance.
- `tests/test_do.py` tests the early return on an Err, the Ok value at the end, the error union, the `TypeError` for a function that is not a generator function and for a yield of a value other than an Err, and the `RuntimeError` of `try_()` after an Err.
- `tests/test_catch.py` tests the conversion of each listed type, the propagation of other exceptions, the kept signature, and the `TypeError` cases.
- `tests/test_narrowing.py` runs each documented style on Result and Option, and holds an `assert_type` in each branch. It also proves that `is_ok()` narrows nothing. The checkers prove it statically, and pytest runs it.
- The four checkers report zero errors on `src/` and `tests/` at target 3.11, so the repo holds no committed negative case.
- No test asserts the type of a lambda passed to a method on a union, because ty 0.0.95 types that lambda as `Unknown`.
- The design's Narrowing styles table is the reference for `test_narrowing.py`.
- `release.yml` has no test step. Its checks are the tag check and the build of the wheel from the sdist, and `ci.yml` tests the tagged commit ([release.md](release.md), Key Decisions: Tests in `release.yml`).
- After each release, a check by hand installs the pinned version from PyPI in a new venv and imports `oxide`.

## Out of Scope

- Async variants, `Panic`, a pydantic extra and a benchmark.
- `sum`, `product`, ordering, `copy.replace` and iteration over a variant.
- `TypeIs` free functions, do functions for Option, and `collect` for Option.
