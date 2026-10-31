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
    *exceptions: type[BaseException],
) -> Callable[[Callable[P, R]], Callable[P, Result[R, BaseException]]]:
    """Turn the listed exceptions of a function into an Err.

    Raise `TypeError` for no type, `Exception` or `BaseException`.
    """
    if not exceptions:
        raise TypeError("catch() got no exception type")
    for exception in exceptions:
        if exception in (Exception, BaseException):
            raise TypeError(
                "catch() converts expected exceptions only,"
                f" not {exception.__name__}"
            )

    def decorator(
        function: Callable[P, R],
    ) -> Callable[P, Result[R, BaseException]]:
        @functools.wraps(function)
        def wrapper(
            *args: P.args, **kwargs: P.kwargs
        ) -> Result[R, BaseException]:
            try:
                return Ok(function(*args, **kwargs))
            except exceptions as error:
                return Err(error)

        return wrapper

    return decorator
