# oxide.py

[Rust](https://www.rust-lang.org)'s `Option<T>` and `Result<T, E>`, implemented for Python. A function returns one of them, so that an absent value or an expected failure is part of its type.

- `match` and `isinstance` narrow both branches on mypy, pyright, ty and pyrefly.
- No type-checker plugin and no config.
- No dependencies from Python 3.12. Python 3.11 needs `typing_extensions`.

## Why

A Python function reports a failure with an exception or with `None`. The signature does not show the exceptions, so a caller can forget to catch them and crash at runtime:

```python
def parse_port(text: str) -> int:
    return int(text)  # raises ValueError on "abc"
```

`oxide` puts the outcome in the return type. The function returns `Ok(value)` or `Err(error)`, `Some(value)` or `Nothing`. The caller unpacks the value with a plain `match`, and the type checker reports a missing case. See [Quick start](#quick-start).

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

### Use cases

- [A service from end to end](#a-service-from-end-to-end)
- [A database error becomes a domain Err](#a-database-error-becomes-a-domain-err)
- [A batch job](#a-batch-job)
- [Async code](#async-code)
- [Migrating from rustedpy/result](#migrating-from-rustedpyresult)

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

### No truth value

A variant has no truth value: `bool()` on an `Ok`, `Err`, `Some` or `Nothing` raises `TypeError`, so `if result:` fails loudly. In Python, `if value:` asks whether `value` is empty, and a true `Some(0)` or `Ok([])` would hide a bug. pyright reports `if result:` before the code runs. mypy, ty and pyrefly do not, so the `TypeError` reports it at runtime.

### Query methods

`is_ok()`, `is_err()`, `is_some()` and `is_nothing()` return `bool` and narrow nothing: a method cannot narrow its own `self` ([PEP 742](https://peps.python.org/pep-0742/)). After `if result.is_ok():`, `result` stays a `Result[int, str]`. Use them where a `bool` is enough, as in `filter(lambda result: result.is_ok(), results)`.

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

## Collections

`collect` gives all the values, or the first `Err`. `partition` keeps every value and every error, in input order.

```python
from oxide import Err, Ok, Result, collect, partition

results: list[Result[int, str]] = [Ok(1), Err("x"), Ok(2), Err("y")]

assert collect([Ok(1), Ok(2)]) == Ok([1, 2])
assert collect(results) == Err("x")
assert partition(results) == ([1, 2], ["x", "y"])
```

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
- `catch()`, `catch(Exception)`, and a value that is not a subclass of `Exception`, such as `KeyboardInterrupt`, raise `TypeError`: `catch` converts expected exceptions only.
- Inside the decorated function, a listed exception becomes an `Err` even when a bug raised it.
- `catch` takes a sync function only. For an `async def`, see [Async code](#async-code).

## Do functions

A function that runs several steps must stop at the first `Err`. Here are three ways to write the same `load_port`:

- `load_port_by_hand` tests each step with `isinstance` and returns the `Err` early.
- `load_port_chained` passes the value of each step to the next with `and_then`.
- `load_port` is a do function. It reads like the version by hand, without the `isinstance` branches.

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
    if isinstance(parsed, Err):
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
- A `yield` of a value other than an `Err` raises `TypeError`. Write `yield from result.try_()`.
- On an `Err`, `@do` closes the generator, so each `finally` block runs.

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

## A service from end to end

A repository returns an Option, a service returns a Result with one error type for each failure, and the HTTP layer maps each error to a status code.

```python
from dataclasses import dataclass
from typing import assert_never

from oxide import Do, Err, Ok, Option, Result, do, from_optional


@dataclass
class Order:
    order_id: int
    owner: str
    shipped: bool = False


@dataclass(frozen=True)
class NotFound:
    order_id: int


@dataclass(frozen=True)
class NotOwner:
    order_id: int


class Orders:
    def __init__(self, *orders: Order) -> None:
        self._rows = {order.order_id: order for order in orders}

    def find(self, order_id: int) -> Option[Order]:
        return from_optional(self._rows.get(order_id))


def check_owner(order: Order, user: str) -> Result[Order, NotOwner]:
    if order.owner != user:
        return Err(NotOwner(order.order_id))
    return Ok(order)


@do
def ship(
    orders: Orders, order_id: int, user: str
) -> Do[int, NotFound | NotOwner]:
    found = yield from orders.find(order_id).ok_or(NotFound(order_id)).try_()
    order = yield from check_owner(found, user).try_()
    order.shipped = True
    return order.order_id


def status_code(result: Result[int, NotFound | NotOwner]) -> int:
    match result:
        case Ok():
            return 200
        case Err(error):
            match error:
                case NotFound():
                    return 404
                case NotOwner():
                    return 403
                case _:
                    assert_never(error)
        case _:
            assert_never(result)


orders = Orders(Order(1, "ann"))
assert status_code(ship(orders, 2, "ann")) == 404
assert status_code(ship(orders, 1, "bob")) == 403
assert status_code(ship(orders, 1, "ann")) == 200
```

- `ok_or` turns a missing order into an `Err`, so one do function runs both checks.
- Match on the error in a second `match`. A pattern such as `case Err(NotFound()):` works at runtime, but no type checker proves that such cases cover every error.

## A database error becomes a domain Err

`@catch` turns the database exception into an `Err`, and `map_err` replaces it with a domain error. Every other database exception propagates.

```python
import sqlite3
from dataclasses import dataclass

from oxide import Err, Ok, Result, catch

database = sqlite3.connect(":memory:")
database.execute("CREATE TABLE users (email TEXT PRIMARY KEY)")


@dataclass(frozen=True)
class EmailTaken:
    email: str


@catch(sqlite3.IntegrityError)
def insert_user(email: str) -> str:
    database.execute("INSERT INTO users VALUES (?)", (email,))
    return email


def register(email: str) -> Result[str, EmailTaken]:
    return insert_user(email).map_err(lambda error: EmailTaken(email))


assert register("ann@example.com") == Ok("ann@example.com")
assert register("ann@example.com") == Err(EmailTaken("ann@example.com"))
```

## A batch job

A batch job keeps each value and logs each error. One error does not stop the job.

```python
import logging

from oxide import Err, Ok, Result, partition


def parse_port(text: str) -> Result[int, str]:
    if not text.isdigit():
        return Err(f"not a number: {text}")
    return Ok(int(text))


ports, errors = partition(parse_port(line) for line in ["80", "x", "443"])
for error in errors:
    logging.warning("skipped a line: %s", error)

assert ports == [80, 443]
assert errors == ["not a number: x"]
```

## Async code

`@do` and `@catch` take sync functions only. In an `async def`, return the `Err` early. The sample uses `Order`, `NotFound` and `NotOwner` from [A service from end to end](#a-service-from-end-to-end).

```python
import asyncio

from oxide import Err, Nothing, Ok, Option, Result, from_optional


class AsyncOrders:
    def __init__(self, *orders: Order) -> None:
        self._rows = {order.order_id: order for order in orders}

    async def find(self, order_id: int) -> Option[Order]:
        return from_optional(self._rows.get(order_id))


async def ship(
    orders: AsyncOrders, order_id: int, user: str
) -> Result[int, NotFound | NotOwner]:
    found = await orders.find(order_id)
    if isinstance(found, Nothing):
        return Err(NotFound(order_id))
    order = found.value
    if order.owner != user:
        return Err(NotOwner(order_id))
    order.shipped = True
    return Ok(order.order_id)


orders = AsyncOrders(Order(1, "ann"))
assert asyncio.run(ship(orders, 2, "ann")) == Err(NotFound(2))
assert asyncio.run(ship(orders, 1, "bob")) == Err(NotOwner(1))
assert asyncio.run(ship(orders, 1, "ann")) == Ok(1)
```

## Migrating from `rustedpy/result`

The table maps the API of [`rustedpy/result`](https://github.com/rustedpy/result) 0.17.0, its last release, to `oxide`.

| `rustedpy/result` | `oxide` | Change |
|---|---|---|
| `Ok`, `Err`, `Result`, `UnwrapError` | Same names | No change |
| `OkErr`, the tuple `(Ok, Err)` | `(Ok, Err)` | `oxide` has no name for the tuple. Write `isinstance(result, (Ok, Err))`. |
| `is_ok(result)`, `is_err(result)` | `match`, or `isinstance(result, Ok)` | The `rustedpy/result` functions narrow only the `if` branch. `match` and `isinstance` narrow both branches. The method `result.is_ok()` narrows nothing. |
| `result.ok_value`, `result.err_value` | `result.value`, `result.error` | Rename |
| `Ok(value).value` | `Ok(value).value` | No change |
| `Err(error).value` | `Err(error).error` | An `oxide` `Err` has no `value`. |
| `result.ok()`, `result.err()`, which return `T \| None` | `result.ok()`, `result.err()` | They return an Option. `.to_optional()` gives `T \| None`. |
| `unwrap`, `expect`, `unwrap_err`, `expect_err`, `unwrap_or`, `unwrap_or_else`, `map`, `map_err`, `and_then`, `or_else` | Same names | No change |
| `unwrap_or_raise`, `map_or`, `map_or_else`, `inspect`, `inspect_err` | No equivalent | Write the logic by hand. |
| `UnwrapError.result`, the original Result | `UnwrapError.__cause__` | `oxide` keeps the error, not the Result, and only when the error is an exception. |
| `@as_result(ValueError)` | `@catch(ValueError)` | `catch` takes 1 to 3 subclasses of `Exception`. It raises `TypeError` for no type, for `Exception`, and for any other type, such as `KeyboardInterrupt`. |
| `do()` on a generator expression, which iterates the variants | `@do` on a generator function, with `yield from result.try_()` | New syntax: see [Do functions](#do-functions). `oxide` variants are not iterable. |
| `as_async_result`, `do_async`, `map_async`, `and_then_async` | No equivalent | `oxide` has no async API. |
| `if result:`, always true, because `Ok` and `Err` have no `__bool__` | Not possible | `bool()` raises `TypeError`: see [No truth value](#no-truth-value). |
