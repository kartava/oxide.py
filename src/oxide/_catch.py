import functools
from collections.abc import Callable
from typing import ParamSpec, TypeVar, overload

from oxide._core import Err, Ok, Result

P = ParamSpec("P")
R = TypeVar("R")
X1 = TypeVar("X1", bound=Exception)
X2 = TypeVar("X2", bound=Exception)
X3 = TypeVar("X3", bound=Exception)


@overload
def catch(
    exception_1: type[X1], /
) -> Callable[[Callable[P, R]], Callable[P, Result[R, X1]]]: ...
@overload
def catch(
    exception_1: type[X1], exception_2: type[X2], /
) -> Callable[[Callable[P, R]], Callable[P, Result[R, X1 | X2]]]: ...
@overload
def catch(
    exception_1: type[X1], exception_2: type[X2], exception_3: type[X3], /
) -> Callable[[Callable[P, R]], Callable[P, Result[R, X1 | X2 | X3]]]: ...
def catch(
    *exceptions: object,
) -> Callable[[Callable[P, R]], Callable[P, Result[R, Exception]]]:
    """Turn the listed exceptions of a function into an Err.

    Raise `TypeError` for no type, for `Exception`, and for a value
    that is not a subclass of `Exception`.
    """
    if not exceptions:
        raise TypeError("catch() got no exception type")
    expected = tuple(_expected(exception) for exception in exceptions)

    def decorator(
        function: Callable[P, R],
    ) -> Callable[P, Result[R, Exception]]:
        @functools.wraps(function)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> Result[R, Exception]:
            try:
                return Ok(function(*args, **kwargs))
            except expected as error:
                return Err(error)

        return wrapper

    return decorator


def _expected(exception: object) -> type[Exception]:
    name = getattr(exception, "__name__", repr(exception))
    if (
        isinstance(exception, type)
        and issubclass(exception, Exception)
        and exception is not Exception
    ):
        return exception
    raise TypeError(f"catch() converts expected exceptions only, not {name}")
