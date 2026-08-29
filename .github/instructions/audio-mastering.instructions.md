---
applyTo: "src/genre_test/mastering/**,src/genre_test/technical/**,docs/mastering/**,config/mastering/**,tests/**mastering**,tests/**technical**"
---

Read `AGENTS.md` and preserve the Genre_test audio/mastering ownership boundaries.

For DSP and mastering changes:

- distinguish measured evidence, engineering interpretation, and listening preference;
- source audio is immutable; compare derived candidates against a traceable source/reference;
- backend-neutral transient, mono/stereo, loudness, codec, and comparison metrics belong in shared technical/QC code;
- Ozone-specific XML, ParamID/schema/build guards, ElementChain/module order, preset construction, and REAPER/Ozone render orchestration belong under the mastering/Ozone boundary;
- do not create a second active mastering meter inside Ozone-specific code;
- full-mix onset detection is not drum-stem separation; do not overclaim source identity from rendered stereo audio;
- preserve bypass/original as a valid winning candidate;
- treat lossy-source limitations separately from processing damage.

For Ozone 12 Advanced, module order is semantically significant. Changes to chain order must be explicit and reviewed for phase, transient/sustain balance, dynamics, harshness, stereo width, downstream Dynamic EQ/de-essing, and Maximizer/True Peak interaction.

Safe default reasoning order:

```text
preparatory correction / balance
-> tonal EQ
-> gentle dynamics / transient processing
-> harshness control / stabilization
-> stereo processing
-> final Dynamic EQ / de-essing
-> Maximizer / True Peak limiter
```

Protect focused transient attack and avoid uncontrolled sustain widening. REAPER is the render host. Ozone/REAPER must remain optional and must not become dependencies of ordinary analysis/retrieval startup.

Independent `AUDIO_SCIENCE` review is mandatory before `READY-MTD` for changes affecting DSP/audio-analysis semantics, restoration/repair/stem processing, loudness/True Peak, transient, stereo/mono, codec methodology, A/B/X audio comparison or level matching, mastering assumptions, Ozone XML/ParamID/ElementChain/module-order semantics, or REAPER/Ozone render/readback compatibility.

The Audio Science verdict must apply to the exact current PR head SHA. Any head change invalidates the old domain verdict and requires revalidation.
