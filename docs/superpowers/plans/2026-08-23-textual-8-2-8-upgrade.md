# Textual 8.2.8 Upgrade Research & Plan

**Goal:** Establish the current released Textual version, the gap to what Avocet ships, and what it actually takes to close it.

**Headline:** The gap is one patch release — `8.2.7` → `8.2.8`. There are **no breaking changes**, **no code changes**, and **no snapshot regeneration** required. The whole upgrade is `uv lock --upgrade-package textual` plus a CI run.

**Verification status:** Every version claim below is from PyPI's JSON API or the Textualize/textual repo. The "nothing breaks" claim is not inferred from the changelog alone — the full suite was run against 8.2.8 in an ephemeral overlay environment (see [Proof](#proof-i-actually-ran-it)).

**Date:** 2026-08-23

---

## 1. Latest released Textual

| Fact | Value | Source |
|---|---|---|
| Latest version | **8.2.8** | [`pypi.org/pypi/textual/json`](https://pypi.org/pypi/textual/json) → `.info.version` |
| Release date | **2026-06-30** (`2026-06-30T06:51:26Z` wheel upload) | same JSON, `.releases["8.2.8"][].upload_time_iso_8601` |
| `requires_python` | **`<4.0,>=3.9`** | same JSON, `.info.requires_python` |
| Git tag | `v8.2.8` @ `1d99508b92`, published `2026-06-30T06:53:30Z` | [releases/tag/v8.2.8](https://github.com/Textualize/textual/releases/tag/v8.2.8) |

There is **no 9.x release and no 9.x pre-release**. Checking every key in `.releases` for non-`X.Y.Z` version strings returns only ancient 0.x alphas/betas (`0.2.0b4` … `0.72.0a1`); the newest tags on GitHub are `v8.2.8, v8.2.7, v8.2.6, …`. The project's `<9` ceiling is therefore not currently binding on anything.

The `main`-branch [CHANGELOG.md](https://raw.githubusercontent.com/Textualize/textual/main/CHANGELOG.md) opens directly with `## [8.2.8] - 2026-06-30` — there is no `Unreleased` section accumulating undelivered work.

## 2. What this repo pins today

| Where | Value | Source |
|---|---|---|
| Declared range | `textual>=8.2,<9` | `pyproject.toml:15` |
| Resolved in lock | **`8.2.7`** | `uv.lock:1230-1231` (`[[package]] name = "textual"` / `version = "8.2.7"`) |
| Actually installed | `8.2.7` | `./.venv/bin/python -c "import textual; print(textual.__version__)"` |
| Project floor | `requires-python = ">=3.12"` | `pyproject.toml:7` |
| CI matrix | `["3.12", "3.13"]` on `ubuntu-latest` | `.github/workflows/python-app.yml:17` |

CI runs `uv sync --locked`, so the lock is authoritative and drift fails the build (`.github/workflows/python-app.yml:25`). `uv lock --check` passes right now — the lock is in sync with `pyproject.toml`, so the only pending change is the deliberate one.

Because `8.2.8` already satisfies `>=8.2,<9`, **`pyproject.toml` does not need to be edited**. Only `uv.lock` moves.

## 3. The delta, read from Textual's own changelog

The entire `8.2.7 → 8.2.8` delta, verbatim in shape from [CHANGELOG.md](https://raw.githubusercontent.com/Textualize/textual/main/CHANGELOG.md):

**Fixed**
- Kitty extended keys with multiple codepoints were mis-parsed ([#6592](https://github.com/Textualize/textual/pull/6592))
- Crash when clicking in the Screen's padding ([#6598](https://github.com/Textualize/textual/pull/6598))

**Changed**
- `super+backspace` is now an alias for `ctrl+u` in `Input` and `TextArea` ([#6594](https://github.com/Textualize/textual/pull/6594))
- `alt+backspace` (option+backspace on Mac) now behaves as `ctrl+backspace` in `Input` and `TextArea` ([#6593](https://github.com/Textualize/textual/pull/6593))

**Breaking changes: none.** **Removals: none. Deprecations: none.** The changelog marks breaking changes explicitly with the literal string `Breaking change:` — grepping the whole file, the most recent such entry is in `8.0.0` (`Select.BLANK` → `Select.NULL`, [#6374](https://github.com/Textualize/textual/pull/6374)), which predates the version this repo already runs. Nothing between 8.2.7 and 8.2.8 carries that marker.

The [diff `v8.2.7...v8.2.8`](https://github.com/Textualize/textual/compare/v8.2.7...v8.2.8) is 19 commits / 13 files, of which only six are library source:

| File | Δ | What |
|---|---|---|
| `src/textual/_xterm_parser.py` | +59 −31 | Kitty key protocol parsing |
| `src/textual/screen.py` | +11 −4 | replaces two `assert isinstance(content_widget.parent, Widget)` with a `Screen` special-case in `_forward_event` |
| `src/textual/widgets/_input.py` | +9 −3 | binding aliases |
| `src/textual/widgets/_text_area.py` | +3 −3 | binding aliases |
| `src/textual/_compositor.py` | +2 −5 | `get_widget_and_offset_at` clamps negative offsets instead of bailing |
| `src/textual/pilot.py` | +1 −1 | `if offset not in screen.region` → `screen.size.region` in `_post_mouse_events` |

## 4. What actually touches this codebase

Short answer: **nothing that changes behaviour or output.** Taking each 8.2.8 change against the real source:

**a. Input binding aliases (#6593, #6594) — reachable, cosmetically invisible.**
Avocet instantiates `Input` in five places: `avocet/screens.py:40-42` (add-bookmark link/title/tags), `avocet/screens.py:74-75` (edit title/tags), `avocet/screens.py:107` (search query), `avocet/screens.py:123` (tag filter). So the changed `Input.BINDINGS` are live in the app. But the upstream patch only widens two existing `Binding` key strings (`"ctrl+u"` → `"ctrl+u,super+backspace"`, `"ctrl+backspace"` → `"ctrl+backspace,alt+backspace"`) and both keep `show=False`. Nothing new appears in the `Footer` (`avocet/app.py:116`), so the modal snapshots (`test_add_modal`, `test_search_modal`, `test_delete_modal` in `tests/test_snapshots.py:32,37,42`) cannot shift. No test drives `ctrl+u`, `super+backspace`, or `alt+backspace` — `grep` over `tests/` finds no such key press.

**b. Screen-padding click fix (#6598) — not reachable from this app or its tests.**
The fix is in mouse-event forwarding for text selection. Avocet's stylesheet sets `padding: 0 1` only on `#detail` (`avocet/avocet.tcss:19`), never on `Screen`, and no test uses mouse input at all: `grep -rn 'pilot.click\|hover' tests/` returns nothing. All interaction tests drive the keyboard (`pilot.press`).

**c. `Pilot._post_mouse_events` bounds check (`screen.region` → `screen.size.region`) — dead code path here.**
Same reason as (b): the eight `run_test()` call sites (`tests/test_app_interaction.py:39`, `tests/test_app_search_edit.py:53,68,93,116,129`, `tests/test_app_sync.py:33`, plus `snap_compare` internals) never post mouse events.

**d. Kitty key-protocol parsing (#6592) — runtime-terminal only.**
`_xterm_parser` handles real terminal input. Under `run_test()`/`snap_compare` keys are injected through `Pilot`, not parsed from escape sequences, so the test suite is untouched. This one only affects `just run` in a Kitty-protocol terminal — and only as a fix.

**e. Everything else in play is unchanged.** `App`/`BINDINGS` (`avocet/app.py:83-91`), `ListView` (`avocet/app.py:109`), `DataTable` (`avocet/app.py:111`), `ModalScreen` (`avocet/screens.py:32,64,88,103,119`), `@work` workers (`avocet/app.py:189,223,249,273,300,326`), `watch_theme` (`avocet/app.py:118`) and `register_theme(CATPPUCCIN_MOCHA)` (`avocet/app.py:126`), and `push_screen` (`avocet/app.py:247,271,296,324,344`) have zero diff between the two tags.

### Snapshot baselines: regeneration is NOT expected

The task brief flagged that SVG output usually shifts between Textual versions. **The changelog does not support that expectation for this jump, and neither does the run.** For contrast, Textual *does* warn when it happens: the `8.2.6` entry says a selection fix "may break some snapshots" — and `8.2.6` is already below the pinned floor. The `8.2.8` entry carries no such note, and the diff adds two *new* upstream snapshot files rather than modifying existing ones.

Repo detail worth recording: the baselines under `tests/__snapshots__/test_snapshots/` are `.raw` files (`test_main_view.raw`, etc.), not `.svg` — they contain `<svg class="rich-terminal" …>` payloads written by syrupy's raw extension. `tests/snapshot_apps/seeded_app.py:2` describes them as "an SVG", which is true of the contents but not the filename.

## 5. Companion packages — verdict: no lockstep move required, and one trap

| Package | Locked | Latest on PyPI | Textual constraint | Verdict |
|---|---|---|---|---|
| `pytest-textual-snapshot` | `1.0.0` (`uv.lock:1105-1106`) | `1.1.0`, 2025-01-23 | `textual>=0.28.0` | **Not a blocker.** 8.2.8 satisfies it. |
| `textual-dev` | `1.8.0` (`uv.lock:1247-1248`) | `1.8.0`, 2025-10-11 | `textual>=0.86.2` | **Already latest**, satisfied. |
| `textual-serve` (transitive via textual-dev) | `1.1.3` (`uv.lock:1265-1266`) | — | depends on `textual` | No pin conflict observed. |

Constraints read from [`pypi.org/pypi/pytest-textual-snapshot/json`](https://pypi.org/pypi/pytest-textual-snapshot/json) and [`pypi.org/pypi/textual-dev/json`](https://pypi.org/pypi/textual-dev/json) (`.info.requires_dist`).

**The trap — do not "helpfully" bump `pytest-textual-snapshot` to 1.1.0 while you are in there.** Its metadata pins syrupy *exactly*:

- `pytest-textual-snapshot 1.0.0` → `syrupy>=4.0.0` → this repo resolves **syrupy 5.2.0** (`uv.lock:1218-1219`)
- `pytest-textual-snapshot 1.1.0` → **`syrupy==4.8.0`**

Moving to 1.1.0 forces a major-version *downgrade* of syrupy (5.2.0 → 4.8.0), which is exactly the kind of change that rewrites snapshot serialization. That is an unrelated, higher-risk change with no benefit to a Textual patch bump. Leave it at 1.0.0.

**Unverified:** I did not test whether syrupy 4.8.0 would in fact alter the `.raw` serialization — I am asserting the risk, not the outcome, and the correct response is to avoid the change rather than characterize it.

## 6. Proof: I actually ran it

Baseline, project venv on textual 8.2.7:

```
$ ./.venv/bin/python -m pytest -q
5 snapshots passed.
57 passed in 9.37s
```

Same suite with 8.2.8 layered on top, via an ephemeral uv overlay that writes to neither `pyproject.toml` nor `uv.lock` nor `.venv`:

```
$ uv run --no-sync --with 'textual==8.2.8' python -c "import textual; print(textual.__version__)"
textual 8.2.8
$ uv run --no-sync --with 'textual==8.2.8' python -m pytest -q
5 snapshots passed.
57 passed in 6.87s
```

All 57 tests pass and **all 5 snapshots match unmodified baselines** on 8.2.8. `git status --porcelain` confirmed no repo files were changed by the run.

Caveat on scope: this was Python 3.12.7 on macOS (darwin) only. CI additionally covers Python 3.13 on `ubuntu-latest`, which this run did not exercise.

## 7. Upgrade plan

1. **Branch.** `git switch -c chore/textual-8.2.8` (repo default branch is `main`).
2. **Re-resolve only Textual.** `uv lock --upgrade-package textual`. Do **not** edit `pyproject.toml` — `>=8.2,<9` already admits 8.2.8. Do **not** run a bare `uv lock --upgrade`, which would sweep all 58 packages and turn a one-line diff into an unreviewable one.
3. **Sanity-check the diff.** `git diff uv.lock` should show the `textual` version/sdist/wheel hashes and nothing else. If any other package moved, back out and redo step 2.
4. **Sync and verify.** `just install && just test && just lint && just typecheck`. Expect 57 passed / 5 snapshots passed with **zero** snapshot updates. If a snapshot fails, stop — that contradicts both the changelog and the trial run, and means something else changed.
5. **Changelog.** Per `CLAUDE.md`, this is arguably not user-facing (a dependency bump with no behaviour change). It does deliver two upstream fixes users can feel — Kitty key parsing and the screen-padding click crash — so a single line under `## [Unreleased]` → `Fixed` is defensible. Judgment call, not a rule.
6. **No version bump.** `pyproject.toml [project].version` stays at `1.0.0`; no re-lock dance beyond step 2.
7. **PR and merge.** CI runs `ruff check`, `ty check`, `pytest` on 3.12 and 3.13 — that is the 3.13 coverage the local trial run lacked.

### Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Snapshot drift | Very low — no upstream warning, trial run clean | Step 4 catches it; `just snapshot-update` only after eyeballing the report |
| Python 3.13 behaves differently | Low | CI matrix covers it before merge |
| `uv lock --upgrade` used by mistake, dragging 57 other packages | Medium (operator error) | Step 3 diff review |
| Collateral `pytest-textual-snapshot` bump forcing syrupy 5.2.0 → 4.8.0 | Only if someone goes looking | Explicitly out of scope; see §5 |

### Effort and risk call

**Effort: ~15 minutes, one command plus a CI run. Risk: minimal.** This is a patch bump inside an already-satisfied version range, with no breaking changes, no API surface this app touches, and a green suite proven against the target version. A staged/intermediate upgrade is **not warranted** — there is no intermediate to stage through; 8.2.8 is the immediate successor of 8.2.7.

The `<9` ceiling is the thing to watch, not this bump. When 9.0 ships it will need a real read of its breaking-change section. As a size reference, `8.0.0` carried exactly one `Breaking change:` line and it was `Select.BLANK` → `Select.NULL` — a widget Avocet does not use. Textual's recent majors have been light, but that is a pattern, not a guarantee.

## 8. Notes for whoever picks this up

- **`docs/` is tracked.** The ignore rule covers only `docs/chroma/`, the vector store, so documents written here commit normally without `-f`.
- **Automation gap:** nothing in `.github/workflows/python-app.yml` notices that a dependency has a newer release. This delta sat for ~8 weeks (8.2.8 released 2026-06-30) with no signal. A Dependabot or Renovate config for `uv` — or a scheduled `uv lock --upgrade --dry-run` job — would have raised it automatically.
