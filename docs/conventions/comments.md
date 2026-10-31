# Comments

This file is normative. Read [README.md](README.md) before you change it.

Default to zero comments. Code carries the _what_. A comment sits only above complex logic and carries a _why_ that no name can carry.

## The deletion test

Delete each comment you write. If the next reader gets the same fact from the names, types and control flow, leave it deleted. The name of a constant or a function counts: it carries the why that its words say. Run the test on every comment, not only on the ones you doubt.

## Never write these

**Restatement**: repeats the signature or the next line.

```python
# Ship the order                                    <- delete
order.ship()
```

**A comment in place of a name**: extract the name and delete the comment.

```python
# cancel an order not shipped within 14 days        <- delete
if age > 1_209_600:
    ...

# becomes:
if age > SHIPPING_DEADLINE:
    ...
```

**A why that a name already carries**: the name says it. Delete the comment.

```python
# The client clock can run ahead of the server clock    <- delete
CLOCK_SKEW_GRACE = timedelta(seconds=5)
```

**Section banners**: `# ---- Helpers ----`, `# === Public API ===`. The file layout carries the structure.

**Body narration**: `# 1. validate`, `# 2. persist` over the steps of a function. A function that needs a table of contents needs extracted functions.

**Changelog or attribution**: `# added by …`, `# changed 2026-01-04`. Git keeps this.

**Commented-out code**: delete it. Git keeps it.

## Earn a comment with

A comment sits only above complex logic, with one of these:

- A workaround for an upstream bug, or a provider, protocol or spec quirk. Name the source.
- An ordering constraint that the types do not enforce.
- A deliberate performance or back-pressure tradeoff.
- A short block above an algorithm, bit manipulation or a state machine that tells the approach, not the steps.
- `TODO:` or `FIXME:` with a ticket ref.

A threshold, a guard, a default or a fallback is simple code. Its name carries its why.

```python
# The shipping replica can lag behind orders. Read the status from the
# event, not from the replica.
```

A tool pragma (`# noqa: E501`, `# type: ignore[arg-type]`) is not a comment. The deletion test does not apply to it.

## Docstrings

Write a docstring only on a public item whose contract neither the signature nor a short body shows: what triggers it, what it rejects, and why. A docstring that repeats the name, or a condition that the body states in one line, fails the deletion test. Ruff checks the PEP 257 form.

```python
"""Return the order status."""  # <- delete

"""Args: order_id: The order id."""  # <- delete

"""Reject a shipped order. Its shipment already exists."""
```

## STE Style

A comment that earns its place follows ASD-STE100 (Simplified Technical English):

- **Short sentences, one idea each.** Split a sentence that a comma, semicolon or dash joins.
- **Active voice.** Say who does what: "The callback records the shipment", not "The shipment is recorded by the callback".
- **Imperative for rules.** "Do not retry here", not "Retrying here is not recommended".
- **Plain, consistent words.** Say the same thing the same way each time. Do not swap in a synonym.

```python
# before: one chained sentence, passive voice
# The status is read again after the lock is taken, since a cancel can be
# committed by another request between the first read and the lock.

# after: short sentences, active voice
# Read the status again after the lock. Another request can cancel the
# order between the first read and the lock.
```

Apply STE Style only to a comment that passes the deletion test and falls under "Earn a comment with".

## In review

Each comment in the diff passes the deletion test, falls under "Earn a comment with" or "Docstrings", and follows STE Style. Flag each one that does not, with the fix: delete it, extract a name, or rewrite it.
