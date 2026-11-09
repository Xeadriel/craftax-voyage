import sys

import pytest


class counting_stub:
    def __init__(self, result):
        self.result = result
        self.calls = 0

    def __call__(self, **kwargs):
        self.calls += 1
        return self.result


def skill(code):
    return {
        "program_code": code,
        "program_name": "f",
        "description": "",
        "generation_failed": False,
        "error": None,
    }


def must_not_be_called(**kwargs):
    raise AssertionError("the critic must not judge a death")


@pytest.fixture(scope="module")
def voyage(tmp_path_factory):
    import craftax_voyage

    argv = sys.argv
    sys.argv = ["craftax_voyage.py", "--ckpt_dir", str(tmp_path_factory.mktemp("ckpt")), "--fps", "0"]
    try:
        args = craftax_voyage.parse_args()
    finally:
        sys.argv = argv
    return craftax_voyage.CraftaxVoyage(args)


def test_death_fails_without_critic_and_ends_rollout(voyage):         # also Review Focus 4
    voyage.action_agent.generate_skill = counting_stub(skill("def f(state, log_fn, step_func):\n    raise EpisodeEnded('x')\n"))
    voyage.critic_agent.check_task_success = must_not_be_called
    info = voyage.rollout("Mine 3 coal", "")
    assert info["died"] is True and info["success"] is False
    assert info["critique"].startswith("The player died.")
    assert voyage.action_agent.generate_skill.calls == 1


def test_critic_gets_report_diff_and_events(voyage):
    voyage.action_agent.generate_skill = counting_stub(skill(
        "def f(state, log_fn, step_func):\n    log_fn('note')\n    state = step_func(Action.NOOP.value)\n    return state\n"))
    seen = {}
    voyage.critic_agent.check_task_success = lambda **kw: (seen.update(kw), (True, ""))[1]
    info = voyage.rollout("Wait", "")
    assert "Vitals:" in seen["report_before"] and isinstance(seen["events"], list)
    assert "note" not in seen["events"] and info["vitals_before"]["health"][1] == 9


def test_report_before_is_taken_before_the_skill_runs(voyage):
    from craftax.craftax.constants import BlockType
    from utils.situation_report import situation_report

    # A diamond just out of view to the right; the skill walks until it sees it
    s = voyage.env_state
    row, col = int(s.player_position[0]), int(s.player_position[1])
    level = int(s.player_level)
    voyage.env_state = s.replace(map=s.map.at[level, row, col + 7].set(BlockType.DIAMOND.value)
                                 .at[level, row, col + 1:col + 7].set(BlockType.GRASS.value))
    expected = situation_report(voyage.env_state)
    assert "diamond not seen" in expected
    voyage.action_agent.generate_skill = counting_stub(skill(
        "def f(state, log_fn, step_func):\n"
        "    for _ in range(3):\n"
        "        state = step_func(Action.RIGHT.value)\n"
        "    return state\n"))
    seen = {}
    voyage.critic_agent.check_task_success = lambda **kw: (seen.update(kw), (True, ""))[1]
    voyage.rollout("Walk", "")
    assert seen["report_before"] == expected


def test_resume_without_vitals_before(voyage):                         # Review Focus 5
    voyage.critic_agent.check_task_success = lambda **kw: (True, "")
    voyage.action_agent.generate_skill = counting_stub(skill("def f(state, log_fn, step_func):\n    return state\n"))
    info = voyage.rollout("Wait", "", resume={"next_attempt": 1, "code": "", "error": "", "log": "", "critique": ""})
    assert info["vitals_before"] is not None


def test_inference_plans_again_after_death_and_stops_after_failures(voyage, monkeypatch):
    plans = iter([["Mine 1 wood", "Craft 1 wood pickaxe"], ["Mine 2 wood"]])
    decompositions = []
    monkeypatch.setattr(voyage, "decompose_task", lambda task: decompositions.append(task) or next(plans))
    results = iter([
        {"task": "Mine 1 wood", "success": True},
        {"task": "Craft 1 wood pickaxe", "success": False, "died": True},
        {"task": "Mine 2 wood", "success": False},
        {"task": "Mine 2 wood", "success": False},
    ])
    ran = []
    monkeypatch.setattr(voyage, "rollout", lambda task, context: ran.append(task) or next(results))
    voyage.inference(task="Craft 1 wood pickaxe")
    assert decompositions == ["Craft 1 wood pickaxe"] * 2
    assert ran == ["Mine 1 wood", "Craft 1 wood pickaxe", "Mine 2 wood", "Mine 2 wood"]


def test_tee_output_writes_the_log_live(tmp_path, monkeypatch):
    import io
    import craftax_voyage

    out, err = io.StringIO(), io.StringIO()
    monkeypatch.setattr(sys, "stdout", out)
    monkeypatch.setattr(sys, "stderr", err)
    log_path = tmp_path / "logs" / "run.txt"
    craftax_voyage.tee_output(str(log_path))
    print("hello ✓")
    sys.stderr.write("oops\n")
    # Readable before anything is closed or flushed explicitly
    assert log_path.read_text(encoding="utf-8").endswith("hello ✓\noops\n")
    assert out.getvalue().endswith("hello ✓\n") and err.getvalue() == "oops\n"
