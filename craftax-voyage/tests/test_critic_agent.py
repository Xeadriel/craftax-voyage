from langchain.schema import AIMessage

from agents.critic import CriticAgent


def test_human_message_has_diff_and_events_but_no_context():
    msg = CriticAgent().render_human_message(task="Mine 3 coal", report_before="B", report_after="A",
        diff="coal 0 -> 3 (+3)", events=["[mine_block] Mined COAL 1/3"], error="")
    c = msg.content
    assert "coal 0 -> 3 (+3)" in c and "[mine_block] Mined COAL 1/3" in c
    assert "Context" not in c and "Task: Mine 3 coal" in c


def test_check_task_success_judges_with_new_inputs():
    critic = CriticAgent()
    seen = []
    critic.llm = lambda messages: (
        seen.append(messages),
        AIMessage(content='{"reasoning": "coal +3", "success": true, "critique": ""}'),
    )[1]
    success, critique = critic.check_task_success(task="Mine 3 coal", report_before="B", report_after="A",
        diff="coal 0 -> 3 (+3)", events=[], error="")
    assert success is True and critique == ""
    assert "Primitive events:\nNone" in seen[0][1].content
