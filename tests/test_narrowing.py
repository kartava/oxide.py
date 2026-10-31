from typing import assert_never, assert_type

import pytest

from oxide import Err, Ok, Result

each_variant = pytest.mark.parametrize(
    ("text", "description"), [("8080", "value 8080"), ("x", "error x")]
)


def parse(text: str) -> Result[int, str]:
    return Ok(int(text)) if text.isdigit() else Err(text)


def describe_by_match(result: Result[int, str]) -> str:
    match result:
        case Ok(value):
            assert_type(value, int)
            return f"value {value}"
        case Err(error):
            assert_type(error, str)
            return f"error {error}"
        case _:
            assert_never(result)


def describe_by_isinstance(result: Result[int, str]) -> str:
    if isinstance(result, Ok):
        assert_type(result, Ok[int])
        return f"value {result.value}"
    assert_type(result, Err[str])
    return f"error {result.error}"


def describe_by_truthiness(result: Result[int, str]) -> str:
    if result:
        assert_type(result, Ok[int])
        return f"value {result.value}"
    assert_type(result, Err[str])
    return f"error {result.error}"


@each_variant
def test_match_narrows_both_branches(text: str, description: str) -> None:
    assert describe_by_match(parse(text)) == description


@each_variant
def test_isinstance_narrows_both_branches(text: str, description: str) -> None:
    assert describe_by_isinstance(parse(text)) == description


@each_variant
def test_truthiness_narrows_both_branches(text: str, description: str) -> None:
    assert describe_by_truthiness(parse(text)) == description
