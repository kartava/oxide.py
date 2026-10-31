import copy
import pickle
from collections.abc import Callable, Iterable
from operator import methodcaller
from typing import Never, assert_type
from unittest.mock import ANY

import pytest

from oxide import Err, Ok, Result, UnwrapError, collect, partition


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


@pytest.mark.parametrize("result", [Ok([1]), Err([2])])
def test_variant_is_not_iterable(result: Result[list[int], list[int]]) -> None:
    assert not isinstance(result, Iterable)


def test_is_ok_and_is_err_return_bool_on_an_ok() -> None:
    assert assert_type(Ok(1).is_ok(), bool) is True
    assert assert_type(Ok(1).is_err(), bool) is False


def test_is_ok_and_is_err_return_bool_on_an_err() -> None:
    assert assert_type(Err("x").is_ok(), bool) is False
    assert assert_type(Err("x").is_err(), bool) is True


def test_is_ok_filters_a_list_of_results() -> None:
    results: list[Result[int, str]] = [Ok(1), Err("x"), Ok(2)]
    oks = filter(lambda result: result.is_ok(), results)
    assert list(oks) == [Ok(1), Ok(2)]


@pytest.mark.parametrize("result", [Ok(1)])
def test_unwrap_and_expect_give_the_value_with_the_ok_type(
    result: Result[int, str],
) -> None:
    assert assert_type(result.unwrap(), int) == 1
    assert assert_type(result.expect("port"), int) == 1


@pytest.mark.parametrize("result", [Err("x")])
def test_unwrap_err_and_expect_err_give_the_error_with_the_err_type(
    result: Result[int, str],
) -> None:
    assert assert_type(result.unwrap_err(), str) == "x"
    assert assert_type(result.expect_err("port"), str) == "x"


@pytest.mark.parametrize(("result", "value"), [(Ok(1), 1), (Err("x"), None)])
def test_unwrap_or_gives_the_value_or_the_default(
    result: Result[int, str], value: int | None
) -> None:
    assert assert_type(result.unwrap_or(None), int | None) == value


@pytest.mark.parametrize(("result", "value"), [(Ok(1), 1), (Err("abc"), 3)])
def test_unwrap_or_else_gives_the_value_or_calls_the_function_on_the_error(
    result: Result[int, str], value: int
) -> None:
    assert assert_type(result.unwrap_or_else(len), int) == value


@pytest.mark.parametrize(
    ("call", "message"),
    [
        (
            lambda: Err("x").unwrap(),
            "called `Result.unwrap()` on an `Err` value: 'x'",
        ),
        (lambda: Err("x").expect("port"), "port: 'x'"),
        (
            lambda: Ok(1).unwrap_err(),
            "called `Result.unwrap_err()` on an `Ok` value: 1",
        ),
        (lambda: Ok(1).expect_err("port"), "port: 1"),
    ],
)
def test_failed_call_raises_unwrap_error_with_only_the_message(
    call: Callable[[], object], message: str
) -> None:
    with pytest.raises(UnwrapError) as caught:
        call()
    assert (caught.value.args, vars(caught.value)) == ((message,), {})


@pytest.mark.parametrize(
    "call", [methodcaller("unwrap"), methodcaller("expect", "port")]
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
    ("result", "mapped"), [(Ok(4), Ok(2.0)), (Err("x"), Err("x"))]
)
def test_map_calls_the_function_on_the_value_of_an_ok(
    result: Result[int, str], mapped: Result[float, str]
) -> None:
    assert assert_type(result.map(half), Ok[float] | Err[str]) == mapped


@pytest.mark.parametrize(
    ("result", "mapped"), [(Ok(1.5), Ok(1.5)), (Err("abc"), Err(3))]
)
def test_map_err_calls_the_function_on_the_error_of_an_err(
    result: Result[float, str], mapped: Result[float, int]
) -> None:
    assert assert_type(result.map_err(len), Ok[float] | Err[int]) == mapped


ODD_NUMBER = ValueError("odd number")


def halve(number: int) -> Result[float, ValueError]:
    return Err(ODD_NUMBER) if number % 2 else Ok(number / 2)


@pytest.mark.parametrize(
    ("result", "chained"),
    [(Ok(4), Ok(2.0)), (Ok(3), Err(ODD_NUMBER)), (Err("x"), Err("x"))],
)
def test_and_then_calls_the_function_on_the_value_of_an_ok(
    result: Result[int, str], chained: Result[float, str | ValueError]
) -> None:
    widened: Result[float, str | ValueError] = result.and_then(halve)
    assert widened == chained


NOT_A_NUMBER = ValueError("not a number")


def parse(text: str) -> Result[int, ValueError]:
    return Ok(int(text)) if text.isdigit() else Err(NOT_A_NUMBER)


@pytest.mark.parametrize(
    ("result", "recovered"),
    [(Ok(1), Ok(1)), (Err("8080"), Ok(8080)), (Err("x"), Err(NOT_A_NUMBER))],
)
def test_or_else_calls_the_function_on_the_error_of_an_err(
    result: Result[int, str], recovered: Result[int, ValueError]
) -> None:
    replaced: Result[int, ValueError] = result.or_else(parse)
    assert replaced == recovered


def fail(content: object) -> Never:
    pytest.fail(f"called with {content!r}")


@pytest.mark.parametrize(
    ("result", "method"),
    [
        (Err("x"), "map"),
        (Ok(1), "map_err"),
        (Err("x"), "and_then"),
        (Ok(1), "or_else"),
    ],
)
def test_transform_on_the_other_variant_returns_it_without_a_call(
    result: Result[int, str], method: str
) -> None:
    assert methodcaller(method, fail)(result) == result


@pytest.mark.parametrize(
    ("result", "flat"),
    [
        (Ok(Ok(1)), Ok(1)),
        (Ok(Err("x")), Err("x")),
        (Err(NOT_A_NUMBER), Err(NOT_A_NUMBER)),
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
        ([Ok(1), Ok(2)], Ok([1, 2])),
        ([Ok(1), Err("x"), Ok(2), Err("y")], Err("x")),
        ([], Ok([])),
    ],
)
def test_collect_gives_all_values_or_the_first_err(
    results: list[Result[int, str]], collected: Result[list[int], str]
) -> None:
    assert assert_type(collect(results), Result[list[int], str]) == collected


def test_partition_gives_the_values_and_the_errors_in_input_order() -> None:
    results: list[Result[int, str]] = [Ok(1), Err("x"), Ok(2), Err("y")]
    values, errors = partition(results)
    assert assert_type(values, list[int]) == [1, 2]
    assert assert_type(errors, list[str]) == ["x", "y"]
