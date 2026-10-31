import copy
import pickle
from unittest.mock import ANY

import pytest

from oxide import Err, Ok, Result


@pytest.mark.parametrize(
    ("result", "attribute"),
    [
        (Ok(1), "value"),
        (Err("x"), "error"),
        (Ok(1), "extra"),
        (Err("x"), "extra"),
    ],
)
def test_assignment_raises_attribute_error(
    result: Result[int, str], attribute: str
) -> None:
    with pytest.raises(AttributeError):
        setattr(result, attribute, 2)


@pytest.mark.parametrize("result", [Ok(True), Err(ValueError("x"))])
def test_result_is_covariant(result: Result[bool, ValueError]) -> None:
    widened: Result[int, Exception] = result
    assert widened is result


@pytest.mark.parametrize(
    ("left", "right", "equal"),
    [
        (Ok(1), Ok(1), True),
        (Ok(1), Ok(2), False),
        (Err("x"), Err("x"), True),
        (Err("x"), Err("y"), False),
        (Ok(1), Err(1), False),
    ],
)
def test_equality_compares_variant_and_content(
    left: Result[int, object], right: Result[int, object], equal: bool
) -> None:
    assert (left == right) is equal


@pytest.mark.parametrize("result", [Ok(1), Err("x")])
def test_equality_with_another_class_asks_the_other_object(
    result: Result[int, str],
) -> None:
    assert result == ANY


def test_hash_matches_equality() -> None:
    assert {Ok(1), Ok(1), Err(1), Err(1)} == {Ok(1), Err(1)}


@pytest.mark.parametrize("result", [Ok([1]), Err([1])])
def test_unhashable_content_makes_the_variant_unhashable(
    result: Result[list[int], list[int]],
) -> None:
    with pytest.raises(TypeError):
        hash(result)


@pytest.mark.parametrize(
    ("result", "text"), [(Ok(1), "Ok(1)"), (Err("x"), "Err('x')")]
)
def test_repr_shows_the_variant_and_content(
    result: Result[int, str], text: str
) -> None:
    assert repr(result) == text


@pytest.mark.parametrize("result", [Ok([1]), Err([2])])
def test_pickle_round_trips_the_variant(
    result: Result[list[int], list[int]],
) -> None:
    assert pickle.loads(pickle.dumps(result)) == result


@pytest.mark.parametrize("result", [Ok([1]), Err([2])])
def test_deepcopy_round_trips_the_variant(
    result: Result[list[int], list[int]],
) -> None:
    assert copy.deepcopy(result) == result
