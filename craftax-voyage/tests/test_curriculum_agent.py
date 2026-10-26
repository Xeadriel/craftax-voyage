from agents.curriculum import CurriculumAgent
from utils.situation_report import vitals


def test_message_uses_report_not_map(tmp_path, base_state):
    agent = CurriculumAgent(ckpt_dir=str(tmp_path))
    agent.completed_tasks = ["Mine 1 wood"]
    agent.qa_llm = lambda m: (_ for _ in ()).throw(AssertionError("QA must be off"))
    c = agent.render_human_message(env_state=base_state).content
    assert "Vitals:" in c and "Map:" not in c


def test_death_clears_world_progress_and_shows_notice(tmp_path, base_state):
    agent = CurriculumAgent(ckpt_dir=str(tmp_path))
    agent.update_exploration_progress({"task": "Mine 3 coal", "success": True})
    agent.update_exploration_progress({"task": "Kill 1 zombie", "success": False, "died": True,
        "critique": "The player died.", "attempts": 1,
        "vitals_before": vitals(base_state), "vitals_after": vitals(base_state)})
    assert agent.world_progress == [] and "Kill 1 zombie" in agent.failed_tasks
    assert agent.completed_tasks == ["Mine 3 coal"]
    c = agent.render_human_message(env_state=base_state).content
    assert CurriculumAgent.DEATH_NOTICE in c and 'Last turn: "Kill 1 zombie" -> failed' in c


def test_task_context_empty_without_qa(tmp_path):
    assert CurriculumAgent(ckpt_dir=str(tmp_path)).get_task_context("Mine 1 wood") == ""


def test_resume_without_world_progress_file(tmp_path):        # Review Focus 5
    (tmp_path / "curriculum").mkdir()
    (tmp_path / "curriculum" / "completed_tasks.json").write_text('["Mine 1 wood"]')
    agent = CurriculumAgent(ckpt_dir=str(tmp_path), resume=True)
    assert agent.world_progress == [] and agent.completed_tasks == ["Mine 1 wood"]
