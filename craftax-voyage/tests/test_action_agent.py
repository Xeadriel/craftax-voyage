from langchain.schema import AIMessage

from agents.action import ActionAgent


def test_additive_note_follows_task():
    msg = ActionAgent().render_human_message(task="Drink 6 water", context="", situation="S")
    assert "Task: Drink 6 water\n" + ActionAgent.ADDITIVE_AMOUNTS_NOTE in msg.content


def test_bad_then_good_response_is_not_a_failed_generation():
    agent = ActionAgent()
    calls = []
    good = "Code:\n```python\ndef f(state, log_fn, step_func):\n    return state\n```"
    agent.llm = lambda messages: (calls.append(list(messages)), AIMessage(content="no code" if len(calls) == 1 else good))[1]
    result = agent.generate_skill(task="t", context="", situation="S")
    assert result["generation_failed"] is False and len(calls) == 2
    assert "No Python code block" in calls[1][-1].content


def test_three_bad_responses_fail():
    agent = ActionAgent()
    calls = []
    agent.llm = lambda messages: (calls.append(1), AIMessage(content="no code"))[1]
    assert agent.generate_skill(task="t", context="", situation="S")["generation_failed"] is True
    assert len(calls) == 3


def test_system_message_renders():                    # Review Focus 2
    content = ActionAgent().render_system_message([]).content
    assert "step_func(Action." in content and "EnvParams" not in content
