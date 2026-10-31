import functools
import inspect
import sys
from collections.abc import Callable, Generator
from typing import Any, ParamSpec

from oxide._core import E, Err, Ok, Result, T

if sys.version_info >= (3, 12):
    from typing import TypeAliasType
else:
    from typing_extensions import TypeAliasType

P = ParamSpec("P")

Do = TypeAliasType("Do", Generator[Err[E], Any, T], type_params=(T, E))


def do(
    function: Callable[P, Generator[Err[E], Any, T]],
) -> Callable[P, Result[T, E]]:
    """Make a do function return a Result in place of a generator.

    Raise `TypeError` when the function is not a generator function.
    """
    if not inspect.isgeneratorfunction(function):
        raise TypeError(f"{function!r} is not a generator function")

    @functools.wraps(function)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> Result[T, E]:
        generator = function(*args, **kwargs)
        try:
            error = next(generator)
        except StopIteration as stop:
            return Ok(stop.value)
        generator.close()
        return error

    return wrapper
