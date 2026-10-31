# Conventions

The files in this folder are the source of truth for code shapes. Code follows them.

## Rules

- Code that differs from a convention is the violation. Fix the code.
- A snippet shows a shape in the [placeholder domain](#placeholder-domain) and cites no source file.
- A convention changes only on a [trigger](#change-triggers), after the user [approves](#approval) it.
- These files belong to `oxide.py`. A change here does not go back to `projects/skills/conventions/`.
- Each convention file opens, under its title, with this line:

  ```markdown
  This file is normative. Read [README.md](README.md) before you change it.
  ```

## Change triggers

| Trigger | When |
|---|---|
| A new shape | Code needs a [new shape](#new-shape). Its convention lands in the same change. |
| A migration the user decides | The user moves every instance of a shape to a different one. |
| A factual-error fix | The file states something false about a tool, framework or library. |
| A dead-section removal | The file covers a file role, tool or entry point that the repo does not have. |

These are not triggers. The code changes and the convention stays:

- a renamed field
- an extra injected dependency
- a new use case of an existing shape

## New shape

A new shape is a new file-role suffix or folder role, or a structural variant of an existing shape: a different base class, decorator set, port or entry point.

## Approval

1. Ask the user with AskUserQuestion. Name the trigger, the file and the new text.
2. After the user approves, apply the edit with the Edit tool (Write for a new file), never with a shell write.

## Names

| Name | Where it appears |
|---|---|
| Tooling, config file names, and Python and standard-library names | Anywhere |
| A bounded-context name | Prose and tables only |
| A feature name | Nowhere |

No inventories: no lists of use cases, routes, topics, tables, modules or files.

## Snippets

- Rule first, then one minimal snippet.
- A good/bad pair only for a known mistake.
- Every domain name comes from the placeholder domain.

## Placeholder domain

| Context | Terms |
|---|---|
| `orders` | `Order`, the aggregate. `OrderLine`, one line of an order. `Quantity`, the value object on `OrderLine.quantity`. Statuses: `cart → submitted → shipped → cancelled`. The cancellation window: how long a submitted `Order` can still be cancelled. The order feed: a live feed of `Order` status changes. |
| `shipping` | `Shipment`, the aggregate. `ShippingOrder`, the replica of an order it ships (table `shipping__orders`), synced from `orders` events. Shipment events: Kafka messages that an outside system sends about a `Shipment`. |

A new term goes in this table before a snippet uses it. It matches no real symbol in `oxide.py`.

A name built from a term and a role suffix (`OrderEntity`, `ShipmentSource`) needs no row of its own.

Reasoning and rejected options: `spectre-api/docs/adr/0003-conventions-are-normative.md`.
