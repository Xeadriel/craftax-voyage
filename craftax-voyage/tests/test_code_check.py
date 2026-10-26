from agents.code_check import check_skill_code

RESERVED = {"sleep", "drink", "known_blocks", "mine_block", "UNKNOWN"}
OK = "def mine_coal(state, log_fn, step_func):\n    state = mine_block(state, log_fn, step_func, BlockType.COAL, 1)\n    state = step_func(Action.NOOP.value)\n    return state\n"


def test_valid_skill_passes():
    assert check_skill_code(OK, "mine_coal", RESERVED) == []


def test_rejects_primitive_name():
    code = "def sleep(state, log_fn, step_func):\n    return sleep(state, log_fn, step_func, max_steps=50)\n"
    assert any("sleep" in e for e in check_skill_code(code, "sleep", RESERVED))


def test_rejects_step_func_with_two_args():
    code = OK.replace("step_func(Action.NOOP.value)", "step_func(state, 5)")
    assert any("step_func" in e for e in check_skill_code(code, "mine_coal", RESERVED))


def test_rejects_unknown_enum_member():
    code = OK.replace("BlockType.COAL", "BlockType.MELEE")
    assert any("MELEE" in e for e in check_skill_code(code, "mine_coal", RESERVED))


def test_rejects_shadowing_helper():
    code = "def f(state, log_fn, step_func):\n    known_blocks = known_blocks(state)\n    return state\n"
    assert any("known_blocks" in e for e in check_skill_code(code, "f", RESERVED))


def test_rejects_fake_primitive_log_line():          # Review Focus 1
    code = "def f(state, log_fn, step_func):\n    log_fn(f\"[mine_block] Successfully mined {1}\")\n    return state\n"
    assert check_skill_code(code, "f", RESERVED) != []


def test_process_ai_message_runs_the_check():
    from langchain.schema import AIMessage

    from agents.action import ActionAgent

    content = "Code:\n```python\ndef sleep(state, log_fn, step_func):\n    return state\n```"
    result = ActionAgent().process_ai_message(AIMessage(content=content))
    assert isinstance(result, str) and "sleep" in result
