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


def test_resume_without_vitals_before(voyage):                         # Review Focus 5
    voyage.critic_agent.check_task_success = lambda **kw: (True, "")
    voyage.action_agent.generate_skill = counting_stub(skill("def f(state, log_fn, step_func):\n    return state\n"))
    info = voyage.rollout("Wait", "", resume={"next_attempt": 1, "code": "", "error": "", "log": "", "critique": ""})
    assert info["vitals_before"] is not None
