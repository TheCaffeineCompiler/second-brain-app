# The system boundary starts at text

ADR-0002 defines a Capture as a raw thought "unedited by the system", and transcription is
the system doing something — so on a strict reading the audio is the raw artifact and the
transcript is derived, which would make it regenerable, which would mean keeping audio in
Git. Ten minutes of speech is roughly 10MB; daily capture would put gigabytes of unprunable
binaries into history and wreck ADR-0001.

**The transcript is the Capture.** Transcription belongs to the capture device, not the
pipeline: it happens before an artifact exists, and audio never enters the Vault. Audio is
kept briefly in GCS — not Git — and deleted after a few weeks, as a backup for checking a
garbled transcript rather than as an artifact.

## Text is the input, not speech

Because the boundary is text, **voice is one input method rather than the system's premise**.
Typing a Capture at a desk, or in an office where dictating aloud is not an option, is the
same path with a different way of producing the text — not a degraded fallback. The
`Transcriber` port is therefore optional, and nothing downstream may assume speech occurred.

## Transcription runs locally

Local Whisper is chosen less for privacy and cost than for availability: capture happens in
cars, on walks and in corridors, and a hosted API needs connectivity exactly when it is
absent. A capture tool that fails offline gets abandoned.

The known weakness of local models is proper nouns, which would be severe here since entity
extraction depends on them. The mitigation is already in the design: Whisper accepts an
initial prompt used for vocabulary biasing, and the **Registry** is a curated list of exactly
the proper nouns the user talks about. Feeding it in makes the words used most transcribe
correctly by construction, and the transcriber improves as the Registry is curated.

## Consequences

**A Capture can never be re-transcribed with a better model.** This is survivable because a
Capture is decided and therefore human-owned: ADR-0002 forbids the *system* from editing it,
not the user. Correcting a mis-heard name changes `source_hash`, and the Note regenerates on
its own.
