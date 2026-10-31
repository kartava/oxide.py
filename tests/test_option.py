import copy
import pickle
from collections.abc import Callable
from typing import assert_type
from unittest.mock import ANY

import pytest

from oxide import Nothing, Ok, Option, Some, UnwrapError


def test_nothing_is_one_instance() -> None:
    assert Nothing() is Nothing()


def test_pickle_keeps_the_nothing_instance() -> None:
    assert pickle.loads(pickle.dumps(Nothing())) is Nothing()


def test_deepcopy_keeps_the_nothing_instance() -> None:
    assert copy.deepcopy(Nothing()) is Nothing()


def test_pickle_round_trips_a_some() -> None:
    assert pickle.loads(pickle.dumps(Some([1]))) == Some([1])


def test_deepcopy_round_trips_a_some() -> None:
    assert copy.deepcopy(Some([1])) == Some([1])


@pytest.mark.parametrize(
    ("left", "right", "equal"),
    [
        (Some(1), Some(1), True),
        (Some(1), Some(2), False),
        (Nothing(), Nothing(), True),
        (Some(None), Nothing(), False),
        (Some(1), Ok(1), False),
    ],
)
def test_equality_compares_variant_and_content(
    left: object, right: object, equal: bool
) -> None:
    assert (left == right) is equal


@pytest.mark.parametrize("option", [Some(1), Nothing()])
def test_equality_with_another_class_asks_the_other_object(
    option: Option[int],
) -> None:
    assert option == ANY


def test_hash_matches_equality() -> None:
    assert {Some(1), Some(1), Nothing(), Nothing()} == {Some(1), Nothing()}


def test_unhashable_content_makes_a_some_unhashable() -> None:
    with pytest.raises(TypeError):
        hash(Some([1]))


@pytest.mark.parametrize(
    ("option", "text"),
    [
        (Some(1), "Some(1)"),
        (Some(None), "Some(None)"),
        (Nothing(), "Nothing()"),
    ],
)
def test_repr_shows_the_variant_and_content(
    option: Option[int | None], text: str
) -> None:
    assert repr(option) == text


@pytest.mark.parametrize(
    ("option", "attribute"),
    [(Some(1), "value"), (Some(1), "extra"), (Nothing(), "extra")],
)
def test_assignment_raises_attribute_error(
    option: Option[int], attribute: str
) -> None:
    with pytest.raises(AttributeError):
        setattr(option, attribute, 2)


@pytest.mark.parametrize("option", [Some(True), Nothing()])
def test_option_is_covariant(option: Option[bool]) -> None:
    widened: Option[int] = option
    assert widened is option


def test_some_of_none_is_a_some() -> None:
    option: Option[None] = Some(None)
    assert isinstance(option, Some)
    assert option != Nothing()


@pytest.mark.parametrize(
    ("option", "truth"),
    [
        (Some(0), True),
        (Some(None), True),
        (Some([]), True),
        (Nothing(), False),
    ],
)
def test_truthiness_tests_the_variant_not_the_content(
    option: Option[object], truth: bool
) -> None:
    assert bool(option) is truth


def test_is_some_and_is_nothing_return_bool_on_a_some() -> None:
    assert assert_type(Some(1).is_some(), bool) is True
    assert assert_type(Some(1).is_nothing(), bool) is False


def test_is_some_and_is_nothing_return_bool_on_nothing() -> None:
    assert assert_type(Nothing().is_some(), bool) is False
    assert assert_type(Nothing().is_nothing(), bool) is True


def test_is_some_filters_a_list_of_options() -> None:
    options: list[Option[int]] = [Some(1), Nothing(), Some(2)]
    somes = filter(lambda option: option.is_some(), options)
    assert list(somes) == [Some(1), Some(2)]


@pytest.mark.parametrize("option", [Some(1)])
def test_unwrap_and_expect_give_the_value_with_the_some_type(
    option: Option[int],
) -> None:
    assert assert_type(option.unwrap(), int) == 1
    assert assert_type(option.expect("port"), int) == 1


@pytest.mark.parametrize(
    ("option", "value"), [(Some(1), 1), (Nothing(), None)]
)
def test_unwrap_or_gives_the_value_or_the_default(
    option: Option[int], value: int | None
) -> None:
    assert assert_type(option.unwrap_or(None), int | None) == value


def default_port() -> int:
    return 8080


@pytest.mark.parametrize(
    ("option", "value"), [(Some(1), 1), (Nothing(), 8080)]
)
def test_unwrap_or_else_gives_the_value_or_calls_the_function(
    option: Option[int], value: int
) -> None:
    assert assert_type(option.unwrap_or_else(default_port), int) == value


@pytest.mark.parametrize(
    ("call", "message"),
    [
        (
            lambda: Nothing().unwrap(),
            "called `Option.unwrap()` on a `Nothing` value",
        ),
        (lambda: Nothing().expect("port"), "port"),
    ],
)
def test_failed_call_raises_unwrap_error_with_only_the_message(
    call: Callable[[], object], message: str
) -> None:
    with pytest.raises(UnwrapError) as caught:
        call()
    assert (caught.value.args, vars(caught.value)) == ((message,), {})
