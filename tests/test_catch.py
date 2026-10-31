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
        pytest.param("apple", "2", "price 6", id="two apples give the price"),
        pytest.param(
            "apple",
            "x",
            "error ValueError",
            id="a count that is not a number gives an err of a value error",
        ),
        pytest.param(
            "pear",
            "2",
            "error KeyError",
            id="an unknown name gives an err of a key error",
        ),
    ],
)
def test_catch_types_the_error_with_the_union_of_its_exceptions(
    name: str, count: str, description: str
) -> None:
    assert describe(name, count) == description


@pytest.mark.parametrize(
    ("exceptions", "message"),
    [
        pytest.param((), "no exception type", id="no type is rejected"),
        pytest.param(
            (Exception,), "not Exception", id="exception is rejected"
        ),
        pytest.param(
            (BaseException,),
            "not BaseException",
            id="base exception is rejected",
        ),
        pytest.param(
            (KeyboardInterrupt,),
            "not KeyboardInterrupt",
            id="keyboard interrupt is rejected",
        ),
        pytest.param(
            (ValueError, ValueError("x")),
            r"not ValueError\('x'\)",
            id="an exception instance is rejected",
        ),
    ],
)
def test_catch(exceptions: tuple[object, ...], message: str) -> None:
    unchecked_catch = cast("Callable[..., object]", catch)
    with pytest.raises(TypeError, match=message):
        unchecked_catch(*exceptions)


@pytest.mark.parametrize(
    "error",
    [
        pytest.param(ValueError("x"), id="a value error becomes an err"),
        pytest.param(KeyError("x"), id="a key error becomes an err"),
        pytest.param(
            ZeroDivisionError("x"), id="a zero division error becomes an err"
        ),
    ],
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
