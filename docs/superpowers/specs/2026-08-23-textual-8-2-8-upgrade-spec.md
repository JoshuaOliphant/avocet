# Textual 8.2.8 Upgrade — Spec

**Date:** 2026-08-23
**Source:** converted from the research plan of the same date
**Status:** executed and merged; one follow-up remains — see Further Notes

## Problem Statement

Avocet pins Textual to a range that admits newer releases than the one it actually
runs, and nothing in the project notices when that gap opens. A patch release
shipped roughly eight weeks before anyone looked, carrying two upstream fixes that
users of the TUI can feel: extended key sequences were mis-parsed in terminals
using the Kitty keyboard protocol, and clicking in a screen's padding could crash
the app.

From a maintainer's perspective the problem is not "we are one patch behind" — it
is that being behind was invisible. The lockfile is authoritative and CI enforces
it, so drift from upstream is silent by construction until someone goes looking by
hand. Every week that passes widens the eventual upgrade and makes it harder to
attribute a regression to the version that caused it.

From a contributor's perspective, the surrounding risk is worse than the bump: the
dependency graph contains a companion package whose newer release would silently
downgrade the snapshot serializer, so the obvious "update everything while I'm in
here" instinct is actively wrong and nothing in the repo says so.

## Solution

Move the resolved Textual version to the latest release inside the existing
declared range, changing only the lockfile, and prove the move is safe against the
real test suite rather than against the changelog's promises.

The declared dependency range does not move, because the target release already
satisfies it. No application code changes. No snapshot baselines are regenerated.
The upgrade is one re-resolution of a single package, a diff review confirming
nothing else moved, and a full verification pass.

Alongside it, record the two findings that make the next upgrade cheaper: the
companion-package trap that must not be taken, and the absence of any automated
signal that a dependency has a newer release.

## User Stories

1. As a TUI user in a Kitty-protocol terminal, I want extended key sequences with
   multiple codepoints to be parsed correctly, so that my keypresses do the thing I
   pressed them for.
2. As a TUI user, I want clicking in a screen's padding not to crash the app, so
   that a stray click does not lose my place in the bookmark list.
3. As a TUI user editing a bookmark, I want the platform-conventional line-kill and
   word-delete chords to work in text inputs, so that editing a title or tag list
   behaves the way every other app on my machine does.
4. As a TUI user, I want the three-pane layout, theme, and keybindings to look and
   behave exactly as they did before the upgrade, so that a dependency bump is
   invisible to me.
5. As a maintainer, I want to know the latest released version of my UI framework
   on demand, so that I can decide whether to move rather than discovering the gap
   by accident.
6. As a maintainer, I want the upgrade to touch only the lockfile, so that the
   change is reviewable in a single glance.
7. As a maintainer, I want the declared version range left alone when the target
   already satisfies it, so that the manifest does not accumulate churn that says
   nothing.
8. As a maintainer, I want a re-resolution scoped to one package, so that a patch
   bump does not turn into an unreviewable sweep of the whole dependency graph.
9. As a reviewer, I want the lockfile diff to show one package's version and
   artifact hashes and nothing else, so that I can approve it without auditing
   fifty-seven unrelated packages.
10. As a reviewer, I want any other package movement in the diff to be treated as a
    signal to back out and redo the resolution, so that collateral changes never
    ride along unnoticed.
11. As a maintainer, I want the full test suite run against the target version
    before the lockfile is committed, so that "no breaking changes" is a measured
    result and not a claim copied from a changelog.
12. As a maintainer, I want that trial run to write to neither the manifest, the
    lockfile, nor the virtual environment, so that investigating an upgrade cannot
    half-apply it.
13. As a maintainer, I want the visual regression baselines to pass unmodified, so
    that I know the rendered output is byte-identical rather than merely
    regenerated to match whatever the new version produces.
14. As a maintainer, I want a failing snapshot during this upgrade to stop the work,
    so that a contradiction between the evidence and the changelog is investigated
    instead of papered over by regenerating baselines.
15. As a contributor, I want to know that the snapshot-testing companion package
    must stay where it is, so that I do not "helpfully" upgrade it and force a
    major-version downgrade of the snapshot serializer underneath it.
16. As a contributor, I want that constraint written down with its reasoning, so
    that the next person does not rediscover it by breaking the suite.
17. As a contributor, I want to know which risks were asserted versus measured, so
    that I can tell a proven fact from a well-argued precaution.
18. As a maintainer, I want the upgrade verified on the full CI matrix before merge,
    so that the Python version the local trial run could not exercise is covered.
19. As a maintainer, I want lint and type checks run alongside the tests, so that
    the upgrade is held to the same bar as any other change.
20. As a maintainer, I want a decision recorded about whether a dependency bump
    earns a changelog line, so that the convention is applied deliberately rather
    than by reflex in both directions.
21. As a maintainer, I want the project version left untouched by a dependency
    bump, so that the release number keeps meaning something about the application.
22. As a maintainer, I want the work done on a branch rather than the default
    branch, so that CI gates it before it lands.
23. As a maintainer, I want to be told when a dependency has a newer release
    without asking, so that the next eight-week gap does not happen.
24. As a maintainer, I want that signal to understand this project's package
    manager and lockfile format, so that the automation produces a change I can
    actually merge rather than one I have to translate.
25. As a maintainer, I want the upper bound of the declared range identified as the
    thing to watch, so that the next major release is a planned read of its
    breaking-change section rather than a surprise.
26. As an AFK agent picking up this spec, I want the already-executed steps marked
    as done, so that I work on the remainder instead of redoing finished work.
27. As an AFK agent, I want the verification commands stated exactly, so that I can
    confirm the current state myself before changing anything.
28. As a maintainer, I want documentation written for this work to be committable,
    so that the reasoning survives past the session that produced it.

## Implementation Decisions

**Scope: the lockfile only.** The dependency manifest already declares a range
admitting the target release, so the manifest is not edited. The resolved version
recorded in the lockfile moves; nothing else does. The project version is
unrelated to a dependency bump and stays put, so none of the release ritual — bump,
re-lock, tag — applies.

**Resolution is scoped to a single package.** The package manager is asked to
re-resolve Textual specifically, not to upgrade everything it can. A blanket
upgrade would re-resolve the entire graph and convert a one-line diff into an
unreviewable one. The diff review is a required step, not a courtesy: if any
package other than Textual moved, the resolution is backed out and redone.

**No application modules change.** The upstream delta touches key-sequence parsing,
mouse-event forwarding into screen padding, the compositor's widget-at-offset
lookup, the test harness's mouse-event bounds check, and the key bindings on the
text input and text area widgets. Against Avocet's actual surface: the modal
screens module instantiates text inputs, so the changed bindings are live in the
app — but the change only widens two existing key strings and both remain hidden,
so nothing new renders in the footer. The stylesheet applies padding to the detail
panel and never to a screen, and no test drives mouse input, so the padding and
compositor fixes are unreachable here. Key-sequence parsing applies to a real
terminal, not to a test harness that injects keys directly. The application module,
the modal screens module, the database manager, the Raindrop API client, and the
summary provider are all untouched.

**Companion packages do not move.** The type checker's and dev tooling's Textual
constraints are already satisfied by the target. The snapshot-testing plugin is
deliberately pinned where it is: its newer release constrains the snapshot
serializer to an exact version that is a major release *below* what this project
currently resolves. Accepting that would rewrite snapshot serialization as a side
effect of a UI-framework patch bump. This is a stated non-goal, not an oversight.

**Snapshot baselines are not regenerated.** Upstream marks releases that are
expected to disturb snapshots; this one carries no such note, and the trial run
confirmed the baselines match unmodified. A snapshot failure during this work is
therefore evidence that something unexpected changed, and the correct response is
to stop and investigate rather than to accept new baselines.

**Changelog treatment is a judgment call, recorded as such.** The bump changes no
Avocet behaviour, which argues against an entry. It does deliver two upstream fixes
a user can feel, which argues for one. Either choice is defensible; what is not
defensible is applying the convention without noticing the question.

**Dependency-freshness automation is a follow-on decision, not part of this bump.**
The signal must be lockfile-aware for this project's package manager. Whether it
arrives as a hosted update bot or a scheduled dry-run resolution in CI is open.

## Testing Decisions

**What makes a good test here.** The existing suite already tests external
behaviour — what the app renders and how it responds to keys — rather than how any
of it is implemented. That is exactly the property that makes it usable as an
upgrade oracle: a suite coupled to Textual's internals would break on a patch bump
that changed nothing a user sees, and would therefore be unable to tell a real
regression from its own brittleness. No new assertions are written for this work.

**The seam is the existing suite, and there is exactly one new one: none.** This is
the ideal case the seam discipline aims at. The highest available seam — the whole
application driven through the test harness, plus the snapshot comparison of
rendered output — already exists and already covers the surface the upgrade could
disturb. Introducing a seam to "test the upgrade" would be testing the package
manager, not the application.

**Modules exercised, by existing layer.** The unit layer covers the Raindrop API
client against a mocked transport, and the database manager and models against a
real in-memory database. The interaction layer drives the whole application through
the test harness with an injected in-memory database and a stub summary provider,
covering collection switching, lazy summary generation, the modal flows, and sync.
The visual regression layer compares rendered output against stored baselines from
a deterministic seeded launcher. The interaction and visual layers are the ones
that would detect a Textual regression; the unit layer is unaffected by definition
but runs anyway.

**Prior art is the suite itself.** No new test *kind* is introduced. The injected
in-memory database and stub summary provider are the existing determinism seam and
are reused as-is.

**Verification sequence.** Resolve, review the diff, sync, then run tests, lint, and
type checks. Expect the full suite green with the visual baselines matching
unmodified and zero regenerations. Then let CI exercise the Python version the
local run could not.

**Known gap in the evidence.** The pre-commit trial ran on one operating system and
one Python version. The other supported Python version is covered only by CI, which
is why merge is gated on it rather than on the local result.

## Out of Scope

- Upgrading the snapshot-testing plugin. See the serializer-downgrade trap above.
- A blanket re-resolution of the dependency graph.
- Any change to the declared dependency range, including relaxing the upper bound
  in anticipation of the next major release.
- Regenerating snapshot baselines.
- Any application behaviour change, feature, or refactor.
- A project version bump or release.
- Planning the eventual major-version upgrade. That needs its own read of its own
  breaking-change section and is not this spec.
- Building the dependency-freshness automation. Identified here, specified
  separately.

## Further Notes

**Execution status.** The upgrade is done and on `main` via PR #15. The lockfile was
re-resolved for Textual alone, the diff confirmed to touch only that package, and the
full verification pass run green — the complete test suite passing with the visual
baselines matching unmodified, and lint and type checks clean. The installed version
was confirmed directly rather than inferred. Both supported Python versions exercised
the upgrade in CI, and the two user-visible upstream fixes are recorded under
`## [Unreleased]` in `CHANGELOG.md`.

What remains open:

- Dependency-freshness automation does not exist. Tracked as issue #14.

**The upper bound is the thing to watch.** The declared range excludes the next
major version, which as of 2026-08-23 did not exist in any form — no release, no pre-release.
When it lands it will need a genuine read of its breaking-change section rather
than a repeat of this spec. Recent majors from this project have been light on
breaking changes, but that is an observed pattern and not a guarantee.
