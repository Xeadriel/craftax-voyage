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


def test_decomposition_system_message_has_tutorial(tmp_path):
    c = CurriculumAgent(ckpt_dir=str(tmp_path)).render_system_message_task_decomposition().content
    assert "MAKE_STONE_PICKAXE" in c and "{Craftax tutorial.md file}" not in c


def test_decomposition_sees_only_situation_skills_and_task(tmp_path, base_state):
    agent = CurriculumAgent(ckpt_dir=str(tmp_path), use_qa=True)
    agent.completed_tasks = ["Mine 1 wood"]
    agent.update_exploration_progress({"task": "Mine 3 coal", "success": False})
    agent.qa_llm = lambda m: (_ for _ in ()).throw(AssertionError("QA must not run"))
    c = agent.render_human_message_task_decomposition(env_state=base_state, task="Craft 1 stone pickaxe").content
    assert "Vitals:" in c and c.endswith("Final task: Craft 1 stone pickaxe")
    assert "Completed tasks so far" not in c and "Last turn" not in c


def test_decomposition_parses_list_after_reasoning(tmp_path, base_state):
    agent = CurriculumAgent(ckpt_dir=str(tmp_path))
    response = 'Reasoning: "Mine [quantity] wood" needs [2] wood.\nSub-goals: [" Mine 3 wood", "Craft 1 wood pickaxe"]'
    agent.llm = lambda m: type("R", (), {"content": response})()
    assert agent.decompose_task("Craft 1 wood pickaxe", env_state=base_state) == ["Mine 3 wood", "Craft 1 wood pickaxe"]
