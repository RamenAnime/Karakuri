# Talking to it, and it acting on its own

Two ways the robot takes work: you ask, or it decides. Both run through one
mission queue, both obey safety and battery first, and both record why every
mission started. Nothing here calls the cloud; the language understanding
runs on the chest computer.

## Just ask

`karakuri ask <plain words>` maps what you say to a skill, or tells you
honestly why it cannot.

```text
$ karakuri ask sweep the floor
Starting sweep floor.
  difficulty: moderate
  steps: ensure_map -> plan_coverage -> lower_brush -> sweep_route -> empty_bin -> return_to_dock

$ karakuri ask mop the floor
Starting mop floor.
  steps: ensure_map -> confirm_hard_floor -> fill_check -> wet_pad -> mop_route -> return_to_dock

$ karakuri ask help me carry this in from the car
I can plan carry in groceries but I am missing: person_tracker, outdoor_traverse.
```

On the robot, speech becomes text through Vosk or whisper.cpp, both fully
offline, both running on the 2014 mini. The text hits the same `match_skill`
the command uses. For free-form phrasing a small local LLM (Ollama, the
loopback-only hook already in `reasoner.py`) rewrites a sentence into one of
the known skills; the rule matcher is the floor, the LLM is the polish, and
neither needs internet.

## It acts on its own

`karakuri chores` shows what the robot would start with nobody asking.

```text
$ karakuri chores --since-vacuum 30
the robot would start, on its own:
  vacuum floor     priority 6  because 24h since last vacuum

$ karakuri chores --quiet --since-vacuum 50
nothing to do right now (quiet hours, low battery, or house is clean)
```

The triggers are conservative and legible, never a black box: time since the
last clean, a schedule window you set, and a dirt hint from vision. Every
self-started mission writes its reason to the audit log, so you can always
read back why the robot did something.

## The skill tiers, honestly

Skills carry a difficulty label so nothing is oversold.

| Skill | Tier | What it needs |
|-------|------|---------------|
| vacuum floor | solved | ships today |
| map home | solved | ships today |
| go charge | solved | ships today (the v0.4 dock) |
| sweep floor | moderate | print `sweeper_module`, one N20 motor, tuning |
| mop floor | moderate | print `mop_module`, a 5 V pump, a floor-type check |
| tidy toys | moderate | the arm, reliable enough grasping |
| fetch object | moderate | the arm plus navigate-to-person |
| carry in groceries | frontier | see below |

### Why "carry it in from the car" is the hard one

This single request hides four unsolved-at-hobby-level problems, and the
registry refuses it rather than fake it:

1. **Going outside.** The whole stack assumes one indoor floor with cliff
   sensors guarding stairs. A driveway has curbs, slopes, gravel, and sun
   that blinds the depth camera. Outdoor traverse is its own project.
2. **Following a person.** The robot must pick you out, keep you in view at
   walking pace, and not lose you at the door. Person tracking on a moving
   camera is doable but it is real work, a `person_tracker` capability the
   build does not yet have.
3. **Taking a bag and holding it.** A handover means feeling the weight
   transfer (the force-torque wrist helps here) and keeping a grip on a
   swinging, shifting load. That is the edge of what the printed arm can do.
4. **The threshold.** Rolling from driveway to door over a lip, maybe a
   step, while carrying weight, is exactly the case where the wheels stop
   helping and the legs are marginal.

The honest path to it, in order: solid indoor fetch first, then person
following indoors, then a force-felt handover, then short outdoor traverse on
smooth ground, and only then the full errand. Each is a milestone the skill
registry already names, so progress is measurable rather than mythical.

## The three floor tools share one mount

The vacuum nozzle, `sweeper_module`, and `mop_module` all bolt to the same
deck intake pattern (56 x 56 mm, M3), so changing the robot's floor job is a
four-bolt swap, not a rebuild. The coverage planner in
`karakuri/robot/coverage_plan.py` drives all three with the same
back-and-forth path; only the attachment and a couple of parameters change.

## New print plates

| Plate | Pieces | For |
|-------|--------|-----|
| sweeper_module | cradle, bin, end cap | sweep skill |
| mop_module | pad plate, water tank | mop skill |

Both in PETG, no supports, same intake bolt pattern as the vacuum nozzle.
