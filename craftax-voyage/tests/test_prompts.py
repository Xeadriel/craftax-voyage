import re
from pathlib import Path

PROMPTS = Path(__file__).resolve().parent.parent / "prompts"


def test_critic_never_states_a_remaining_amount():
    # Every attempt is judged from its own start, so "1 more coal is needed"
    # would make the next attempt mine too little
    text = (PROMPTS / "critic.txt").read_text(encoding="utf-8")
    assert not re.search(r"\d+ more coal is needed", text)
    assert "own start" in text


def test_action_rule_16_keeps_the_whole_task():
    text = (PROMPTS / "action_template.txt").read_text(encoding="utf-8")
    assert "the whole task from its own start" in text


def test_example_collects_enough_wood_for_table_and_pickaxe():
    text = (PROMPTS / "action_template.txt").read_text(encoding="utf-8")
    example = re.search(r"def mine_3_coal\(.*?return state", text, re.S).group(0)
    assert "BlockType.TREE, 3" in example


def task_formats(prompt_name):
    text = (PROMPTS / f"{prompt_name}.txt").read_text(encoding="utf-8")
    line = next(l for l in text.splitlines() if "concise format, such as" in l)
    return re.findall(r'"([^"]+)"', line)


def test_decomposition_uses_the_curriculum_task_format():
    # The action agent and critic are written for the curriculum's tasks
    assert task_formats("curriculum_task_decomposition") == task_formats("curriculum")
