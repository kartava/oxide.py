# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`oxide.py` ports Rust's `Option<T>` and `Result<T, E>` to Python. It must beat the existing libraries on three points: type narrowing, no type-checker plugin, and maintenance.

The repo has no package code yet. The design doc in `docs/` defines the v1 API.

## Rules

- IMPORTANT: Build every ticket test-first with the `tdd` skill. `/sdlc apply` turns on `tdd` only when the user asks.
- Run Python and every Python tool only through `.venv/bin/python`, the project venv. Install packages with `.venv/bin/python -m pip`. Then each tool runs with the same Python and packages. The one exception: pre-commit runs its hook tools in its own cached envs, so that each contributor gets the same tools.
- Add no public API outside the list in the design doc. v1 must stay small enough to read in one pass.
- Ask before any PyPI upload or GitHub release. Both are public, and PyPI does not accept the same version twice.

## Commands

Create `.venv` once per clone with `python3 -m venv .venv`, or link an existing env to `.venv`. Then run each tool as a module of its Python.

```sh
.venv/bin/python -m pip install ruff==0.17.3 pre-commit  # dev tools
.venv/bin/python -m pre_commit install                   # once per clone
.venv/bin/python -m ruff format .                        # format
.venv/bin/python -m ruff check .                         # lint
.venv/bin/python -m pytest                               # all tests
.venv/bin/python -m pytest <file>::<test_name>           # one test
.venv/bin/python -m pre_commit run --all-files           # all hooks
```

The pre-commit hook checks the staged files and never writes a file. It runs `ruff format --check`, `ruff check`, and checks for TOML and YAML syntax, merge-conflict markers, large files, trailing whitespace and the final newline. A failed hook stops the commit. Fix the files, then stage them again. `.pre-commit-config.yaml` pins each hook repo with `rev`. Keep the Ruff `rev` equal to the Ruff version in `.venv`.

## Tests

- Plain pytest tests check runtime behavior.
- `assert_type` files check narrowing. They prove that each narrowing style in `README.md` narrows both branches, for `Option` and `Result`, on each type checker that the design doc picks.
- Each picked checker reports zero errors on the package and the `assert_type` files. Run the checkers with no plugin and no library-specific config.
- CI (GitHub Actions) tests each supported Python version. A local run tests only the `.venv` version.

## Docs and conventions

- `docs/conventions/` is normative. Read its `README.md` before you change a file there.
- `docs/conventions/python.md` gives the Ruff rules and the Python rules that Ruff cannot check. `pyproject.toml` holds the Ruff config.
- `docs/conventions/local-artifacts.md` gives the location of the design doc, the ADRs, `tickets.md` and the glossary `CONTEXT.md`.
- Branch names, commit subjects and PR titles follow `docs/conventions/git.md`.
