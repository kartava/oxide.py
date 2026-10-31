# Option and Result — Design

## Context

`oxide.py` v1 ports Rust's `Option<T>` and `Result<T, E>` to Python as the `oxide` package. A function returns an Option or a Result, so that an absent value or an expected failure is part of its type, and a type checker forces the caller to handle it. The design beats the existing libraries on three points from the research doc "Designing a Rust-style Result/Option library for Python": narrowing that each of four checkers proves in both branches, no checker plugin, and a small, pinned and CI-tested codebase. Library callers use it; v1 ends merged on `main`, before any release.

## Constraints

- Ruff checks `src/` and `tests/` at 79 columns: annotations on every signature, PEP 257 docstrings, PEP 8 names, the `_co` suffix on a covariant TypeVar, and absolute imports ([python.md](conventions/python.md)).
- A keyword name takes a trailing underscore, and each public module sets `__all__` ([python.md](conventions/python.md)). A public item has a docstring when it carries a fact that its name and signature do not ([comments.md](conventions/comments.md)).
- The terms are those of [CONTEXT.md](../CONTEXT.md). A Some can hold `None`, and an Err holds any value.
- Each picked checker reports zero errors on the package and the tests, with no plugin and no library-specific config on the caller's side ([CLAUDE.md](../CLAUDE.md)).
- Python 3.10 is past its end of life (2026-10-01). Python 3.11 is the oldest supported version, until 2027-10-31.
- A covariant TypeVar cannot be a method parameter on any of the four checkers. A method that takes a value of the content type uses a second TypeVar.
- ty 0.0.95 infers a lambda passed to a method on a union as `Unknown`, with no error. The tests assert no lambda result on a union.
- ty 0.0.95 types a string literal argument as its `Literal` type, so `assert_type(option.ok_or("x"), Err[str])` fails on ty. The tests assert no type of a literal argument.

## Architecture

One package and one glossary. `_core` imports nothing from the package; `_do` and `_catch` import `_core`.

```
src/oxide/
  __init__.py   re-exports the public names, sets __all__
  _core.py      Ok, Err, Some, Nothing, Result, Option, UnwrapError,
                collect, partition, from_optional
  _do.py        do, Do
  _catch.py     catch
  py.typed
tests/
  test_result.py
  test_option.py
  test_do.py
  test_catch.py
  test_narrowing.py
.github/workflows/ci.yml
README.md
```

## Design Gate

| Piece | Kind | Consumer today | Derived from | Change vs base |
|---|---|---|---|---|
| `Ok`, `Err` | public class | callers, the README sample, `tests/` | — | new |
| `Some`, `Nothing` | public class | callers, `tests/` | — | new |
| `Result`, `Option` | type alias | caller annotations | the variant classes | new |
| `Do` | type alias | do function annotations | `Generator`, `Err` | new |
| `UnwrapError` | exception | callers that catch a failed unwrap | — | new |
| `collect`, `partition` | function | callers with a list of Results | — | new |
| `from_optional` | function | callers that hold a `T \| None` | — | new |
| `do` | decorator | do functions, the README sample | — | new |
| `catch` | decorator | functions that raise expected exceptions, the README sample | — | new |
| `py.typed` | marker | the type checkers of callers | — | new |
| `[project]`, `[build-system]`, `[dependency-groups]`, checker settings | `pyproject.toml` | `pip install`, CI, contributors | — | added next to `[tool.ruff]` |
| `ci.yml` | CI workflow | each PR and each push to `main` | — | new |
| `README.md` | doc | repo readers; `tests/test_narrowing.py` proves its styles | — | new |
| The status line, the dev-tools install line and the Ruff `rev` line | `CLAUDE.md` | contributors | `[dependency-groups]` | changed |

New public names: 13. New files: 12. Changed files: `pyproject.toml`, `CLAUDE.md`. The counts are against the effort branch: its first commit, `3d70fd0`, adds `pyproject.toml`, `CLAUDE.md`, `.pre-commit-config.yaml`, `.gitignore` and `docs/conventions/`, which are new against `main` too.

Cut review: done 2026-10-31

## API

The variants are `@final` generic classes with `__slots__`. `T_co` and `E_co` are covariant. `U`, `F` and `D` are plain TypeVars.

```python
@final
class Ok(Generic[T_co]):
    __match_args__ = ("value",)

    def __init__(self, value: T_co) -> None: ...
    @property
    def value(self) -> T_co: ...
    def is_ok(self) -> bool: ...
    def is_err(self) -> bool: ...
    def expect(self, message: str) -> T_co: ...
    def expect_err(self, message: str) -> Never: ...
    def unwrap(self) -> T_co: ...
    def unwrap_err(self) -> Never: ...
    def unwrap_or(self, default: object) -> T_co: ...
    def unwrap_or_else(self, function: Callable[[Never], object]) -> T_co: ...
    def map(self, function: Callable[[T_co], U]) -> Ok[U]: ...
    def map_err(self, function: Callable[[Never], object]) -> Ok[T_co]: ...
    def and_then(
        self, function: Callable[[T_co], Result[U, F]]
    ) -> Result[U, F]: ...
    def or_else(self, function: Callable[[Never], object]) -> Ok[T_co]: ...
    def ok(self) -> Some[T_co]: ...
    def err(self) -> Nothing: ...
    def flatten(self: Ok[Result[U, F]]) -> Result[U, F]: ...
    def transpose(self: Ok[Option[U]]) -> Option[Ok[U]]: ...
    def try_(self) -> Generator[Never, Any, T_co]: ...
    def __bool__(self) -> Literal[True]: ...


@final
class Err(Generic[E_co]):
    __match_args__ = ("error",)

    def __init__(self, error: E_co) -> None: ...
    @property
    def error(self) -> E_co: ...
    def is_ok(self) -> bool: ...
    def is_err(self) -> bool: ...
    def expect(self, message: str) -> Never: ...
    def expect_err(self, message: str) -> E_co: ...
    def unwrap(self) -> Never: ...
    def unwrap_err(self) -> E_co: ...
    def unwrap_or(self, default: D) -> D: ...
    def unwrap_or_else(self, function: Callable[[E_co], D]) -> D: ...
    def map(self, function: Callable[[Never], object]) -> Err[E_co]: ...
    def map_err(self, function: Callable[[E_co], F]) -> Err[F]: ...
    def and_then(self, function: Callable[[Never], object]) -> Err[E_co]: ...
    def or_else(
        self, function: Callable[[E_co], Result[U, F]]
    ) -> Result[U, F]: ...
    def ok(self) -> Nothing: ...
    def err(self) -> Some[E_co]: ...
    def flatten(self) -> Err[E_co]: ...
    def transpose(self) -> Some[Err[E_co]]: ...
    def try_(self) -> Generator[Err[E_co], Any, Never]: ...
    def __bool__(self) -> Literal[False]: ...
```

```python
@final
class Some(Generic[T_co]):
    __match_args__ = ("value",)

    def __init__(self, value: T_co) -> None: ...
    @property
    def value(self) -> T_co: ...
    def is_some(self) -> bool: ...
    def is_nothing(self) -> bool: ...
    def expect(self, message: str) -> T_co: ...
    def unwrap(self) -> T_co: ...
    def unwrap_or(self, default: object) -> T_co: ...
    def unwrap_or_else(self, function: Callable[[], object]) -> T_co: ...
    def map(self, function: Callable[[T_co], U]) -> Some[U]: ...
    def and_then(self, function: Callable[[T_co], Option[U]]) -> Option[U]: ...
    def or_else(self, function: Callable[[], object]) -> Some[T_co]: ...
    def ok_or(self, error: object) -> Ok[T_co]: ...
    def ok_or_else(self, function: Callable[[], object]) -> Ok[T_co]: ...
    def flatten(self: Some[Option[U]]) -> Option[U]: ...
    def transpose(self: Some[Result[U, F]]) -> Result[Some[U], F]: ...
    def to_optional(self) -> T_co: ...
    def __bool__(self) -> Literal[True]: ...


@final
class Nothing:
    def __new__(cls) -> Nothing: ...
    def is_some(self) -> bool: ...
    def is_nothing(self) -> bool: ...
    def expect(self, message: str) -> Never: ...
    def unwrap(self) -> Never: ...
    def unwrap_or(self, default: D) -> D: ...
    def unwrap_or_else(self, function: Callable[[], D]) -> D: ...
    def map(self, function: Callable[[Never], object]) -> Nothing: ...
    def and_then(self, function: Callable[[Never], object]) -> Nothing: ...
    def or_else(self, function: Callable[[], Option[U]]) -> Option[U]: ...
    def ok_or(self, error: F) -> Err[F]: ...
    def ok_or_else(self, function: Callable[[], F]) -> Err[F]: ...
    def flatten(self) -> Nothing: ...
    def transpose(self) -> Ok[Nothing]: ...
    def to_optional(self) -> None: ...
    def __bool__(self) -> Literal[False]: ...
```

```python
Result: TypeAlias = Ok[T] | Err[E]
Option: TypeAlias = Some[T] | Nothing
Do = TypeAliasType("Do", Generator[Err[E], Any, T], type_params=(T, E))


class UnwrapError(Exception): ...


def collect(items: Iterable[Result[T, E]]) -> Result[list[T], E]: ...
def partition(items: Iterable[Result[T, E]]) -> tuple[list[T], list[E]]: ...
def from_optional(value: T | None) -> Option[T]: ...
def do(
    function: Callable[P, Generator[Err[E], Any, T]],
) -> Callable[P, Result[T, E]]: ...
@overload
def catch(
    exception_1: type[X1], /
) -> Callable[[Callable[P, R]], Callable[P, Result[R, X1]]]: ...
@overload
def catch(
    exception_1: type[X1], exception_2: type[X2], /
) -> Callable[[Callable[P, R]], Callable[P, Result[R, X1 | X2]]]: ...
@overload
def catch(
    exception_1: type[X1], exception_2: type[X2], exception_3: type[X3], /
) -> Callable[[Callable[P, R]], Callable[P, Result[R, X1 | X2 | X3]]]: ...
```

`X1`, `X2` and `X3` are bound to `Exception`. On a union such as `Result[int, str]`, each method call resolves on both variants: `result.unwrap()` is `int`, and `result.and_then(function)` accumulates the error types, `Err[str] | Err[ValueError]`.

```python
from oxide import Do, Err, Ok, Result, catch, do


@catch(ValueError)
def parse_port(text: str) -> int:
    return int(text)


def check_range(port: int) -> Result[int, str]:
    return Ok(port) if 0 < port < 65_536 else Err(f"out of range: {port}")


@do
def load_port(text: str) -> Do[int, ValueError | str]:
    port = yield from parse_port(text).try_()
    return (yield from check_range(port).try_())


match load_port("8080"):
    case Ok(port):
        print(port)
    case Err(error):
        print(error)
```

## Narrowing styles

`README.md` lists these three styles, and `tests/test_narrowing.py` proves each one in both branches, on Result and Option, at runtime and on each of the four checkers.

| Style | Result | Option |
|---|---|---|
| `match`, the primary style | `case Ok(value):`, `case Err(error):`, then `assert_never` | `case Some(value):`, `case Nothing():`, then `assert_never` |
| `isinstance` | `isinstance(result, Ok)` | `isinstance(option, Some)` |
| Truthiness | `if result:` | `if option:` |

`is_ok()`, `is_err()`, `is_some()` and `is_nothing()` return `bool` and narrow nothing. A method cannot narrow its own `self` (PEP 742), and the README says so. Truthiness tests the variant, not the content: `Some(0)`, `Some(None)` and `Ok([])` are true, and the README says so too.

## Do functions

A do function replaces Rust's `?` ([adr/0001](adr/0001-do-function-with-try-replaces-question-mark.md)). Do functions take Results only: an Option converts first with `ok_or`. `do` raises `TypeError` when it decorates a function that is not a generator function.

```mermaid
sequenceDiagram
    participant C as Caller
    participant W as do wrapper
    participant G as Do function
    C->>W: load_port("x")
    W->>G: start the generator
    G->>G: parse_port(text).try_()
    alt the step is an Ok
        G->>G: take the value, run the next step
        G-->>W: return value (StopIteration)
        W-->>C: Ok(value)
    else the step is an Err
        G-->>W: yield the Err
        W->>G: close()
        W-->>C: the Err
    end
```

## Errors

`unwrap`, `expect`, `unwrap_err` and `expect_err` raise `UnwrapError` on the other variant. When the error is an exception, they raise `from` it, so the traceback keeps the original exception.

| Call | On | Message |
|---|---|---|
| `unwrap()` | `Err` | ``called `Result.unwrap()` on an `Err` value: {error!r}`` |
| `expect(message)` | `Err` | `{message}: {error!r}` |
| `unwrap_err()` | `Ok` | ``called `Result.unwrap_err()` on an `Ok` value: {value!r}`` |
| `expect_err(message)` | `Ok` | `{message}: {value!r}` |
| `unwrap()` | `Nothing` | ``called `Option.unwrap()` on a `Nothing` value`` |
| `expect(message)` | `Nothing` | `{message}` |

`catch` raises `TypeError` at decoration time when it gets no exception type, or `Exception` or `BaseException`. Inside the decorated function, an exception of a listed type becomes an Err, even when a bug raised it. Each other exception propagates unchanged, and so does each exception that a callback raises outside `catch`.

## Runtime behavior

| Behavior | Rule |
|---|---|
| Immutability | `__slots__` and read-only properties: an assignment to `value`, `error` or a new attribute raises `AttributeError`. |
| Equality | The same variant class and equal content: `Ok(1) == Ok(1)`, `Ok(1) != Some(1)`. |
| Hash | The hash of the variant class and its content. Unhashable content makes the variant unhashable. |
| `repr` | `Ok(1)`, `Err('empty')`, `Some(None)`, `Nothing()`. |
| Pickle and copy | Default pickling and `copy.deepcopy` work on the slots. Both rebuild through `__new__`, so `Nothing` keeps one instance. |
| Iteration | None: the variants have no `__iter__`. |

## Packaging and CI

```toml
[project]
name = "oxide.py"
version = "0.1.0"
requires-python = ">=3.11"
license = "MIT"
readme = "README.md"
dependencies = ['typing_extensions>=4.6; python_version < "3.12"']

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/oxide"]

[dependency-groups]
dev = [
    "ruff==0.17.3",
    "pre-commit==4.7.0",
    "pytest==9.2.0",
    "mypy==2.4.1",
    "pyright==1.1.414",
    "ty==0.0.95",
    "pyrefly==1.4.0",
]
```

`packages` is needed because the distribution name `oxide.py` differs from the import name `oxide`. `typing_extensions` supplies `TypeAliasType` below 3.12 only.

| Checker | Mode | Target | Paths |
|---|---|---|---|
| mypy | `strict` | 3.11 | `src`, `tests` |
| pyright | `strict` | 3.11 | `src`, `tests` |
| ty | default | 3.11 | `src`, `tests` |
| pyrefly | default | 3.11 | `src`, `tests` |

The checker settings live in `pyproject.toml`. `--group` needs pip 25.1 or later, and Python 3.11 and 3.12 bundle pip 24.2, so each install upgrades pip first. `ci.yml` runs on each PR and each push to `main`:

| Job | Python | Steps |
|---|---|---|
| `test` | 3.11, 3.12, 3.13, 3.14, 3.15 | Create `.venv`, run `pip install -U pip`, install `-e . --group dev`, run pytest. |
| `check` | 3.14 | Install the same way, run `pre-commit run --all-files`, then the four checkers. |

## Key Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Names | Distribution `oxide.py`, import `oxide` | It matches the repo, and `oxide-py` is free on PyPI. **`oxide_py` import.** Rejected: it reads worse in `from … import`. |
| Structure | Union aliases of `@final` classes | Only a closed union makes `match` with `assert_never` exhaustive on all four checkers. **A base class.** Rejected: it leaves the union open. |
| Attributes | Read-only `value` and `error` properties over slots | A property keeps the class covariant; under PEP 695 a plain attribute is invariant on all four checkers. |
| Nothing | `Nothing()`, one instance | [adr/0002](adr/0002-nothing-is-a-final-class-singleton.md). |
| Query methods | `is_ok()`, `is_err()`, `is_some()`, `is_nothing()`, returning `bool` | They keep Rust's names for calls such as `filter(lambda result: result.is_ok(), results)`, and the README says that they narrow nothing. **Rust's `is_none()`.** Rejected: it reads as a check for Python's `None`. |
| Methods | The extract, transform, collect and convert set in API | The research doc's Implement list sets the v1 scope: `map`, `and_then`, the `unwrap` family, `ok`, `err`, `collect`, `partition`, `transpose`, `flatten`, `from_optional`, `to_optional`. `expect`, `expect_err`, `map_err`, `or_else`, `ok_or` and `ok_or_else` complete Rust's pairs. **All portable Rust methods.** Rejected: twice the size, with no v1 caller for the rest. |
| `collect` | Results only | On an empty input, the runtime cannot choose between `Ok([])` and `Some([])`. **One overloaded `collect` for both types.** Rejected: an empty list of Options returns the wrong variant. |
| Narrowing styles | `match`, `isinstance`, truthiness | Each narrows both branches on all four checkers. **`TypeIs` free functions.** Rejected: they repeat `isinstance`. **No `__bool__`.** Rejected: `if parse(text):` would then always be true. |
| `?` substitute | Do functions with `try_()`, Results only | [adr/0001](adr/0001-do-function-with-try-replaces-question-mark.md). An Option converts with `ok_or`, which keeps one `Do` alias. |
| Bugs | No `Panic`; `UnwrapError` for a failed unwrap | Python already propagates each callback exception. **better-result's `Panic`.** Rejected: it wraps every callback to cover one case inside `catch`. |
| `catch` | 1 to 3 exception types, bound to `Exception`; `TypeError` for `Exception` and `BaseException` | It converts expected exceptions only. **One `*exceptions` signature.** Rejected: mypy widens the union to a common base class. |
| `UnwrapError` | No extra attributes; Rust messages with `repr`; `raise from` | No v1 caller reads the variant from the exception, and `raise from` keeps the original traceback. |
| Docstrings | A public item that carries a fact its name and signature do not: what the call does in each case, what it raises, or a trap | An editor's hover and `help()` are the in-editor docs of a library, and an obvious docstring adds only noise. Ruff checks the form, not the presence: its `D1` rules skip `_` modules. **A docstring on every public item.** Rejected: `value` and `is_ok()` would restate their names. |
| Runtime | `__slots__`, read-only properties, `==`, `hash`, `repr`, default pickling | Pickle has users in multiprocessing and caches. Without `__hash__`, `__eq__` makes every variant unhashable. **Ordering and `copy.replace`.** Rejected: no v1 caller. **A raising `__setattr__` with `__reduce__`.** Rejected: slots and read-only properties already block public writes, and default pickling works. |
| Async | None in v1 | It would double the API surface. |
| Cuts | No pydantic extra, benchmark, migration guide, `sum` or `product` | None has a user before a release. The migration guide fits the release effort. |
| Minimum Python | 3.11, old TypeVar syntax | It reaches the most users. Ruff's `UP046` and `UP047` move the code to PEP 695 when 3.11 reaches end of life. **3.12 or 3.13.** Rejected: they drop 3.11 a year early. |
| Dependencies | `typing_extensions` below 3.12 only | `TypeAliasType` is the only feature that 3.11 lacks. |
| Checkers | mypy, pyright, ty, pyrefly, each with an exact pin | Proof on all four is the narrowing point. Exact pins keep a new release of ty, which is pre-1.0, out of CI. |
| Tests | Plain pytest; `tests/test_narrowing.py` holds the `assert_type` proofs | Narrowing is a static check, and one file proves each style at runtime and statically. **Gherkin.** Rejected: its steps check runtime behavior only. |
| CI | pytest on 3.11 to 3.15; one `check` job targeting 3.11 | All four checkers gave the same result at 3.11 and 3.14. CI is the only test path below the `.venv` version. |
| Packaging | `hatchling`, `src/oxide/`, `py.typed`, `0.1.0` | The README install step and CI need a build backend. `0.1.0` leaves `1.0.0` to the release effort. |
| Dev tools | `[dependency-groups] dev` with exact pins | One list serves CI, contributors and `.venv`. |
| Modules | `_core`, `_do` and `_catch`, re-exported from `__init__` | Option and Result call each other, so they share `_core`, and no import is circular. |
| README | Install steps, one usage sample, the three styles | The narrowing tests prove the styles that it lists. |

## Unresolved Questions

None outstanding.
