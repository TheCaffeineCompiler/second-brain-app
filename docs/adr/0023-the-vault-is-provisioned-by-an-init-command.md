# The Vault is provisioned by an init command, under a separate credential

The Vault — the user's actual notes — lives in its own private repository, independent of this
application repository. Provisioning it is part of application initialization rather than a
manual checklist: `init` creates the private repository, applies branch protection, seeds the
OKF bundle skeleton, and records the repository as configuration (12-factor), so the Vault's
location is never hardcoded.

## Two credentials, not one

Creating a repository and setting branch protection require far broader scopes than committing
to a known repository. Sharing one credential would leave the nightly Cloud Run Job
permanently holding rights to create and delete repositories, when its only legitimate need is
pushing to one.

- **Bootstrap credential** — held by the operator locally, used once by `init`, never deployed.
- **Runtime credential** — scoped to the Vault repository alone; the only one that reaches
  Cloud Run.

This also settles where `init` runs: it is an operator command on a workstation, not something
the deployed application is capable of performing.

## Initialization is not destructive

An `init` that force-seeds over an existing Vault destroys decided artifacts, which are
irreplaceable (ADR-0011) — the same unrecoverable failure as a force-push, under a friendlier
name. `init` must therefore detect an existing Vault and refuse, seeding only what is genuinely
absent.

## Consequences

The seeded skeleton establishes the derived/decided regions from the outset, including an empty
human-written `registry.md` and the `log.md` that OKF reserves for chronological history
(ADR-0015, ADR-0019).

Branch protection — blocking force-push and branch deletion — is applied by `init` rather than
left to a manual step, so a Vault cannot exist in an unprotected state.

## Amendment: branch protection is not available

Provisioning the real Vault showed that GitHub refuses branch protection on a private
repository without a paid plan: *"Upgrade to GitHub Pro or make this repository public
to enable this feature."* Making the Vault public is not an option — it holds personal
notes — so the platform cannot enforce the guarantee ADR-0019 relies on.

`init` therefore treats protection as best-effort: it attempts it, and when refused it
reports loudly that force-push is **not** blocked rather than failing or passing
silently. The guard moves into the code instead, which is arguably the better place for
it since it sits at the point of action: no module may pass `--force`, `--force-with-lease`
or `--mirror` to git, asserted over the source as an executable invariant.

If the Vault ever warrants it, GitHub Pro restores platform-level enforcement and the
code guard remains as a second layer.
