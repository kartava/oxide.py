from collections.abc import Callable
from typing import Generic, Literal, Never, TypeAlias, TypeVar, cast, final

T = TypeVar("T")
E = TypeVar("E")
D = TypeVar("D")
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


Result: TypeAlias = Ok[T] | Err[E]
