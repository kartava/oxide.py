import inspect
from collections.abc import Callable
from typing import Any, assert_type

import pytest

from oxide import Do, Err, Nothing, Ok, Option, Result, Some, do

NOT_A_NUMBER = ValueError("not a number")


def parse(text: str) -> Result[int, ValueError]:
    return Ok(int(text)) if text.isdigit() else Err(NOT_A_NUMBER)


def check_range(port: int) -> Result[int, str]:
    return Ok(port) if 0 < port < 65_536 else Err(f"out of range: {port}")


@do
def load_address(text: str) -> Do[str, ValueError | str]:
    number = yield from parse(text).try_()
    assert_type(number, int)
    port = yield from check_range(number).try_()
    assert_type(port, int)
    return f"localhost:{port}"


def test_do_function_returns_ok_of_its_return_value() -> None:
    assert load_address("8080") == Ok("localhost:8080")


@pytest.mark.parametrize(
    ("text", "result"),
    [
        pytest.param(
            "x",
            Err(NOT_A_NUMBER),
            id="a letter gives the err of the first step",
        ),
        pytest.param(
            "70000",
            Err("out of range: 70000"),
            id="a large number gives the err of the second step",
        ),
    ],
)
def test_do_function_returns_the_err_of_the_first_failed_step(
    text: str, result: Result[str, ValueError | str]
) -> None:
    load: Callable[[str], Result[str, ValueError | str]] = load_address
    assert load(text) == result


def test_do_closes_the_generator_on_an_err() -> None:
    # CPython also runs the finally block when it frees the generator.
    # It drops the error from that run. The error reaches the caller
    # only when `do` closes the generator.
    @do
    def load(text: str) -> Do[int, ValueError]:
        try:
            return (yield from parse(text).try_())
        finally:
            raise OSError("cleanup failed")

    with pytest.raises(OSError, match="cleanup failed"):
        load("x")


def test_do_rejects_a_function_that_is_not_a_generator_function() -> None:
    def steps(text: str) -> Do[int, ValueError]:
        return (yield from parse(text).try_())

    def delegate(text: str) -> Do[int, ValueError]:
        return steps(text)

    with pytest.raises(TypeError, match="not a generator function"):
        do(delegate)


def test_do_rejects_a_yield_that_is_not_an_err() -> None:
    port: Any = 8080

    @do
    def load() -> Do[int, str]:
        yield port
        return 1

    with pytest.raises(TypeError, match="yielded 8080, not an Err"):
        load()


def test_try_resumed_after_an_err_raises() -> None:
    steps = Err("x").try_()
    assert next(steps) == Err("x")
    with pytest.raises(RuntimeError, match="resumed after an Err"):
        next(steps)


def test_do_function_keeps_its_parameters() -> None:
    assert list(inspect.signature(load_address).parameters) == ["text"]
    assert load_address(text="8080") == Ok("localhost:8080")


NO_PORT = LookupError("no port")


def find(text: str) -> Option[int]:
    return Some(int(text)) if text.isdigit() else Nothing()


@do
def load_port(text: str) -> Do[int, LookupError]:
    port = yield from find(text).ok_or(NO_PORT).try_()
    assert_type(port, int)
    return port


@pytest.mark.parametrize(
    ("text", "result"),
    [
        pytest.param("8080", Ok(8080), id="a some gives its value"),
        pytest.param("x", Err(NO_PORT), id="nothing returns the err"),
    ],
)
def test_ok_or_step(text: str, result: Result[int, LookupError]) -> None:
    assert load_port(text) == result
