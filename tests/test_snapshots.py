# ABOUTME: Visual regression snapshots via pytest-textual-snapshot.
# ABOUTME: Determinism comes from the seeded in-memory DB + stub provider in seeded_app.py.
from pathlib import Path

APP = str(Path(__file__).parent / "snapshot_apps" / "seeded_app.py")

# Navigate from All (index=None) to Python: first down moves to index 0 (All),
# second down moves to index 1 (Python); then enter fires ListView.Selected.
_SELECT_PYTHON = ["down", "down", "enter"]


def test_main_view(snap_compare):
    # Show the Python collection so bookmark rows are visible.
    assert snap_compare(APP, terminal_size=(100, 30), press=_SELECT_PYTHON)


def test_detail_with_summary(snap_compare):
    # Select Python collection, tab to bookmarks table, enter to select first row,
    # then wait for the StubSummaryProvider worker to write the summary.
    async def navigate_and_wait(pilot):

        await pilot.press(*_SELECT_PYTHON)
        await pilot.pause()
        await pilot.press("tab", "enter")
        await pilot.pause()
        await pilot.app.workers.wait_for_complete()
        await pilot.pause()

    assert snap_compare(APP, terminal_size=(100, 30), run_before=navigate_and_wait)


def test_add_modal(snap_compare):
    # Press 'a' — the add modal opens whenever _current_collection_id is set.
    assert snap_compare(APP, terminal_size=(100, 30), press=["a"])


def test_search_modal(snap_compare):
    # Press '/' to open the search modal.
    assert snap_compare(APP, terminal_size=(100, 30), press=["slash"])


def test_delete_modal(snap_compare):
    # Navigate to Python collection, tab to bookmarks table, press d to open delete modal.
    assert snap_compare(
        APP,
        terminal_size=(100, 30),
        press=[*_SELECT_PYTHON, "tab", "d"],
    )
