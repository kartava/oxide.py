# Variants have no truth value

`bool()` on an `Ok`, `Err`, `Some` or `Nothing` raises `TypeError`, and the message names `match` and `isinstance`. In Python, `if value:` usually asks whether `value` is empty, but `Some(0)`, `Some(None)` and `Ok([])` would be true, so a truthy variant hides bugs. `__bool__` returns `Never`, so pyright reports `if result:` statically. mypy, ty and pyrefly do not, so the `TypeError` reports it at runtime.

## Considered Options

- **`__bool__` returning `Literal[True]` or `Literal[False]`.** Rejected: it narrows on all four checkers, but `if option:` then reads as "not empty" and is true for `Some(0)`.
- **No `__bool__`.** Rejected: every variant is then true, so `if parse(text):` passes silently on an `Err`.
