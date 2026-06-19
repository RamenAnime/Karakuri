# Setting out home clothes

When the robot recognizes someone arriving home, it can fetch their usual
home clothes or sleepwear and lay them out on a surface so they are ready.
This is the same safe pick-and-place the arm already does: fetch a labeled
item from a known spot, set it down on a flat surface. The robot never
handles, dresses, or touches the person. They change themselves, in private,
exactly as before. The robot only saves them the trip to the dresser.

## What it does

```text
$ karakuri wardrobe --person Sam --surface bed
Setting out Sam's sleepwear on the bed: pajama top, pajama bottoms, robe.
  fetch pajama top from drawer_3, place on bed (grip: plush)
  fetch pajama bottoms from drawer_3, place on bed (grip: plush)
  fetch robe from closet_hook, place on bed (grip: plush)
```

It chooses which set by time of day from the person's own configured
outfits: evening and later default to sleepwear, daytime to home day wear.
The trigger phrase "set out my pajamas" (and "lay out my clothes", and
similar) routes through the reasoner, and it can also run automatically as a
step in relax mode.

## You teach it what you wear

Nothing is assumed about anyone's body or clothing. The robot only knows the
labels and storage spots a person configures themselves, stored with their
profile on the robot. The shape, under a person's preferences:

```text
wardrobe:
  layout_surface: bed
  outfits:
    home_day:
      - { label: soft tee,     location: drawer_2 }
      - { label: lounge pants, location: drawer_2 }
    sleepwear:
      - { label: pajama top,    location: drawer_3 }
      - { label: pajama bottoms, location: drawer_3 }
      - { label: robe,          location: closet_hook }
  window_map:        # optional: override which outfit a time window uses
    evening: sleepwear
```

Each item names a label and the location the gripper fetches from. Soft home
clothing uses the plush grip preset by default. A person with nothing
configured gets no guesses, just a prompt to set it up.

## The boundary, again

This feature is object retrieval to a surface and stops there. The step
library has no action that dresses or handles a person, by design. The robot
lays your pajamas on the bed; settling in is yours. That line is the same one
the relax routine holds, and it is enforced in the code, not just described
here.

## Commands

| Command | Does |
|---------|------|
| `karakuri wardrobe --person NAME` | Set out that person's home clothes for the current time of day |
| `karakuri wardrobe --person NAME --surface "reading chair"` | Lay them on a chosen surface |

To run it automatically when someone arrives, set `set_out_clothes: true` in
their preferences and it becomes a step in relax mode.
