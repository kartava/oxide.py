# Git

This file is normative. Read [README.md](README.md) before you change it.

## Branches

`<prefix>/<slug>`. The prefix is `feature`, `fix`, `refactor` or `chore`. The slug is 2 to 6 kebab-case words that name the topic, not the ticket title.

```
feature/order-cancellation
fix/shipment-refresh-on-reconnect
```

## PR titles and commits

A PR title and a commit subject start with a third-person present verb, such as `Adds`, `Fixes`, `Updates` or `Removes`, and name the net change. A PR squashes to one commit, so its title describes the change, not the steps to it.

```
Adds order cancellation to the orders module
Fixes the shipment refresh after a reconnect
```

Bad:

```
Add order cancellation
feat: order cancellation
```
