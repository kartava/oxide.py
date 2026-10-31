# A do function with `try_()` replaces Rust's `?`

Python has no `?` operator. A do function, a generator function under `@do`, takes its place: `x = yield from r.try_()` gives the value of an Ok, or returns the Err from the function. mypy, pyright, ty and pyrefly infer `x` and report each Err type that the annotation `Do[T, E]` leaves out.

## Considered Options

- **Plain `yield from r`, through `__iter__`.** Rejected: pyright and pyrefly infer `x` as `Unknown`, and an iterable Ok or Err surprises a reader.
- **`x = r.q()`, with `@propagate` and a private exception.** Rejected: no checker reports an Err type outside the declared one, and a `.q()` call outside the decorator raises the private exception.
- **No `?` substitute.** Rejected: a chain of `and_then` calls hides the order of the steps, which the research doc's open question asks the library to solve.

## Consequences

- Ok and Err have no `__iter__`, so neither is iterable.
- A `try`/`except BaseException`, or a bare `except:`, around a `yield from` also catches the `GeneratorExit` that `@do` sends to close the generator. `except Exception` does not catch it.
