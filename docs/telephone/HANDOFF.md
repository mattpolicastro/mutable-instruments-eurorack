# Phreak — hand-off (2026-10-21)

**State**
- Branch `telephone` (local only; clone of github.com/lylepmills/eurorack): stmlib
  vendored, `community/phreak` un-ignored, OpenSpec initialised, `BRIEF.md` with
  Matt's decisions.
- `spec/phreak-engine`: the OpenSpec change drafted by `specloop propose` from the
  brief — review before admitting.
- specloop manifest: `~/Projects/nightshift/specloop/manifests/plaits-phreak.toml`
  (stage + `plaits_lab.py check --full`; passes under the verify sandbox in ~5 s).

**Before admitting**
1. Review the drafted spec (scenario IDs, the HARMONICS zone values, cadences).
2. Write the trusted tone checks beside the manifest, keyed to the spec's scenario
   IDs: copy the candidate package, swap in trusted `tests/scenarios.json`
   entries (fixed HARMONICS per tone, TIMBRE 0, note 60 / 72, triggerHz 0 or >0),
   `plaits_lab.py render` each, and verify from the WAV (L = MAIN, R = AUX) with a
   Goertzel detector: the pair's energy at both frequencies vs the other DTMF
   frequencies, busy/ring on-off timing, burst length when triggered, octave
   transposition at note 72, AUX clean vs MAIN treated. Print `SCENARIO <id>` for
   each passing check; set `[coverage] step` to that step and add it to
   `mutation_steps` with `mutation_paths` on the package `src/**`.
3. Add a negative control (a deliberately wrong tone must fail the checks).
4. `uv run specloop admit specloop/manifests/plaits-phreak.toml` from ~/Projects/nightshift.

**After v1:** ARM compile (`check --full --arm`, needs the builder Docker image),
`qemu/estimate.py --sweep`, then a hardware build with `--cpu-probe` on the Tall Dog
clone. Palette submission uploads to Rubato — Matt's call.
