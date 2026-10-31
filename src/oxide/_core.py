from collections.abc import Callable, Generator, Iterable
from typing import (
    Any,
    Generic,
    Never,
    TypeAlias,
    TypeVar,
    cast,
    final,
)

T = TypeVar("T")
E = TypeVar("E")
D = TypeVar("D")
U = TypeVar("U")
F = TypeVar("F")
T_co = TypeVar("T_co", covariant=True)
E_co = TypeVar("E_co", covariant=True)


class UnwrapError(Exception):
    """Report a failed unwrap or expect call.

    The `__cause__` holds the error when it is an exception.
    """


def _no_truth_value(variant: str) -> TypeError:
    return TypeError(f"{variant} has no truth value. Use match or isinstance.")


@final
class Ok(Generic[T_co]):
    """Hold the success value of a Result."""

    __slots__ = ("_value",)
    __match_args__ = ("value",)

    def __init__(self, value: T_co) -> None:
        self._value = value

    @property
    def value(self) -> T_co:
        return self._value

    def is_ok(self) -> bool:
        """Narrow nothing: use `match` or `isinstance` instead."""
        return True

    def is_err(self) -> bool:
        """Narrow nothing: use `match` or `isinstance` instead."""
        return False

    def expect(self, message: str) -> T_co:
        """Return the value of an Ok.

        Raise `UnwrapError` on an Err. Show the message and the error.
        """
        return self._value

    def expect_err(self, message: str) -> Never:
        """Return the error of an Err.

        Raise `UnwrapError` on an Ok. Show the message and the value.
        """
        raise UnwrapError(f"{message}: {self._value!r}")

    def unwrap(self) -> T_co:
        """Return the value of an Ok.

        Raise `UnwrapError` on an Err.
        """
        return self._value

    def unwrap_err(self) -> Never:
        """Return the error of an Err.

        Raise `UnwrapError` on an Ok.
        """
        raise UnwrapError(
            f"called `Result.unwrap_err()` on an `Ok` value: {self._value!r}"
        )

    def unwrap_or(self, default: object) -> T_co:
        """Return the value of an Ok. Return the default on an Err."""
        return self._value

    def unwrap_or_else(self, function: Callable[[Never], object]) -> T_co:
        """Return the value of an Ok. Call the function on an Err."""
        return self._value

    def map(self, function: Callable[[T_co], U]) -> "Ok[U]":
        """Apply the function to the value of an Ok. Keep an Err."""
        return Ok(function(self._value))

    def map_err(self, function: Callable[[Never], object]) -> "Ok[T_co]":
        """Apply the function to the error of an Err. Keep an Ok."""
        return self

    def and_then(
        self, function: Callable[[T_co], "Result[U, F]"]
    ) -> "Result[U, F]":
        """Pass the value of an Ok to the function. Keep an Err."""
        return function(self._value)

    def or_else(self, function: Callable[[Never], object]) -> "Ok[T_co]":
        """Pass the error of an Err to the function. Keep an Ok."""
        return self

    def ok(self) -> "Some[T_co]":
        """Convert to an Option of the value. Drop any error."""
        return Some(self._value)

    def err(self) -> "Nothing":
        """Convert to an Option of the error. Drop any value."""
        return Nothing()

    def flatten(self: "Ok[Result[U, F]]") -> "Result[U, F]":
        """Return the inner Result of an Ok. Keep an Err."""
        return self._value

    def transpose(self: "Ok[Option[U]]") -> "Option[Ok[U]]":
        """Swap the layers: an Ok of a Some becomes a Some of an Ok."""
        return self._value.map(Ok)

    def try_(self) -> Generator[Never, Any, T_co]:
        """Give an Ok's value to `yield from`. Return an Err early.

        Use it only in a generator function under `@do`.
        """
        # `yield from ()` makes a generator that only returns the value.
        yield from ()
        return self._value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Ok):
            return NotImplemented
        # isinstance gives `Ok[Unknown]`. Strict pyright rejects it.
        return self._value == cast("Ok[object]", other)._value

    def __hash__(self) -> int:
        return hash((Ok, self._value))

    def __repr__(self) -> str:
        return f"Ok({self._value!r})"

    def __bool__(self) -> Never:
        raise _no_truth_value("Ok")


@final
class Err(Generic[E_co]):
    """Hold the expected failure of a Result."""

    __slots__ = ("_error",)
    __match_args__ = ("error",)

    def __init__(self, error: E_co) -> None:
        self._error = error

    @property
    def error(self) -> E_co:
        return self._error

    def is_ok(self) -> bool:
        """Narrow nothing: use `match` or `isinstance` instead."""
        return False

    def is_err(self) -> bool:
        """Narrow nothing: use `match` or `isinstance` instead."""
        return True

    def expect(self, message: str) -> Never:
        """Return the value of an Ok.

        Raise `UnwrapError` on an Err. Show the message and the error.
        """
        self._raise(f"{message}: {self._error!r}")

    def expect_err(self, message: str) -> E_co:
        """Return the error of an Err.

        Raise `UnwrapError` on an Ok. Show the message and the value.
        """
        return self._error

    def unwrap(self) -> Never:
        """Return the value of an Ok.

        Raise `UnwrapError` on an Err.
        """
        self._raise(
            f"called `Result.unwrap()` on an `Err` value: {self._error!r}"
        )

    def unwrap_err(self) -> E_co:
        """Return the error of an Err.

        Raise `UnwrapError` on an Ok.
        """
        return self._error

    def unwrap_or(self, default: D) -> D:
        """Return the value of an Ok. Return the default on an Err."""
        return default

    def unwrap_or_else(self, function: Callable[[E_co], D]) -> D:
        """Return the value of an Ok. Call the function on an Err."""
        return function(self._error)

    def map(self, function: Callable[[Never], object]) -> "Err[E_co]":
        """Apply the function to the value of an Ok. Keep an Err."""
        return self

    def map_err(self, function: Callable[[E_co], F]) -> "Err[F]":
        """Apply the function to the error of an Err. Keep an Ok."""
        return Err(function(self._error))

    def and_then(self, function: Callable[[Never], object]) -> "Err[E_co]":
        """Pass the value of an Ok to the function. Keep an Err."""
        return self

    def or_else(
        self, function: Callable[[E_co], "Result[U, F]"]
    ) -> "Result[U, F]":
        """Pass the error of an Err to the function. Keep an Ok."""
        return function(self._error)

    def ok(self) -> "Nothing":
        """Convert to an Option of the value. Drop any error."""
        return Nothing()

    def err(self) -> "Some[E_co]":
        """Convert to an Option of the error. Drop any value."""
        return Some(self._error)

    def flatten(self) -> "Err[E_co]":
        """Return the inner Result of an Ok. Keep an Err."""
        return self

    def transpose(self) -> "Some[Err[E_co]]":
        """Swap the layers: an Ok of a Some becomes a Some of an Ok."""
        return Some(self)

    def try_(self) -> Generator["Err[E_co]", Any, Never]:
        """Give an Ok's value to `yield from`. Return an Err early.

        Use it only in a generator function under `@do`.
        """
        yield self
        raise RuntimeError("`try_()` resumed after an Err, outside `@do`")

    def _raise(self, message: str) -> Never:
        if isinstance(self._error, BaseException):
            raise UnwrapError(message) from self._error
        raise UnwrapError(message)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Err):
            return NotImplemented
        # isinstance gives `Err[Unknown]`. Strict pyright rejects it.
        return self._error == cast("Err[object]", other)._error

    def __hash__(self) -> int:
        return hash((Err, self._error))

    def __repr__(self) -> str:
        return f"Err({self._error!r})"

    def __bool__(self) -> Never:
        raise _no_truth_value("Err")


@final
class Some(Generic[T_co]):
    """Hold the value of an Option.

    `Some(None)` is a Some, not Nothing.
    """

    __slots__ = ("_value",)
    __match_args__ = ("value",)

    def __init__(self, value: T_co) -> None:
        self._value = value

    @property
    def value(self) -> T_co:
        return self._value

    def is_some(self) -> bool:
        """Narrow nothing: use `match` or `isinstance` instead."""
        return True

    def is_nothing(self) -> bool:
        """Narrow nothing: use `match` or `isinstance` instead."""
        return False

    def expect(self, message: str) -> T_co:
        """Return the value of a Some.

        Raise `UnwrapError` on Nothing. Show the message.
        """
        return self._value

    def unwrap(self) -> T_co:
        """Return the value of a Some.

        Raise `UnwrapError` on Nothing.
        """
        return self._value

    def unwrap_or(self, default: object) -> T_co:
        """Return the value of a Some. Return the default on Nothing."""
        return self._value

    def unwrap_or_else(self, function: Callable[[], object]) -> T_co:
        """Return the value of a Some. Call the function on Nothing."""
        return self._value

    def map(self, function: Callable[[T_co], U]) -> "Some[U]":
        """Apply the function to the value of a Some. Keep Nothing."""
        return Some(function(self._value))

    def and_then(self, function: Callable[[T_co], "Option[U]"]) -> "Option[U]":
        """Pass the value of a Some to the function. Keep Nothing."""
        return function(self._value)

    def or_else(self, function: Callable[[], object]) -> "Some[T_co]":
        """Call the function for Nothing. Keep a Some."""
        return self

    def ok_or(self, error: object) -> Ok[T_co]:
        """Convert to a Result. Use the error in place of Nothing."""
        return Ok(self._value)

    def ok_or_else(self, function: Callable[[], object]) -> Ok[T_co]:
        """Convert to a Result. Build the error with the function."""
        return Ok(self._value)

    def flatten(self: "Some[Option[U]]") -> "Option[U]":
        """Return the inner Option of a Some. Keep Nothing."""
        return self._value

    def transpose(self: "Some[Result[U, F]]") -> "Result[Some[U], F]":
        """Swap the layers: a Some of an Ok becomes an Ok of a Some."""
        return self._value.map(Some)

    def to_optional(self) -> T_co:
        """Return the value of a Some. Return None on Nothing."""
        return self._value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Some):
            return NotImplemented
        # isinstance gives `Some[Unknown]`. Strict pyright rejects it.
        return self._value == cast("Some[object]", other)._value

    def __hash__(self) -> int:
        return hash((Some, self._value))

    def __repr__(self) -> str:
        return f"Some({self._value!r})"

    def __bool__(self) -> Never:
        raise _no_truth_value("Some")


@final
class Nothing:
    """Stand for an Option that holds no value.

    `Nothing()` always returns the same instance.
    """

    __slots__ = ()

    def __new__(cls) -> "Nothing":
        return _NOTHING

    def __reduce__(self) -> tuple[type["Nothing"], tuple[()]]:
        return (Nothing, ())

    def is_some(self) -> bool:
        """Narrow nothing: use `match` or `isinstance` instead."""
        return False

    def is_nothing(self) -> bool:
        """Narrow nothing: use `match` or `isinstance` instead."""
        return True

    def expect(self, message: str) -> Never:
        """Return the value of a Some.

        Raise `UnwrapError` on Nothing. Show the message.
        """
        raise UnwrapError(message)

    def unwrap(self) -> Never:
        """Return the value of a Some.

        Raise `UnwrapError` on Nothing.
        """
        raise UnwrapError("called `Option.unwrap()` on a `Nothing` value")

    def unwrap_or(self, default: D) -> D:
        """Return the value of a Some. Return the default on Nothing."""
        return default

    def unwrap_or_else(self, function: Callable[[], D]) -> D:
        """Return the value of a Some. Call the function on Nothing."""
        return function()

    def map(self, function: Callable[[Never], object]) -> "Nothing":
        """Apply the function to the value of a Some. Keep Nothing."""
        return self

    def and_then(self, function: Callable[[Never], object]) -> "Nothing":
        """Pass the value of a Some to the function. Keep Nothing."""
        return self

    def or_else(self, function: Callable[[], "Option[U]"]) -> "Option[U]":
        """Call the function for Nothing. Keep a Some."""
        return function()

    def ok_or(self, error: F) -> Err[F]:
        """Convert to a Result. Use the error in place of Nothing."""
        return Err(error)

    def ok_or_else(self, function: Callable[[], F]) -> Err[F]:
        """Convert to a Result. Build the error with the function."""
        return Err(function())

    def flatten(self) -> "Nothing":
        """Return the inner Option of a Some. Keep Nothing."""
        return self

    def transpose(self) -> "Ok[Nothing]":
        """Swap the layers: a Some of an Ok becomes an Ok of a Some."""
        return Ok(self)

    def to_optional(self) -> None:
        """Return the value of a Some. Return None on Nothing."""
        return None

    def __repr__(self) -> str:
        return "Nothing()"

    def __bool__(self) -> Never:
        raise _no_truth_value("Nothing")


_NOTHING = object.__new__(Nothing)


Result: TypeAlias = Ok[T] | Err[E]
Option: TypeAlias = Some[T] | Nothing


def collect(items: Iterable[Result[T, E]]) -> Result[list[T], E]:
    """Return the first Err. Else return an Ok of the values."""
    values: list[T] = []
    for item in items:
        if isinstance(item, Err):
            return item
        values.append(item.value)
    return Ok(values)


def partition(items: Iterable[Result[T, E]]) -> tuple[list[T], list[E]]:
    """Return the values and the errors, each in input order."""
    values: list[T] = []
    errors: list[E] = []
    for item in items:
        if isinstance(item, Ok):
            values.append(item.value)
        else:
            errors.append(item.error)
    return values, errors


def from_optional(value: T | None) -> Option[T]:
    """Return Nothing for None. Return a Some of any other value."""
    return Nothing() if value is None else Some(value)
