# Phreak → GitHub and the Nightshift front door (hand-off, 2026-10-21)

For the session managing Phreak. Matt approved this plan on 2026-10-21:

- Phreak's repo becomes a **public GitHub fork** of `lylepmills/eurorack` (Rubato's
  fork of Mutable's repo) under `mattpolicastro`. A fork of a public repo cannot be
  private; the Plaits code is MIT.
- It becomes the **first repository on Nightshift's GitHub front door** (issue →
  drafted spec PR → `spec:approved` → specloop build → same PR → Matt merges).
- **The current build is not interrupted.** `phreak-engine` keeps running locally
  under the shared `specloop serve`. Only its publication goes to GitHub.

## Where things stand (at writing)

- Run `phreak-engine`: admitted, 5/17 tasks, driven by the shared supervisor.
- Source clone: `~/Projects/plaits-telephone`. Its `origin` is still
  `lylepmills/eurorack`. Base branch: `telephone`.
- Manifest and trusted checks: `~/Projects/nightshift/specloop/manifests/plaits-phreak.toml`
  and `plaits-phreak/`. The run uses its own copy at
  `~/.specloop/runs/phreak-engine/manifest.toml`.

## A. Now (safe while the run builds)

1. **Create the fork:** `gh repo fork lylepmills/eurorack --clone=false`, giving
   `mattpolicastro/eurorack`. Then `gh repo edit mattpolicastro/eurorack --enable-issues`:
   forks have issues disabled by default, and the front door starts from issues.
2. **Repoint the source clone.** In `~/Projects/plaits-telephone`:
   ```sh
   git remote rename origin upstream
   git remote add origin https://github.com/mattpolicastro/eurorack.git
   git push -u origin telephone
   gh repo edit mattpolicastro/eurorack --default-branch telephone
   ```
   `specloop publish` pushes to the source clone's `origin`, so this repointing is
   what sends the PR to the fork. Do not push `spec/phreak-engine` from the clone:
   the run's branch is ahead, and `publish` pushes the run's own head.
3. **Create the labels:** all eight. The front door uses the spec labels, and
   `nightshift/config.py` also defaults the `agent:*` workflow labels.
   ```sh
   for l in spec:draft spec:review spec:approved agent:revise needs-human \
            agent:ready agent:working agent:done; do
     gh label create "$l" -R mattpolicastro/eurorack --force; done
   ```
4. **Name the GitHub repo in the manifest.** Add `github = "mattpolicastro/eurorack"`
   under `[run]` in both the template (`plaits-phreak.toml`) and the run's copy
   (`~/.specloop/runs/phreak-engine/manifest.toml`). `publish` reads the run's copy
   when it runs, so this needs no pause.

## B. When the run pauses `ready_to_publish`

5. **Publish:** use **Publish** in Paseo's Factory section, which asks for
   confirmation, or run `uv run specloop publish phreak-engine` from
   `~/Projects/nightshift`. This pushes the branch to the fork and opens a draft PR
   against `telephone`, as Matt via his gh credentials.
6. **Matt's checks.** Matt auditions the renders, then does the ARM compile
   (`check --full --arm`), `qemu/estimate.py --sweep`, and a `--cpu-probe` build on
   the Tall Dog clone. Then `specloop finish phreak-engine` (or **Finish** on the
   page) archives the change and marks the PR ready, and **Matt merges**.

## C. The front door, for Phreak's next changes

7. **Enrol** in `~/Projects/nightshift/config.toml`. This is a deliberate edit
   Matt has approved for this repo:
   ```toml
   [[repos]]
   name = "mattpolicastro/eurorack"
   engine = "specloop"
   manifest = "/Users/mattpolicastro/Projects/nightshift/specloop/manifests/plaits-phreak.toml"
   base = "telephone"
   ```
   The daemon overrides the template's change and branch for each issue.
8. **Check the daemon picks it up.** Since 2026-10-21 it is running, with only
   `mattpolicastro/nightshift` enrolled. The old worker-engine repos have been
   removed. After the `config.toml` edit, restart it:
   `launchctl kickstart -k gui/$(id -u)/com.mattpolicastro.nightshift`. Then run
   `uv run nightshift preflight` and `uv run nightshift status`.
9. **First front-door test.** Open an issue on the fork, for example "Add a UK tone
   table (dial, busy, ring cadences)", and label it `spec:draft`. The daemon drafts
   a spec PR (`spec:review`); Matt reviews it and adds `spec:approved`; specloop
   builds and publishes to the same PR. This is the "one real change through the
   front door" milestone that retiring the worker engine waits on.

## Caveats

- **Comment filtering is in place (`85e79bf` in nightshift).** Only comments,
  reviews and inline comments from OWNER, MEMBER or COLLABORATOR reach an agent,
  and an issue opened by anyone else is escalated rather than drafted. That has
  to be true before step 5 makes the PR public, and it is.

- **Manifests stay off the fork.** The trusted manifest and checks must stay
  outside the fork; agents can read anything on disk, so never put a working
  reference engine anywhere. Nightshift is public now, and per-project manifests
  stay where they are: `specloop/manifests/` is gitignored and never published.
- **Who can label.** Nothing yet checks who applied a label. On a public repo only
  collaborators can apply labels, so this is fine unless Matt adds collaborators.
- **One driver at a time.** The shared supervisor drives `phreak-engine`; don't also
  `specloop run` it by hand. The run lock refuses that anyway.
