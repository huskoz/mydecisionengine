"""Checks the pipeline against the spec's expected v1 output.
Plain asserts on the plan built from the real config.yaml, so these
double as documentation of expected behaviour. Run: python -m pytest
"""

from app.config_loader import load_config
from app.pipeline import build_plan


def build():
    """Build the default plan and index its tasks by id."""
    plan = build_plan(load_config())
    return plan, {task["id"]: task for task in plan["tasks"]}


def test_the_three_do_now_tasks():
    _, tasks = build()
    assert tasks["get_playtesters"]["verdict"] == "DO NOW"
    assert tasks["finish_art_music"]["verdict"] == "DO NOW"
    assert tasks["rework_level_skips"]["verdict"] == "DO NOW"


def test_get_playtesters_ranks_first():
    _, tasks = build()
    assert tasks["get_playtesters"]["rank"] == 1
    assert tasks["get_playtesters"]["priority_score"] == 4.35


def test_add_ui_is_queued_because_capacity_ran_out():
    # add_ui is ready and scores well, but finish_art_music (ranked
    # higher) takes the last programming and art capacity first.
    _, tasks = build()
    add_ui = tasks["add_ui"]
    assert add_ui["verdict"] == "QUEUED"
    assert "capacity is full" in add_ui["reason"]
    assert "programming" in add_ui["reason"]
    assert "art" in add_ui["reason"]


def test_make_trailer_is_not_ready():
    _, tasks = build()
    trailer = tasks["make_trailer"]
    assert trailer["verdict"] == "NOT YET"
    assert "readiness 1" in trailer["reason"]


def test_speedrun_board_is_not_ready_and_unranked():
    # readiness 3 is below the gate of 4, so it never reaches the ranking.
    _, tasks = build()
    board = tasks["creating_speedrun_board"]
    assert board["verdict"] == "NOT YET"
    assert board["rank"] is None
    assert "readiness 3" in board["reason"]


def test_remaining_capacity_after_allocation():
    plan, _ = build()
    assert plan["remaining_capacity"] == {
        "programming": 0, "music": 0, "art": 0, "gameplay": 2}


def test_demo_crunch_mode_is_selectable():
    plan = build_plan(load_config(), "demo_crunch")
    assert plan["mode"] == "demo_crunch"


def test_unknown_mode_is_rejected():
    try:
        build_plan(load_config(), "no_such_mode")
        assert False, "expected a ValueError"
    except ValueError as error:
        assert "unknown mode" in str(error)


def test_same_input_gives_same_plan():
    # Deterministic: building twice gives exactly the same result.
    assert build_plan(load_config()) == build_plan(load_config())


if __name__ == "__main__":
    # So `python -m tests.test_pipeline` also works, without pytest.
    test_the_three_do_now_tasks()
    test_get_playtesters_ranks_first()
    test_add_ui_is_queued_because_capacity_ran_out()
    test_make_trailer_is_not_ready()
    test_speedrun_board_is_not_ready_and_unranked()
    test_remaining_capacity_after_allocation()
    test_demo_crunch_mode_is_selectable()
    test_unknown_mode_is_rejected()
    test_same_input_gives_same_plan()
    print("all tests passed")
