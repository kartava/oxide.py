from collections.abc import Callable, Generator, Iterable
from typing import (
    Any,
    Generic,
    Literal,
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
    pass


@final
class Ok(Generic[T_co]):
    __slots__ = ("_value",)
    __match_args__ = ("value",)

    def __init__(self, value: T_co) -> None:
        self._value = value

    @property
    def value(self) -> T_co:
        return self._value

    def is_ok(self) -> bool:
        return True

    def is_err(self) -> bool:
        return False

    def expect(self, message: str) -> T_co:
        return self._value

    def expect_err(self, message: str) -> Never:
        raise UnwrapError(f"{message}: {self._value!r}")

    def unwrap(self) -> T_co:
        return self._value

    def unwrap_err(self) -> Never:
        raise UnwrapError(
            f"called `Result.unwrap_err()` on an `Ok` value: {self._value!r}"
        )

    def unwrap_or(self, default: object) -> T_co:
        return self._value

    def unwrap_or_else(self, function: Callable[[Never], object]) -> T_co:
        return self._value

    def map(self, function: Callable[[T_co], U]) -> "Ok[U]":
        return Ok(function(self._value))

    def map_err(self, function: Callable[[Never], object]) -> "Ok[T_co]":
        return self

    def and_then(
        self, function: Callable[[T_co], "Result[U, F]"]
    ) -> "Result[U, F]":
        return function(self._value)

    def or_else(self, function: Callable[[Never], object]) -> "Ok[T_co]":
        return self

    def ok(self) -> "Some[T_co]":
        return Some(self._value)

    def err(self) -> "Nothing":
        return Nothing()

    def flatten(self: "Ok[Result[U, F]]") -> "Result[U, F]":
        return self._value

    def transpose(self: "Ok[Option[U]]") -> "Option[Ok[U]]":
        return self._value.map(Ok)

    def try_(self) -> Generator[Never, Any, T_co]:
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

    def __bool__(self) -> Literal[True]:
        return True


@final
class Err(Generic[E_co]):
    __slots__ = ("_error",)
    __match_args__ = ("error",)

    def __init__(self, error: E_co) -> None:
        self._error = error

    @property
    def error(self) -> E_co:
        return self._error

    def is_ok(self) -> bool:
        return False

    def is_err(self) -> bool:
        return True

    def expect(self, message: str) -> Never:
        self._raise(f"{message}: {self._error!r}")

    def expect_err(self, message: str) -> E_co:
        return self._error

    def unwrap(self) -> Never:
        self._raise(
            f"called `Result.unwrap()` on an `Err` value: {self._error!r}"
        )

    def unwrap_err(self) -> E_co:
        return self._error

    def unwrap_or(self, default: D) -> D:
        return default

    def unwrap_or_else(self, function: Callable[[E_co], D]) -> D:
        return function(self._error)

    def map(self, function: Callable[[Never], object]) -> "Err[E_co]":
        return self

    def map_err(self, function: Callable[[E_co], F]) -> "Err[F]":
        return Err(function(self._error))

    def and_then(self, function: Callable[[Never], object]) -> "Err[E_co]":
        return self

    def or_else(
        self, function: Callable[[E_co], "Result[U, F]"]
    ) -> "Result[U, F]":
        return function(self._error)

    def ok(self) -> "Nothing":
        return Nothing()

    def err(self) -> "Some[E_co]":
        return Some(self._error)

    def flatten(self) -> "Err[E_co]":
        return self

    def transpose(self) -> "Some[Err[E_co]]":
        return Some(self)

    def try_(self) -> Generator["Err[E_co]", Any, Never]:
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

    def __bool__(self) -> Literal[False]:
        return False


@final
class Some(Generic[T_co]):
    __slots__ = ("_value",)
    __match_args__ = ("value",)

    def __init__(self, value: T_co) -> None:
        self._value = value

    @property
    def value(self) -> T_co:
        return self._value

    def is_some(self) -> bool:
        return True

    def is_nothing(self) -> bool:
        return False

    def expect(self, message: str) -> T_co:
        return self._value

    def unwrap(self) -> T_co:
        return self._value

    def unwrap_or(self, default: object) -> T_co:
        return self._value

    def unwrap_or_else(self, function: Callable[[], object]) -> T_co:
        return self._value

    def map(self, function: Callable[[T_co], U]) -> "Some[U]":
        return Some(function(self._value))

    def and_then(self, function: Callable[[T_co], "Option[U]"]) -> "Option[U]":
        return function(self._value)

    def or_else(self, function: Callable[[], object]) -> "Some[T_co]":
        return self

    def ok_or(self, error: object) -> Ok[T_co]:
        return Ok(self._value)

    def ok_or_else(self, function: Callable[[], object]) -> Ok[T_co]:
        return Ok(self._value)

    def flatten(self: "Some[Option[U]]") -> "Option[U]":
        return self._value

    def transpose(self: "Some[Result[U, F]]") -> "Result[Some[U], F]":
        return self._value.map(Some)

    def to_optional(self) -> T_co:
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

    def __bool__(self) -> Literal[True]:
        return True


@final
class Nothing:
    __slots__ = ()

    def __new__(cls) -> "Nothing":
        return _NOTHING

    def is_some(self) -> bool:
        return False

    def is_nothing(self) -> bool:
        return True

    def expect(self, message: str) -> Never:
        raise UnwrapError(message)

    def unwrap(self) -> Never:
        raise UnwrapError("called `Option.unwrap()` on a `Nothing` value")

    def unwrap_or(self, default: D) -> D:
        return default

    def unwrap_or_else(self, function: Callable[[], D]) -> D:
        return function()

    def map(self, function: Callable[[Never], object]) -> "Nothing":
        return self

    def and_then(self, function: Callable[[Never], object]) -> "Nothing":
        return self

    def or_else(self, function: Callable[[], "Option[U]"]) -> "Option[U]":
        return function()

    def ok_or(self, error: F) -> Err[F]:
        return Err(error)

    def ok_or_else(self, function: Callable[[], F]) -> Err[F]:
        return Err(function())

    def flatten(self) -> "Nothing":
        return self

    def transpose(self) -> "Ok[Nothing]":
        return Ok(self)

    def to_optional(self) -> None:
        return None

    def __repr__(self) -> str:
        return "Nothing()"

    def __bool__(self) -> Literal[False]:
        return False


_NOTHING = object.__new__(Nothing)


Result: TypeAlias = Ok[T] | Err[E]
Option: TypeAlias = Some[T] | Nothing


def collect(items: Iterable[Result[T, E]]) -> Result[list[T], E]:
    values: list[T] = []
    for item in items:
        if isinstance(item, Err):
            return item
        values.append(item.value)
    return Ok(values)


def partition(items: Iterable[Result[T, E]]) -> tuple[list[T], list[E]]:
    values: list[T] = []
    errors: list[E] = []
    for item in items:
        if isinstance(item, Ok):
            values.append(item.value)
        else:
            errors.append(item.error)
    return values, errors


def from_optional(value: T | None) -> Option[T]:
    return Nothing() if value is None else Some(value)
