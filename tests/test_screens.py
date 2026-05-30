# ABOUTME: Tests for the modal screen result dataclasses.
# ABOUTME: Confirms AddResult carries the fields the app needs to call the API.
from avocet.screens import AddResult


def test_add_result_fields():
    result = AddResult(link="https://x", collection_id=1, tags=["py", "tui"])
    assert result.link == "https://x"
    assert result.collection_id == 1
    assert result.tags == ["py", "tui"]
