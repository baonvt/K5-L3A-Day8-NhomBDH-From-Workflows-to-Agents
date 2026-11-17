"""Regression check for the first wrong step in seeded_regression C-002@11."""

import pytest

pytestmark = pytest.mark.student


def test_ticket_override_is_the_first_wrong_step():
    from lab9.trace_case import investigate

    bad = investigate("seeded_regression", "C-002", 11)
    fixed = investigate("fixed", "C-002", 11)
    bad_kinds = [event.get("kind") for event in bad["trial"]["events"]]
    fixed_kinds = [event.get("kind") for event in fixed["trial"]["events"]]

    assert bad_kinds.index("model_override") < bad_kinds.index("quote")
    assert "model_override" not in fixed_kinds
    assert bad["trial"]["snapshot"]["refund_vnd"] != bad["label"]["refund_vnd"]
    assert fixed["trial"]["lab8_pass"] is True
