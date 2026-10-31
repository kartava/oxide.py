from typing import Generic, Literal, TypeAlias, TypeVar, cast, final

T = TypeVar("T")
E = TypeVar("E")
T_co = TypeVar("T_co", covariant=True)
E_co = TypeVar("E_co", covariant=True)


@final
class Ok(Generic[T_co]):
    __slots__ = ("_value",)
    __match_args__ = ("value",)

    def __init__(self, value: T_co) -> None:
        self._value = value

    @property
    def value(self) -> T_co:
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
