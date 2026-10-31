import inspect
from collections.abc import Callable
from types import FunctionType
from typing import assert_never, assert_type, cast

import pytest

from oxide import Err, Ok, catch

PRICES = {"apple": 3}


@catch(ValueError, KeyError)
def price_of(name: str, count: str) -> int:
    return PRICES[name] * int(count)


def describe(name: str, count: str) -> str:
    result = price_of(name, count)
    match result:
        case Ok(value):
            assert_type(value, int)
            return f"price {value}"
        case Err(error):
            assert_type(error, ValueError | KeyError)
            return f"error {type(error).__name__}"
        case _:
            assert_never(result)


@pytest.mark.parametrize(
    ("name", "count", "description"),
    [
        ("apple", "2", "price 6"),
        ("apple", "x", "error ValueError"),
        ("pear", "2", "error KeyError"),
    ],
)
def test_catch_types_the_error_with_the_union_of_its_exceptions(
    name: str, count: str, description: str
) -> None:
    assert describe(name, count) == description


@pytest.mark.parametrize(
    ("exceptions", "message"),
    [
        ((), "no exception type"),
        ((Exception,), "not Exception"),
        ((BaseException,), "not BaseException"),
    ],
)
def test_catch_rejects_no_type_exception_and_base_exception(
    exceptions: tuple[type[BaseException], ...], message: str
) -> None:
    unchecked_catch = cast("Callable[..., object]", catch)
    with pytest.raises(TypeError, match=message):
        unchecked_catch(*exceptions)


@pytest.mark.parametrize(
    "error", [ValueError("x"), KeyError("x"), ZeroDivisionError("x")]
)
def test_catch_turns_each_listed_exception_into_an_err_of_it(
    error: ValueError | KeyError | ZeroDivisionError,
) -> None:
    @catch(ValueError, KeyError, ZeroDivisionError)
    def load() -> int:
        raise error

    assert load() == Err(error)


def test_catch_propagates_an_exception_it_does_not_list() -> None:
    error = KeyError("pear")

    @catch(ValueError)
    def load() -> int:
        raise error

    with pytest.raises(KeyError) as caught:
        load()
    assert caught.value is error


def test_catch_keeps_the_parameters() -> None:
    assert list(inspect.signature(price_of).parameters) == ["name", "count"]
    assert price_of(name="apple", count="2") == Ok(6)


def test_catch_keeps_the_name_and_the_wrapped_function() -> None:
    def load(name: str) -> int:
        return PRICES[name]

    decorated = catch(KeyError)(load)
    assert isinstance(decorated, FunctionType)
    assert decorated.__name__ == "load"
    assert inspect.unwrap(decorated) is load
