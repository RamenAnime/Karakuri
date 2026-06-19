# Recognition and relax mode

The robot can learn who lives in the house, greet each person by name, load
their preferences, and run a personalized wind-down when asked. All of it
runs on the chest computer with nothing sent anywhere.

## It knows you, privately

Recognition uses a local face model (face_recognition or InsightFace, both
offline) to turn a face into a numeric embedding. The robot stores only that
embedding, never a photo, so the saved data cannot be turned back into an
image. The store lives in `memory/people.json` on the robot and supports a
one-call wipe.

```text
$ karakuri who
  Sam: 3 face sample(s), preferred_name=Sam, drink=chamomile tea, music=True
```

Three privacy rules are built into the code, not just promised here:

1. **Faces never leave the robot.** No upload path exists; the embedding
   file is local.
2. **Photos are never kept.** Only the math representation is stored.
3. **Forgetting is real.** `PeopleStore.forget(name)` removes one person and
   `wipe()` erases everyone; after the next save the data is gone.

Recognition is conservative on purpose: a match must clear a distance
threshold, and anything past it is reported as unknown so the robot asks
rather than greeting the wrong person by the wrong name.

### Enrolling

On the robot, enrollment captures a few embeddings of a willing person who
chooses to be recognized, and records their preferences. The preferences are
plain key-value pairs the rest of the system reads: `preferred_name`,
`drink`, `music`, `tidy_first`, and an optional `relax_steps` list to fully
customize the wind-down order.

## Relax mode

Say "let's go relax" (the reasoner recognizes several natural phrasings) and
the robot turns the room into a calm space and takes the small chores off
your hands. It personalizes from whoever it recognizes.

```text
$ karakuri relax --person Sam
Setting up relax mode for Sam. Bringing your chamomile tea.
  - Set the smart lights to a warm low level
  - Quick coverage pass to clear clutter from the floor
  - Bring the preferred drink from its usual spot
  - Start the wind-down playlist on the local speaker
  - Hold off on any noisy autonomous chores
  - Park nearby and wait quietly in case you need something
```

Every step is backed by a capability the robot already has and acts on the
room or brings something to you. The routine adjusts to preferences: a drink
named in your profile becomes a fetch step, music can be turned off, and the
tidy pass can be skipped. An unrecognized face gets a sensible default
routine and a gentle nudge to enroll.

The wind-down also flips the autonomy layer into quiet hours, so the robot
will not start a noisy chore while you are settling in.

## What this layer does not do

The relax routine acts on the environment and fetches objects. It does not
perform physical caretaking of a person. That boundary is deliberate and is
reflected in the step library: there is no step that handles, dresses, or
feeds a human, because a machine cannot read a person's state or respond to
distress, and intimate physical assistance is not something to hand to an
autonomous robot. The good version of "take care of me" that the robot can
genuinely deliver is a calm room, a tidy floor, a warm drink within reach,
and quiet company, which is what relax mode provides.

## Commands

| Command | Does |
|---------|------|
| `karakuri who` | List recognized people and their preferences |
| `karakuri relax` | Run the wind-down with the default routine |
| `karakuri relax --person NAME` | Run it personalized for a recognized person |

Recognition pairs naturally with the rest of the stack: a greeted person's
preferences can pick which room to clean, what music to play, or how the
robot prioritizes its chores.
