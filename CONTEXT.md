# oxide.py

Rust's `Option<T>` and `Result<T, E>` for Python. A function returns one of them, so that an absent value or an expected failure is part of its type.

## Language

### Types and variants

**Option**:
A value that is either a Some or Nothing.
_Avoid_: Maybe (the Haskell and `returns` word), optional (`Optional[T]` means `T | None`, not an Option)

**Some**:
The variant of an Option that holds a value. The value can be Python's `None`: `Some(None)` is a Some, not Nothing.

**Nothing**:
The variant of an Option that holds no value. `Nothing()` always returns the same instance.
_Avoid_: None (Python's `None`), Empty (it suggests an empty container), Nil (another language's word)

**Result**:
A value that is either an Ok or an Err.
_Avoid_: Either (it has no success side), outcome (too vague)

**Ok**:
The variant of a Result that holds the success value. An Ok can hold `None`, as `Ok(())` does in Rust.
_Avoid_: Success (the `returns` name)

**Err**:
The variant of a Result that holds an expected failure: a failure that the caller can act on. The failure can be any value, such as a string, an enum member or an exception instance.
_Avoid_: Failure (the `returns` name), error (it also means a raised exception)

**Variant**:
One of the two shapes of an Option or a Result: Some or Nothing, Ok or Err.
_Avoid_: case (the `match` keyword), subclass (it names an implementation)

### Use

**Unwrap**:
To take the value out of a Some or an Ok. On the other variant, unwrap raises.
_Avoid_: get (it suggests a default of `None`), extract (too general: it hides that the call can raise)

**Do function**:
A generator function under `@do`. In it, `yield from result.try_()` gives the value of an Ok, or returns the Err from the function.
_Avoid_: effect (Expression's word), try block (Python's `try`)

**Narrowing style**:
A way to branch on a variant that each picked type checker narrows in both branches. [README.md](README.md) lists the styles.
_Avoid_: guard (one mechanism, `TypeGuard` or `TypeIs`, not a style), check (too general: any `if` checks something)
