# Post-MVP Requirements

Deferred deliberately. Each entry records what was decided and why it waits.

## Inbound edit path ("add a thought while reading")

While reading a **Note**, the user can add a thought without leaving it. The thought is
written as a **new Capture** referencing that Note, and the Note regenerates to include it.

- In the PWA this is an explicit affordance in the reading view.
- In Obsidian there is no affordance, so drift detection catches the edit after the fact
  and demotes it into a Capture.

**Why deferred:** the MVP ships drift detection (ADR-0003), which makes the single-writer
invariant real. The demotion path is about removing friction, and how often that friction
actually bites is not yet known. Designing the UX before the habit exists is guessing.

**Prerequisite:** drift detection must be in place first — it is the mechanism the Obsidian
path relies on.
