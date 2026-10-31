# oxide.py

[Rust](https://www.rust-lang.org)'s `Option<T>` and `Result<T, E>`, implemented for Python. A function returns one of them, so that an absent value or an expected failure is part of its type.

- `match`, `isinstance` and `if result:` narrow both branches on mypy, pyright, ty and pyrefly.
- No type-checker plugin and no config.
- No dependencies from Python 3.12. Python 3.11 needs `typing_extensions`.

## Installation

The package needs Python 3.11 or later, and imports as `oxide`.

```sh
pip install git+https://github.com/kartava/oxide.py
```

## Usage

### Core features

- [Importing](#importing)
- [Quick start](#quick-start)
- [Option](#option)
- [Result](#result)
- [Narrowing](#narrowing)
- [Chaining](#chaining)
- [Converting](#converting)
- [Nesting](#nesting)
- [Collections](#collections)

### Advanced

- [Catching exceptions](#catching-exceptions)
- [Do functions](#do-functions)
- [Unwrap errors](#unwrap-errors)

## Importing

Every public name comes from the package root:

```python
from oxide import (
    Do,
    Err,
    Nothing,
    Ok,
    Option,
    Result,
    Some,
    UnwrapError,
    catch,
    collect,
    do,
    from_optional,
    partition,
)
```

[Back to contents](#usage)

## Quick start

A function returns `Ok(value)` on success, or `Err(error)` on an expected failure. The caller handles both with `match`.

```python
from oxide import Err, Ok, Result


def parse_port(text: str) -> Result[int, str]:
    if not text.isdigit():
        return Err(f"not a number: {text}")
    return Ok(int(text))


match parse_port("8080"):
    case Ok(port):
        print(f"port {port}")
    case Err(error):
        print(f"error: {error}")
```

The sample prints `port 8080`. For `"x"` it prints `error: not a number: x`. A type checker knows that `port` is an `int` and `error` is a `str`.

[Back to contents](#usage)

## Option

An Option is either `Some(value)` or `Nothing()`. Both variants have the same methods, so you can chain calls before you take the value out.

```python
from oxide import Nothing, Option, Some


def divide(number: float, divisor: float) -> Option[float]:
    return Nothing() if divisor == 0 else Some(number / divisor)


assert divide(100, 20).unwrap() == 5.0
assert divide(100, 20).expect("the divisor is zero") == 5.0
assert divide(100, 0).unwrap_or(1.0) == 1.0
assert divide(100, 20).map(str) == Some("5.0")
assert divide(100, 0).map(str) == Nothing()
```

- `unwrap()` and `expect(message)` raise `UnwrapError` on `Nothing`.
- A `Some` can hold `None`: `Some(None)` is a `Some`, not `Nothing`.
- `Nothing()` always returns the same instance.

[Back to contents](#usage)

## Result

A Result is either `Ok(value)` or `Err(error)`. An `Err` holds an expected failure: a string, an enum member or an exception.

```python
from oxide import Err, Ok, Result


def divide(number: float, divisor: float) -> Result[float, str]:
    if divisor == 0:
        return Err("division by zero")
    return Ok(number / divisor)


assert divide(100, 20).unwrap() == 5.0
assert divide(100, 0).unwrap_or(1.0) == 1.0
assert divide(100, 0).unwrap_err() == "division by zero"
assert divide(100, 20).map(round) == Ok(5)
assert divide(100, 0).map_err(len) == Err(16)
```

- `unwrap()` and `expect(message)` raise `UnwrapError` on an `Err`.
- `unwrap_err()` and `expect_err(message)` raise `UnwrapError` on an `Ok`.

[Back to contents](#usage)

## Narrowing

Each style narrows both branches of a Result and an Option on mypy, pyright, ty and pyrefly. [tests/test_narrowing.py](tests/test_narrowing.py) proves each one.

### `match`

The primary style. `assert_never` in `case _:` makes a type checker report a missing variant.

```python
from typing import assert_never

from oxide import Err, Nothing, Ok, Option, Result, Some


def describe(result: Result[int, str]) -> str:
    match result:
        case Ok(value):
            return f"value {value}"
        case Err(error):
            return f"error {error}"
        case _:
            assert_never(result)


def describe_option(option: Option[int]) -> str:
    match option:
        case Some(value):
            return f"value {value}"
        case Nothing():
            return "nothing"
        case _:
            assert_never(option)
```

### `isinstance`

```python
from oxide import Ok, Option, Result, Some


def describe(result: Result[int, str]) -> str:
    if isinstance(result, Ok):
        return f"value {result.value}"
    return f"error {result.error}"


def describe_option(option: Option[int]) -> str:
    if isinstance(option, Some):
        return f"value {option.value}"
    return "nothing"
```

### Truthiness

`Ok` and `Some` are true, and `Err` and `Nothing` are false. Truthiness tests the variant, not the content: `Some(0)`, `Some(None)` and `Ok([])` are true.

```python
from oxide import Option, Result


def describe(result: Result[int, str]) -> str:
    if result:
        return f"value {result.value}"
    return f"error {result.error}"


def describe_option(option: Option[int]) -> str:
    if option:
        return f"value {option.value}"
    return "nothing"
```

### Query methods

`is_ok()`, `is_err()`, `is_some()` and `is_nothing()` return `bool` and narrow nothing: a method cannot narrow its own `self` ([PEP 742](https://peps.python.org/pep-0742/)). After `if result.is_ok():`, `result` stays a `Result[int, str]`. Use them where a `bool` is enough, as in `filter(lambda result: result.is_ok(), results)`.

[Back to contents](#usage)

## Chaining

`and_then` runs the next step on an `Ok`, and `or_else` recovers from an `Err`. Each callback runs on its own variant only.

```python
from oxide import Err, Ok, Result


def parse(text: str) -> Result[int, str]:
    return Ok(int(text)) if text.isdigit() else Err(f"not a number: {text}")


def check_port(number: int) -> Result[int, str]:
    if 0 < number < 65_536:
        return Ok(number)
    return Err(f"out of range: {number}")


def default_port(error: str) -> Result[int, str]:
    return Ok(80)


assert parse("8080").and_then(check_port) == Ok(8080)
assert parse("70000").and_then(check_port) == Err("out of range: 70000")
assert parse("x").and_then(check_port) == Err("not a number: x")
assert parse("x").or_else(default_port) == Ok(80)
```

`and_then` keeps every error type. On a `Result[int, str]`, `and_then` with a function that returns `Result[float, ValueError]` gives a `Result[float, str | ValueError]`. Option has `map`, `and_then` and `or_else` too.

[Back to contents](#usage)

## Converting

```python
from oxide import Err, Nothing, Ok, Some, from_optional

assert from_optional(None) == Nothing()
assert from_optional(0) == Some(0)
assert Some(8080).to_optional() == 8080

assert Ok(8080).ok() == Some(8080)
assert Err("closed").ok() == Nothing()
assert Err("closed").err() == Some("closed")

assert Some(8080).ok_or("no port") == Ok(8080)
assert Nothing().ok_or("no port") == Err("no port")
```

`Nothing().to_optional()` is `None`. So is `Some(None).to_optional()`, because a `T | None` cannot tell `Some(None)` from `Nothing()`. `ok_or_else` builds the error with a function, only for `Nothing`.

[Back to contents](#usage)

## Nesting

A Result can hold an Option, so a search can tell "found", "found nothing" and "failed" apart. `match` reads the nested variants in one pattern.

```python
from oxide import Err, Nothing, Ok, Option, Result, Some


def search(query: str) -> Result[Option[int], str]:
    if not query:
        return Err("empty query")
    return Ok(Some(len(query)) if query.isalpha() else Nothing())


def describe(query: str) -> str:
    match search(query):
        case Ok(Some(count)):
            return f"found {count} entries"
        case Err(error):
            return f"error: {error}"
        case _:
            return "no results"


assert describe("ports") == "found 5 entries"
assert describe("8080") == "no results"
assert describe("") == "error: empty query"
```

`transpose` swaps the two layers, and `flatten` removes one:

```python
from oxide import Err, Nothing, Ok, Some

assert Ok(Some(5)).transpose() == Some(Ok(5))
assert Ok(Nothing()).transpose() == Nothing()
assert Some(Some(5)).flatten() == Some(5)
assert Ok(Err("closed")).flatten() == Err("closed")
```

[Back to contents](#usage)

## Collections

`collect` gives all the values, or the first `Err`. `partition` keeps every value and every error, in input order.

```python
from oxide import Err, Ok, Result, collect, partition

results: list[Result[int, str]] = [Ok(1), Err("x"), Ok(2), Err("y")]

assert collect([Ok(1), Ok(2)]) == Ok([1, 2])
assert collect(results) == Err("x")
assert partition(results) == ([1, 2], ["x", "y"])
```

[Back to contents](#usage)

## Catching exceptions

`@catch` turns the listed exceptions of a function into an `Err`. Every other exception propagates unchanged.

```python
from oxide import Ok, Result, catch


@catch(KeyError, ValueError)
def price(name: str, count: str) -> int:
    return {"apple": 3}[name] * int(count)


assert price("apple", "2") == Ok(6)
assert isinstance(price("pear", "2").unwrap_err(), KeyError)
assert isinstance(price("apple", "x").unwrap_err(), ValueError)

checked: Result[int, KeyError | ValueError] = price("apple", "2")
```

- `catch` takes one to three exception types, and the `Err` type is their union.
- `catch()`, `catch(Exception)` and `catch(BaseException)` raise `TypeError`: `catch` converts expected exceptions only.
- Inside the decorated function, a listed exception becomes an `Err` even when a bug raised it.

[Back to contents](#usage)

## Do functions

A function that runs several steps must stop at the first `Err`. Here are three ways to write the same `load_port`:

- `load_port_by_hand` checks each step and returns the `Err` early.
- `load_port_chained` passes the value of each step to the next with `and_then`.
- `load_port` is a do function. It reads like the version by hand, without the checks.

```python
from oxide import Do, Err, Ok, Result, do


def parse_port(text: str) -> Result[int, str]:
    if not text.isdigit():
        return Err(f"not a number: {text}")
    return Ok(int(text))


def check_range(port: int) -> Result[int, str]:
    return Ok(port) if 0 < port < 65_536 else Err(f"out of range: {port}")


def load_port_by_hand(text: str) -> Result[int, str]:
    parsed = parse_port(text)
    if not parsed:
        return parsed
    return check_range(parsed.value)


def load_port_chained(text: str) -> Result[int, str]:
    return parse_port(text).and_then(check_range)


@do
def load_port(text: str) -> Do[int, str]:
    port = yield from parse_port(text).try_()
    return (yield from check_range(port).try_())


for load in (load_port_by_hand, load_port_chained, load_port):
    assert load("8080") == Ok(8080)
    assert load("x") == Err("not a number: x")
    assert load("70000") == Err("out of range: 70000")
```

Read `port = yield from parse_port(text).try_()` as Rust's `parse_port(text)?`:

- On an `Ok`, it gives the value, so `port` is an `int`.
- On an `Err`, it stops `load_port`, and `load_port` returns that `Err`.
- `@do` runs the function as a generator. The caller calls `load_port("8080")` and gets a `Result`, not a generator.

An Option enters a do function through `ok_or`:

```python
from oxide import Do, Err, Nothing, Ok, Option, Some, do

PORTS = {"web": 8080}


def lookup(name: str) -> Option[int]:
    return Some(PORTS[name]) if name in PORTS else Nothing()


@do
def address(name: str) -> Do[str, str]:
    port = yield from lookup(name).ok_or(f"unknown service: {name}").try_()
    return f"localhost:{port}"


assert address("web") == Ok("localhost:8080")
assert address("db") == Err("unknown service: db")
```

- `Do[T, E]` is the return annotation: `T` is the value of the final `Ok`, and `E` is the union of the `Err` types. Each type checker reports an `Err` type that `E` leaves out.
- A do function takes Results only. An Option enters it through `ok_or`.
- On an `Err`, `@do` closes the generator, so each `finally` block runs.

[Back to contents](#usage)

## Unwrap errors

A failed `unwrap`, `expect`, `unwrap_err` or `expect_err` raises `UnwrapError`. When the error is an exception, `UnwrapError` is raised from it, so the traceback keeps the original exception.

```python
from oxide import Err, UnwrapError

try:
    Err(ValueError("bad port")).unwrap()
except UnwrapError as error:
    assert str(error).startswith("called `Result.unwrap()` on an `Err` value")
    assert isinstance(error.__cause__, ValueError)
```

[Back to contents](#usage)
