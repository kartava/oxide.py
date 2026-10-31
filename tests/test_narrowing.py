from typing import assert_never, assert_type

import pytest

from oxide import Err, Nothing, Ok, Option, Result, Some

each_variant = pytest.mark.parametrize(
    ("text", "description"),
    [
        pytest.param("8080", "value 8080", id="an ok takes the ok branch"),
        pytest.param("x", "error x", id="an err takes the err branch"),
    ],
)
each_option = pytest.mark.parametrize(
    ("text", "description"),
    [
        pytest.param("8080", "value 8080", id="a some takes the some branch"),
        pytest.param("x", "nothing", id="nothing takes the nothing branch"),
    ],
)


def parse(text: str) -> Result[int, str]:
    return Ok(int(text)) if text.isdigit() else Err(text)


def find(text: str) -> Option[int]:
    return Some(int(text)) if text.isdigit() else Nothing()


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


@each_variant
def test_match_narrows_both_branches(text: str, description: str) -> None:
    assert describe_by_match(parse(text)) == description


@each_variant
def test_isinstance_narrows_both_branches(text: str, description: str) -> None:
    assert describe_by_isinstance(parse(text)) == description


def describe_option_by_match(option: Option[int]) -> str:
    match option:
        case Some(value):
            assert_type(value, int)
            return f"value {value}"
        case Nothing():
            assert_type(option, Nothing)
            return "nothing"
        case _:
            assert_never(option)


@each_option
def test_match_narrows_both_branches_of_an_option(
    text: str, description: str
) -> None:
    assert describe_option_by_match(find(text)) == description


def describe_option_by_isinstance(option: Option[int]) -> str:
    if isinstance(option, Some):
        assert_type(option, Some[int])
        return f"value {option.value}"
    assert_type(option, Nothing)
    return "nothing"


@each_option
def test_isinstance_narrows_both_branches_of_an_option(
    text: str, description: str
) -> None:
    assert describe_option_by_isinstance(find(text)) == description
