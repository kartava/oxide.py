import copy
import pickle
from collections.abc import Callable, Iterable
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
    collect,
    partition,
)


@pytest.mark.parametrize(
    ("result", "attribute"),
    [
        pytest.param(Ok(1), "value", id="setting the value of an ok raises"),
        pytest.param(
            Err("x"), "error", id="setting the error of an err raises"
        ),
        pytest.param(Ok(1), "extra", id="a new attribute on an ok raises"),
        pytest.param(Err("x"), "extra", id="a new attribute on an err raises"),
    ],
)
def test_assignment_raises_attribute_error(
    result: Result[int, str], attribute: str
) -> None:
    with pytest.raises(AttributeError):
        setattr(result, attribute, 2)


@pytest.mark.parametrize(
    "result",
    [
        pytest.param(Ok(True), id="an ok of a bool is a result of an int"),
        pytest.param(
            Err(ValueError("x")),
            id="an err of a value error is a result of an exception",
        ),
    ],
)
def test_result_is_covariant(result: Result[bool, ValueError]) -> None:
    widened: Result[int, Exception] = result
    assert widened is result


@pytest.mark.parametrize(
    ("left", "right", "equal"),
    [
        pytest.param(Ok(1), Ok(1), True, id="equal oks are equal"),
        pytest.param(
            Ok(1), Ok(2), False, id="oks with different values differ"
        ),
        pytest.param(Err("x"), Err("x"), True, id="equal errs are equal"),
        pytest.param(
            Err("x"), Err("y"), False, id="errs with different errors differ"
        ),
        pytest.param(Ok(1), Err(1), False, id="an ok and an err differ"),
    ],
)
def test_equality_compares_variant_and_content(
    left: Result[int, object], right: Result[int, object], equal: bool
) -> None:
    assert (left == right) is equal


@pytest.mark.parametrize(
    "result",
    [
        pytest.param(Ok(1), id="an ok asks the other object"),
        pytest.param(Err("x"), id="an err asks the other object"),
    ],
)
def test_equality_with_another_class_asks_the_other_object(
    result: Result[int, str],
) -> None:
    assert result == ANY


def test_hash_matches_equality() -> None:
    assert {Ok(1), Ok(1), Err(1), Err(1)} == {Ok(1), Err(1)}


@pytest.mark.parametrize(
    "result",
    [
        pytest.param(Ok([1]), id="an ok of a list is unhashable"),
        pytest.param(Err([1]), id="an err of a list is unhashable"),
    ],
)
def test_unhashable_content_makes_the_variant_unhashable(
    result: Result[list[int], list[int]],
) -> None:
    with pytest.raises(TypeError):
        hash(result)


@pytest.mark.parametrize(
    ("result", "text"),
    [
        pytest.param(Ok(1), "Ok(1)", id="an ok shows its value"),
        pytest.param(Err("x"), "Err('x')", id="an err shows its error"),
    ],
)
def test_repr_shows_the_variant_and_content(
    result: Result[int, str], text: str
) -> None:
    assert repr(result) == text


@pytest.mark.parametrize(
    "result",
    [
        pytest.param(Ok([1]), id="an ok round trips"),
        pytest.param(Err([2]), id="an err round trips"),
    ],
)
def test_pickle_round_trips_the_variant(
    result: Result[list[int], list[int]],
) -> None:
    assert pickle.loads(pickle.dumps(result)) == result


@pytest.mark.parametrize(
    "result",
    [
        pytest.param(Ok([1]), id="an ok round trips"),
        pytest.param(Err([2]), id="an err round trips"),
    ],
)
def test_deepcopy_round_trips_the_variant(
    result: Result[list[int], list[int]],
) -> None:
    assert copy.deepcopy(result) == result


@pytest.mark.parametrize(
    "result",
    [
        pytest.param(Ok([1]), id="an ok is not iterable"),
        pytest.param(Err([2]), id="an err is not iterable"),
    ],
)
def test_variant_is_not_iterable(result: Result[list[int], list[int]]) -> None:
    assert not isinstance(result, Iterable)


def test_is_ok() -> None:
    assert assert_type(Ok(1).is_ok(), bool) is True
    assert assert_type(Err("x").is_ok(), bool) is False


def test_is_err() -> None:
    assert assert_type(Ok(1).is_err(), bool) is False
    assert assert_type(Err("x").is_err(), bool) is True


def test_is_ok_filters_a_list_of_results() -> None:
    results: list[Result[int, str]] = [Ok(1), Err("x"), Ok(2)]
    oks = filter(lambda result: result.is_ok(), results)
    assert list(oks) == [Ok(1), Ok(2)]


@pytest.mark.parametrize(
    "result", [pytest.param(Ok(1), id="ok gives its value")]
)
def test_unwrap(result: Result[int, str]) -> None:
    assert assert_type(result.unwrap(), int) == 1


@pytest.mark.parametrize(
    "result", [pytest.param(Ok(1), id="ok gives its value")]
)
def test_expect(result: Result[int, str]) -> None:
    assert assert_type(result.expect("port"), int) == 1


@pytest.mark.parametrize(
    "result", [pytest.param(Err("x"), id="err gives its error")]
)
def test_unwrap_err(result: Result[int, str]) -> None:
    assert assert_type(result.unwrap_err(), str) == "x"


@pytest.mark.parametrize(
    "result", [pytest.param(Err("x"), id="err gives its error")]
)
def test_expect_err(result: Result[int, str]) -> None:
    assert assert_type(result.expect_err("port"), str) == "x"


@pytest.mark.parametrize(
    ("result", "value"),
    [
        pytest.param(Ok(1), 1, id="ok gives its value"),
        pytest.param(Err("x"), None, id="err gives the default"),
    ],
)
def test_unwrap_or(result: Result[int, str], value: int | None) -> None:
    assert assert_type(result.unwrap_or(None), int | None) == value


@pytest.mark.parametrize(
    ("result", "value"),
    [
        pytest.param(Ok(1), 1, id="ok gives its value"),
        pytest.param(Err("abc"), 3, id="err calls the function on its error"),
    ],
)
def test_unwrap_or_else(result: Result[int, str], value: int) -> None:
    assert assert_type(result.unwrap_or_else(len), int) == value


@pytest.mark.parametrize(
    ("call", "message"),
    [
        pytest.param(
            lambda: Err("x").unwrap(),
            "called `Result.unwrap()` on an `Err` value: 'x'",
            id="unwrap on an err gives the default message",
        ),
        pytest.param(
            lambda: Err("x").expect("port"),
            "port: 'x'",
            id="expect on an err gives the given message",
        ),
        pytest.param(
            lambda: Ok(1).unwrap_err(),
            "called `Result.unwrap_err()` on an `Ok` value: 1",
            id="unwrap_err on an ok gives the default message",
        ),
        pytest.param(
            lambda: Ok(1).expect_err("port"),
            "port: 1",
            id="expect_err on an ok gives the given message",
        ),
    ],
)
def test_failed_call_raises_unwrap_error_with_only_the_message(
    call: Callable[[], object], message: str
) -> None:
    with pytest.raises(UnwrapError) as caught:
        call()
    assert (caught.value.args, vars(caught.value)) == ((message,), {})


@pytest.mark.parametrize(
    "call",
    [
        pytest.param(
            methodcaller("unwrap"), id="unwrap raises from the exception"
        ),
        pytest.param(
            methodcaller("expect", "port"),
            id="expect raises from the exception",
        ),
    ],
)
def test_failed_call_raises_from_an_exception_error(
    call: methodcaller,
) -> None:
    error = ValueError("x")
    with pytest.raises(UnwrapError) as caught:
        call(Err(error))
    assert caught.value.__cause__ is error


def test_unwrap_error_subclasses_exception() -> None:
    assert UnwrapError.__bases__ == (Exception,)


def half(number: int) -> float:
    return number / 2


@pytest.mark.parametrize(
    ("result", "mapped"),
    [
        pytest.param(Ok(4), Ok(2.0), id="ok maps its value"),
        pytest.param(Err("x"), Err("x"), id="err stays"),
    ],
)
def test_map(result: Result[int, str], mapped: Result[float, str]) -> None:
    assert assert_type(result.map(half), Ok[float] | Err[str]) == mapped


@pytest.mark.parametrize(
    ("result", "mapped"),
    [
        pytest.param(Ok(1.5), Ok(1.5), id="ok stays"),
        pytest.param(Err("abc"), Err(3), id="err maps its error"),
    ],
)
def test_map_err(
    result: Result[float, str], mapped: Result[float, int]
) -> None:
    assert assert_type(result.map_err(len), Ok[float] | Err[int]) == mapped


ODD_NUMBER = ValueError("odd number")


def halve(number: int) -> Result[float, ValueError]:
    return Err(ODD_NUMBER) if number % 2 else Ok(number / 2)


@pytest.mark.parametrize(
    ("result", "chained"),
    [
        pytest.param(Ok(4), Ok(2.0), id="ok of an even number gives an ok"),
        pytest.param(
            Ok(3), Err(ODD_NUMBER), id="ok of an odd number gives an err"
        ),
        pytest.param(Err("x"), Err("x"), id="err stays"),
    ],
)
def test_and_then(
    result: Result[int, str], chained: Result[float, str | ValueError]
) -> None:
    widened: Result[float, str | ValueError] = result.and_then(halve)
    assert widened == chained


NOT_A_NUMBER = ValueError("not a number")


def parse(text: str) -> Result[int, ValueError]:
    return Ok(int(text)) if text.isdigit() else Err(NOT_A_NUMBER)


@pytest.mark.parametrize(
    ("result", "recovered"),
    [
        pytest.param(Ok(1), Ok(1), id="ok stays"),
        pytest.param(Err("8080"), Ok(8080), id="err of a number gives an ok"),
        pytest.param(
            Err("x"), Err(NOT_A_NUMBER), id="err of a letter gives an err"
        ),
    ],
)
def test_or_else(
    result: Result[int, str], recovered: Result[int, ValueError]
) -> None:
    replaced: Result[int, ValueError] = result.or_else(parse)
    assert replaced == recovered


def fail(content: object) -> Never:
    pytest.fail(f"called with {content!r}")


@pytest.mark.parametrize(
    ("result", "method"),
    [
        pytest.param(Err("x"), "map", id="map on an err returns the err"),
        pytest.param(Ok(1), "map_err", id="map_err on an ok returns the ok"),
        pytest.param(
            Err("x"), "and_then", id="and_then on an err returns the err"
        ),
        pytest.param(Ok(1), "or_else", id="or_else on an ok returns the ok"),
    ],
)
def test_transform_on_the_other_variant_returns_it_without_a_call(
    result: Result[int, str], method: str
) -> None:
    assert methodcaller(method, fail)(result) == result


@pytest.mark.parametrize(
    ("result", "flat"),
    [
        pytest.param(Ok(Ok(1)), Ok(1), id="an ok of an ok gives the inner ok"),
        pytest.param(
            Ok(Err("x")), Err("x"), id="an ok of an err gives the inner err"
        ),
        pytest.param(Err(NOT_A_NUMBER), Err(NOT_A_NUMBER), id="an err stays"),
    ],
)
def test_flatten_removes_one_level_of_nesting(
    result: Result[Result[int, str], ValueError],
    flat: Result[int, str | ValueError],
) -> None:
    flattened: Result[int, str | ValueError] = result.flatten()
    assert flattened == flat


@pytest.mark.parametrize(
    ("results", "collected"),
    [
        pytest.param(
            [Ok(1), Ok(2)], Ok([1, 2]), id="all oks give an ok of the values"
        ),
        pytest.param(
            [Ok(1), Err("x"), Ok(2), Err("y")],
            Err("x"),
            id="errs give the first err",
        ),
        pytest.param([], Ok([]), id="empty list gives an ok of an empty list"),
    ],
)
def test_collect(
    results: list[Result[int, str]], collected: Result[list[int], str]
) -> None:
    assert assert_type(collect(results), Result[list[int], str]) == collected


def test_partition_gives_the_values_and_the_errors_in_input_order() -> None:
    results: list[Result[int, str]] = [Ok(1), Err("x"), Ok(2), Err("y")]
    values, errors = partition(results)
    assert assert_type(values, list[int]) == [1, 2]
    assert assert_type(errors, list[str]) == ["x", "y"]


@pytest.mark.parametrize(
    ("result", "option"),
    [
        pytest.param(Ok(1), Some(1), id="ok gives a some"),
        pytest.param(Err("x"), Nothing(), id="err gives nothing"),
    ],
)
def test_ok(result: Result[int, str], option: Option[int]) -> None:
    assert assert_type(result.ok(), Some[int] | Nothing) == option


@pytest.mark.parametrize(
    ("result", "option"),
    [
        pytest.param(Ok(1), Nothing(), id="ok gives nothing"),
        pytest.param(Err("x"), Some("x"), id="err gives a some"),
    ],
)
def test_err(result: Result[int, str], option: Option[str]) -> None:
    assert assert_type(result.err(), Nothing | Some[str]) == option


@pytest.mark.parametrize(
    ("result", "option"),
    [
        pytest.param(
            Ok(Some(1)), Some(Ok(1)), id="ok of a some gives a some of an ok"
        ),
        pytest.param(
            Ok(Nothing()), Nothing(), id="ok of nothing gives nothing"
        ),
        pytest.param(
            Err("x"), Some(Err("x")), id="err gives a some of the err"
        ),
    ],
)
def test_transpose(
    result: Result[Option[int], str], option: Option[Result[int, str]]
) -> None:
    transposed: Option[Result[int, str]] = result.transpose()
    assert transposed == option
