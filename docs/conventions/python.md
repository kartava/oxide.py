# Python

This file is normative. Read [README.md](README.md) before you change it.

Code follows PEP 8 and PEP 257. Ruff checks each rule it can, from `[tool.ruff]` in `pyproject.toml`. This file holds the rules that Ruff cannot check.

## Ruff

| Concern | Owner |
|---|---|
| Layout, quotes, wrap at 79 columns | `ruff format` |
| PEP 8 errors and warnings; docstrings and comments wrap at 72 | `E`, `W` |
| Import order; absolute imports only | `I`, `TID` |
| PEP 8 names; `_co` on a covariant `TypeVar` | `N`, `PLC0105` |
| PEP 257 docstring form | `D`, convention `pep257` |
| Annotations on every signature; a code on each `# type: ignore` | `ANN`, `PGH` |
| Unused code, bug patterns, simpler forms, current syntax, pytest style | `F`, `B`, `SIM`, `UP`, `RUF`, `PT` |

- `D1` is off. [comments.md](comments.md) decides which items get a docstring.
- `ANN401` is off. The design doc decides where `Any` is allowed.
- `target-version` is unset. Ruff reads `requires-python` from `pyproject.toml`.

## Names

A name that is a Python keyword takes a trailing underscore, as PEP 8 says. Do not pick a synonym.

```python
def or_(self, other: Quantity) -> Quantity: ...
```

## `__all__`

Each module whose name has no leading underscore sets `__all__`. It lists the public names of the module and nothing else.

```python
__all__ = ["Order", "OrderLine"]
```
