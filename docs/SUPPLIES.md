# Supply tracking and reordering

The robot keeps count of everyday consumables, sets them out alongside your
clothes when you want, tells you when stock is getting low, and can stage a
reorder on your Amazon shopping list. It is built so the helpful parts are
automatic and the spending part stays under your control.

## Tracking stock

Each consumable is tracked with a count on hand, a reorder point, and
optionally a daily-use figure so the robot can estimate days remaining.

```text
$ karakuri supplies
  vacuum_filters: 10 on hand (reorder at 12), ~1.2 days left  LOW, reorder
  mop_pads: 20 on hand (reorder at 4)
```

Stock goes down as items are used or set out and goes back up when an order
arrives (`restock`). The file lives on the robot in `memory/supplies.json`.

## Setting them out with your clothes

A consumable can be set out alongside an outfit. Add it to your wardrobe under
`set_out_with_clothes`, and it becomes another fetch-and-place step on the
same surface as your pajamas or day clothes:

```text
wardrobe:
  set_out_with_clothes:
    - { label: fresh sleep mask, location: supply_bin, supply: sleep_masks }
```

Like everything in the clothing layer, this is retrieval to a surface and
nothing more. The robot brings the item to your bed or chair; it never
handles or dresses a person. The `supply` field links the item to its stock
entry so setting it out keeps the count honest.

## Reordering, with you in the loop

When something hits its reorder point, the robot raises a request. What
happens next depends on a policy you set, and the default is the safe one.

| Mode | What it does |
|------|--------------|
| `list_only` (default) | Adds the item to your Amazon shopping list, a staging area you review. Never buys. |
| `auto_buy` | Places the order, but only under a per-item price ceiling and a cooldown so the same item cannot be ordered twice in a short window. |
| `off` | Records the need locally and does nothing automatic. |

```text
$ karakuri reorder --mode list_only
reorder policy: list_only
  vacuum_filters: queued_local
items added to the reorder queue for your Amazon list; review before buying
```

Low stock also shows up on its own through the autonomy layer, so the robot
brings it to your attention rather than waiting to be asked.

### How the Amazon connection works, and the honest caveat

This module never embeds your Amazon credentials and never talks to a
hardcoded endpoint. It calls a local helper you configure, for example a
small script that drives the official Amazon API or a browser automation you
run on the chest computer. If you set no helper, requests are written to a
local queue you act on by hand.

The honest caveat on fully hands-off buying: Amazon does not offer a simple,
officially supported way for a personal device to silently place arbitrary
orders. The reliable, supported path is adding to your shopping list. That is
why the default is `list_only` and why `auto_buy` is gated behind a price
ceiling and cooldown: even when you wire up automation, a sensor glitch or a
miscount should never be able to run up a bill. The robot is excellent at
noticing you are low and staging the order; the final click is a place to keep
a human, or a deliberate subscription, in the loop.

For a recurring consumable, the setup I would suggest: track it here so you
always know your runway, and put the actual resupply on a deliberate schedule
that you control. The robot's job becomes making sure the schedule is right,
not gambling on an unsupported checkout.

## Commands

| Command | Does |
|---------|------|
| `karakuri supplies` | Show stock and what is low |
| `karakuri reorder --mode list_only` | Stage low items on your Amazon list |
| `karakuri reorder --mode auto_buy --max-price 40` | Order within limits, if you have enabled it |
