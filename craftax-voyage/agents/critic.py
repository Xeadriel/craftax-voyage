from __future__ import annotations

from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

from prompts import load_prompt
from utils.json_utils import fix_and_parse_json


class CriticAgent:
    def __init__(
        self,
        model_name="Qwen/Qwen3.5-4B",
        api_base="http://localhost:8000/v1",
        temperature=0,
        request_timeout=120,
        mode="auto",
    ):
        self.llm = ChatOpenAI(
            model_name=model_name,
            temperature=temperature,
            request_timeout=request_timeout,
            openai_api_base=api_base,
            openai_api_key="EMPTY",
            max_tokens=4096,
        )

        assert mode in ["auto", "manual"]
        self.mode = mode

    def render_system_message(self):
        return SystemMessage(content=load_prompt("critic"))

    def render_human_message(
        self,
        *,
        task,
        context,
        textual_state_before,
        textual_state,
        new_achievements,
        log,
        error,
    ):
        observation = (
            f"State before execution:\n{textual_state_before}\n\n"
            f"State after execution:\n{textual_state}\n\n"
            f"Achievements unlocked during execution: "
            f"{', '.join(new_achievements) if new_achievements else 'None'}\n\n"
            f"Execution log:\n{log if log else 'None'}\n\n"
            f"Skill execution error: {error if error else 'None'}\n\n"
            f"Task: {task}\n\n"
            f"Context: {context if context else 'None'}\n"
        )

        print(
            "\033[31m"
            f"****Critic Agent human message****\n{observation}"
            "\033[0m", flush=True
        )

        return HumanMessage(content=observation)

    def human_check_task_success(self):
        confirmed = False
        success = False
        critique = ""

        while not confirmed:
            success = input("Success? (y/n)").lower() == "y"
            critique = input("Enter your critique:")
            print(f"Success: {success}\nCritique: {critique}", flush=True)
            confirmed = input("Confirm? (y/n)") in ["y", ""]

        return success, critique

    def ai_check_task_success(self, messages, max_retries=5):
        for attempt in range(max_retries):
            critic = self.llm(messages).content

            print(
                f"****Critic Agent ai message****\n{critic}", flush=True
            )

            try:
                response = fix_and_parse_json(critic)

                if not isinstance(response, dict):
                    raise ValueError("Critic response is not a JSON object")

                if not isinstance(response.get("success"), bool):
                    raise ValueError(
                        "Critic response has invalid 'success' field"
                    )

                return (
                    response["success"],
                    response.get("critique", ""),
                )

            except Exception as e:
                print(
                    "\033[31m"
                    f"Error parsing critic response: {e}. "
                    f"Retrying ({attempt + 1}/{max_retries})..."
                    "\033[0m", flush=True
                )

        print(
            "\033[31m"
            "Failed to parse Critic Agent response. "
            "Consider updating your prompt."
            "\033[0m", flush=True
        )
        return False, ""

    def check_task_success(
        self,
        *,
        task,
        context,
        textual_state_before,
        textual_state,
        new_achievements=None,
        log="",
        error="",
        max_retries=5,
    ):
        if self.mode == "manual":
            return self.human_check_task_success()

        if self.mode == "auto":
            messages = [
                self.render_system_message(),
                self.render_human_message(
                    task=task,
                    context=context,
                    textual_state_before=textual_state_before,
                    textual_state=textual_state,
                    new_achievements=new_achievements or [],
                    log=log,
                    error=error,
                ),
            ]

            return self.ai_check_task_success(
                messages=messages,
                max_retries=max_retries,
            )

        raise ValueError(f"Invalid critic agent mode: {self.mode}")
