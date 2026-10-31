import inspect
from collections.abc import Callable
from typing import assert_type

import pytest

from oxide import Do, Err, Ok, Result, do

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
    ("text", "error"),
    [("x", Err(NOT_A_NUMBER)), ("70000", Err("out of range: 70000"))],
)
def test_do_function_returns_the_err_of_the_first_failed_step(
    text: str, error: Result[str, ValueError | str]
) -> None:
    assert load_address(text) == error


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


def test_do_function_returns_the_error_union_of_its_annotation() -> None:
    load: Callable[[str], Result[str, ValueError | str]] = load_address
    assert load("x") == Err(NOT_A_NUMBER)


def test_do_function_keeps_its_parameters() -> None:
    assert list(inspect.signature(load_address).parameters) == ["text"]
    assert load_address(text="8080") == Ok("localhost:8080")
