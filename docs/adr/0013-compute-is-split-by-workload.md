# Compute is split by workload, and the read path lives in the client

The PRD names Cloud Run as the deployment target (§7), but that was inherited rather than
derived, and the system is two programs with opposite profiles. The pipeline is a long batch
job — hours during a replay, bottlenecked on LLM API latency, run nightly, needing the whole
Vault. The app is bursty and single-user, sensitive to first-paint latency, and needs query
answers rather than files. Forcing one compute choice to serve both is what made the read
path awkward.

**The pipeline runs as a Cloud Run Job.** Task timeouts measured in hours rather than the
request-scoped limits of a service, built-in retries and resumability — which ADR-0010
requires, since a corpus replay will be interrupted — triggered by Cloud Scheduler and
scaling to zero between runs.

**The app ships its read index to the client.** The PWA holds a SQLite index in the browser
(OPFS via wa-sqlite) and answers search, graph and review-list queries locally. The server
exists almost solely to commit decided state to Git.

This works because §3 puts semantic backlinking in the *pipeline*, not the app. Embeddings —
the bulk of any index — never need to reach the client at all. What the app queries is
full-text, graph edges and list state: tens of megabytes for a few thousand Notes.

## Considered Options

- **Cloud Run service holding a SQLite index downloaded from GCS** — no client complexity,
  but every session pays a cold start on a scale-to-zero personal app, and pinning
  `min-instances=1` costs roughly $10–20/month to avoid it.
- **A small Compute Engine VM with the checkout and index on persistent disk** — cheapest and
  never cold, and it collapses the most machinery, but it means operating a machine and makes
  the app stateful, violating the 12-Factor requirement in §7.

## Consequences

Reads are instant and work offline, which for a note-taking app is a feature rather than a
nicety. The interactive graph view in §6 is materially better client-side, with panning and
filtering that need no round trips.

Cloud Run scale-to-zero stops being a problem, because the service only handles rare,
deliberate writes where a second of commit latency is acceptable.

**The client index must be kept lean.** The temptation to push embeddings into it would undo
the entire rationale.

Every server process stays stateless and disposable, so 12-Factor holds.

The compute topology now mirrors ADR-0011: derived artifacts are produced by a batch job and
read from a local derived index, while the server's only real job is writing decided state.
