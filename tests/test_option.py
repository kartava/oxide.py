import copy
import pickle
from collections.abc import Callable
from operator import methodcaller
from typing import Never, assert_type
from unittest.mock import ANY

import pytest

from oxide import (
    Err,
    Nothing,
    Ok,
    Option,
    Result,
    Some,
    UnwrapError,
    from_optional,
)


def test_nothing_is_one_instance() -> None:
    assert Nothing() is Nothing()


@pytest.mark.parametrize(
    "protocol",
    [
        pytest.param(protocol, id=f"protocol {protocol} keeps the instance")
        for protocol in range(pickle.HIGHEST_PROTOCOL + 1)
    ],
)
def test_pickle_keeps_the_nothing_instance(protocol: int) -> None:
    assert pickle.loads(pickle.dumps(Nothing(), protocol)) is Nothing()


def test_deepcopy_keeps_the_nothing_instance() -> None:
    assert copy.deepcopy(Nothing()) is Nothing()


def test_pickle_round_trips_a_some() -> None:
    assert pickle.loads(pickle.dumps(Some([1]))) == Some([1])


def test_deepcopy_round_trips_a_some() -> None:
    assert copy.deepcopy(Some([1])) == Some([1])


@pytest.mark.parametrize(
    ("left", "right", "equal"),
    [
        pytest.param(Some(1), Some(1), True, id="equal somes are equal"),
        pytest.param(
            Some(1), Some(2), False, id="somes with different values differ"
        ),
        pytest.param(Nothing(), Nothing(), True, id="nothing equals nothing"),
        pytest.param(
            Some(None),
            Nothing(),
            False,
            id="a some of none differs from nothing",
        ),
        pytest.param(Some(1), Ok(1), False, id="a some differs from an ok"),
    ],
)
def test_equality_compares_variant_and_content(
    left: object, right: object, equal: bool
) -> None:
    assert (left == right) is equal


@pytest.mark.parametrize(
    "option",
    [
        pytest.param(Some(1), id="a some asks the other object"),
        pytest.param(Nothing(), id="nothing asks the other object"),
    ],
)
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
        pytest.param(Some(1), "Some(1)", id="a some shows its value"),
        pytest.param(Some(None), "Some(None)", id="a some of none shows none"),
        pytest.param(Nothing(), "Nothing()", id="nothing shows no value"),
    ],
)
def test_repr_shows_the_variant_and_content(
    option: Option[int | None], text: str
) -> None:
    assert repr(option) == text


@pytest.mark.parametrize(
    ("option", "attribute"),
    [
        pytest.param(
            Some(1), "value", id="setting the value of a some raises"
        ),
        pytest.param(Some(1), "extra", id="a new attribute on a some raises"),
        pytest.param(
            Nothing(), "extra", id="a new attribute on nothing raises"
        ),
    ],
)
def test_assignment_raises_attribute_error(
    option: Option[int], attribute: str
) -> None:
    with pytest.raises(AttributeError):
        setattr(option, attribute, 2)


@pytest.mark.parametrize(
    "option",
    [
        pytest.param(Some(True), id="a some of a bool is an option of an int"),
        pytest.param(Nothing(), id="nothing is an option of an int"),
    ],
)
def test_option_is_covariant(option: Option[bool]) -> None:
    widened: Option[int] = option
    assert widened is option


def test_some_of_none_is_a_some() -> None:
    option: Option[None] = Some(None)
    assert isinstance(option, Some)
    assert option != Nothing()


@pytest.mark.parametrize(
    ("option", "message"),
    [
        pytest.param(
            Some(1),
            "Some has no truth value. Use match or isinstance.",
            id="bool of a some raises",
        ),
        pytest.param(
            Nothing(),
            "Nothing has no truth value. Use match or isinstance.",
            id="bool of nothing raises",
        ),
    ],
)
def test_bool_raises_type_error(option: Option[int], message: str) -> None:
    with pytest.raises(TypeError) as caught:
        bool(option)
    assert caught.value.args == (message,)


def test_is_some() -> None:
    assert assert_type(Some(1).is_some(), bool) is True
    assert assert_type(Nothing().is_some(), bool) is False


def test_is_nothing() -> None:
    assert assert_type(Some(1).is_nothing(), bool) is False
    assert assert_type(Nothing().is_nothing(), bool) is True


def test_is_some_filters_a_list_of_options() -> None:
    options: list[Option[int]] = [Some(1), Nothing(), Some(2)]
    somes = filter(lambda option: option.is_some(), options)
    assert list(somes) == [Some(1), Some(2)]


@pytest.mark.parametrize(
    "option", [pytest.param(Some(1), id="a some gives its value")]
)
def test_unwrap(option: Option[int]) -> None:
    assert assert_type(option.unwrap(), int) == 1


@pytest.mark.parametrize(
    "option", [pytest.param(Some(1), id="a some gives its value")]
)
def test_expect(option: Option[int]) -> None:
    assert assert_type(option.expect("port"), int) == 1


@pytest.mark.parametrize(
    ("option", "value"),
    [
        pytest.param(Some(1), 1, id="a some gives its value"),
        pytest.param(Nothing(), None, id="nothing gives the default"),
    ],
)
def test_unwrap_or(option: Option[int], value: int | None) -> None:
    assert assert_type(option.unwrap_or(None), int | None) == value


def default_port() -> int:
    return 8080


@pytest.mark.parametrize(
    ("option", "value"),
    [
        pytest.param(Some(1), 1, id="a some gives its value"),
        pytest.param(Nothing(), 8080, id="nothing calls the function"),
    ],
)
def test_unwrap_or_else(option: Option[int], value: int) -> None:
    assert assert_type(option.unwrap_or_else(default_port), int) == value


@pytest.mark.parametrize(
    ("call", "message"),
    [
        pytest.param(
            lambda: Nothing().unwrap(),
            "called `Option.unwrap()` on a `Nothing` value",
            id="unwrap on nothing gives the default message",
        ),
        pytest.param(
            lambda: Nothing().expect("port"),
            "port",
            id="expect on nothing gives the given message",
        ),
    ],
)
def test_failed_call_raises_unwrap_error_with_only_the_message(
    call: Callable[[], object], message: str
) -> None:
    with pytest.raises(UnwrapError) as caught:
        call()
    assert (caught.value.args, vars(caught.value)) == ((message,), {})


def half(number: int) -> float:
    return number / 2


@pytest.mark.parametrize(
    ("option", "mapped"),
    [
        pytest.param(Some(4), Some(2.0), id="a some maps its value"),
        pytest.param(Nothing(), Nothing(), id="nothing stays nothing"),
    ],
)
def test_map(option: Option[int], mapped: Option[float]) -> None:
    assert assert_type(option.map(half), Some[float] | Nothing) == mapped


def halve(number: int) -> Option[float]:
    return Nothing() if number % 2 else Some(number / 2)


@pytest.mark.parametrize(
    ("option", "chained"),
    [
        pytest.param(
            Some(4), Some(2.0), id="a some of an even number gives a some"
        ),
        pytest.param(
            Some(3), Nothing(), id="a some of an odd number gives nothing"
        ),
        pytest.param(Nothing(), Nothing(), id="nothing stays nothing"),
    ],
)
def test_and_then(option: Option[int], chained: Option[float]) -> None:
    replaced: Option[float] = option.and_then(halve)
    assert replaced == chained


def fallback_port() -> Option[int]:
    return Some(8080)


@pytest.mark.parametrize(
    ("option", "recovered"),
    [
        pytest.param(Some(1), Some(1), id="a some stays"),
        pytest.param(Nothing(), Some(8080), id="nothing calls the function"),
    ],
)
def test_or_else(option: Option[int], recovered: Option[int]) -> None:
    replaced: Option[int] = option.or_else(fallback_port)
    assert replaced == recovered


@pytest.mark.parametrize(
    ("option", "flat"),
    [
        pytest.param(
            Some(Some(1)), Some(1), id="a some of a some gives the inner some"
        ),
        pytest.param(
            Some(Nothing()), Nothing(), id="a some of nothing gives nothing"
        ),
        pytest.param(Nothing(), Nothing(), id="nothing stays nothing"),
    ],
)
def test_flatten_removes_one_level_of_nesting(
    option: Option[Option[int]], flat: Option[int]
) -> None:
    flattened: Option[int] = option.flatten()
    assert flattened == flat


NO_PORT = LookupError("no port")


@pytest.mark.parametrize(
    ("option", "result"),
    [
        pytest.param(Some(1), Ok(1), id="a some gives an ok"),
        pytest.param(Nothing(), Err(NO_PORT), id="nothing gives an err"),
    ],
)
def test_ok_or(option: Option[int], result: Result[int, LookupError]) -> None:
    converted = option.ok_or(NO_PORT)
    assert assert_type(converted, Ok[int] | Err[LookupError]) == result


def no_port() -> LookupError:
    return NO_PORT


@pytest.mark.parametrize(
    ("option", "result"),
    [
        pytest.param(Some(1), Ok(1), id="a some gives an ok"),
        pytest.param(Nothing(), Err(NO_PORT), id="nothing calls the function"),
    ],
)
def test_ok_or_else(
    option: Option[int], result: Result[int, LookupError]
) -> None:
    converted = option.ok_or_else(no_port)
    assert assert_type(converted, Ok[int] | Err[LookupError]) == result


def fail(*contents: object) -> Never:
    pytest.fail(f"called with {contents!r}")


@pytest.mark.parametrize(
    ("option", "method", "returned"),
    [
        pytest.param(
            Nothing(), "map", Nothing(), id="map on nothing returns nothing"
        ),
        pytest.param(
            Nothing(),
            "and_then",
            Nothing(),
            id="and_then on nothing returns nothing",
        ),
        pytest.param(
            Some(1),
            "or_else",
            Some(1),
            id="or_else on a some returns the some",
        ),
        pytest.param(
            Some(1),
            "ok_or_else",
            Ok(1),
            id="ok_or_else on a some returns an ok",
        ),
    ],
)
def test_callback_on_the_other_variant_is_not_called(
    option: Option[int], method: str, returned: object
) -> None:
    assert methodcaller(method, fail)(option) == returned


@pytest.mark.parametrize(
    ("option", "value"),
    [
        pytest.param(Some(1), 1, id="a some gives its value"),
        pytest.param(Nothing(), None, id="nothing gives none"),
    ],
)
def test_to_optional(option: Option[int], value: int | None) -> None:
    assert assert_type(option.to_optional(), int | None) == value


def test_to_optional_of_some_none_is_none() -> None:
    assert Some(None).to_optional() is None


@pytest.mark.parametrize(
    ("value", "option"),
    [
        pytest.param(0, Some(0), id="zero gives a some"),
        pytest.param(None, Nothing(), id="none gives nothing"),
    ],
)
def test_from_optional(value: int | None, option: Option[int]) -> None:
    assert assert_type(from_optional(value), Option[int]) == option


@pytest.mark.parametrize(
    ("option", "result"),
    [
        pytest.param(
            Some(Ok(1)),
            Ok(Some(1)),
            id="a some of an ok gives an ok of a some",
        ),
        pytest.param(
            Some(Err("x")), Err("x"), id="a some of an err gives the err"
        ),
        pytest.param(
            Nothing(), Ok(Nothing()), id="nothing gives an ok of nothing"
        ),
    ],
)
def test_transpose(
    option: Option[Result[int, str]], result: Result[Option[int], str]
) -> None:
    transposed: Result[Option[int], str] = option.transpose()
    assert transposed == result
