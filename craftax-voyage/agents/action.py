from __future__ import annotations
import inspect

import re
import time

from langchain.chat_models import ChatOpenAI
from langchain.prompts import SystemMessagePromptTemplate
from langchain.schema import AIMessage, HumanMessage, SystemMessage

from control_primitives import load_control_primitives
from craftax.craftax.renderer import render_craftax_text
from prompts import load_prompt


class ActionAgent:
    def __init__(
        self,
        model_name="Qwen/Qwen3.5-4B",
        temperature=0,
        api_base="http://localhost:8000/v1",
        request_timeout=120,
    ):
        self.llm = ChatOpenAI(
            model_name=model_name,
            temperature=temperature,
            request_timeout=request_timeout,
            openai_api_base=api_base,
            openai_api_key="EMPTY",
        )

    def render_system_message(self, skills=None):
        skills = skills or []

        system_template = load_prompt("action_template")

        programs = "\n\n".join(
            skills
        )

        response_format = load_prompt("action_response_format")

        response = SystemMessagePromptTemplate.from_template(
            system_template
        ).format(
            programs=programs,
            response_format=response_format,
        )

        assert isinstance(response, SystemMessage)

        return response

    def render_human_message(
        self,
        *,
        task,
        context,
        textual_state,
        skills=None,
        critique="",
    ):
        observation = ""

        if skills:
            observation += (
                "Retrieved skills:\n"
                + "\n\n".join(skills)
                + "\n\n"
            )
        else:
            observation += "Retrieved skills: None\n\n"

        observation += f"Current state:\n{textual_state}\n\n"
        observation += f"Task: {task}\n\n"

        if context:
            observation += f"Context: {context}\n\n"
        else:
            observation += "Context: None\n\n"

        if critique:
            observation += f"Critique: {critique}\n\n"
        else:
            observation += "Critique: None\n\n"

        return HumanMessage(content=observation)

    def generate_skill(
        self,
        *,
        task,
        context,
        textual_state,
        skills=None,
        critique="",
        max_retries=3,
    ):
        """
        Generate and validate an action skill.

        Always returns a dictionary.

        Successful result:
            {
                "program_code": str,
                "program_name": str,
                "description": str,
                "generation_failed": False,
                "error": None,
            }

        Failed result after all retries:
            {
                "program_code": str,
                "program_name": "failed_action_skill",
                "description": str,
                "generation_failed": True,
                "error": str,
            }
        """

        messages = [
            self.render_system_message(skills),
            self.render_human_message(
                task=task,
                context=context,
                textual_state=textual_state,
                skills=skills,
                critique=critique,
            ),
        ]

        retry = max_retries
        error = None

        while retry > 0:
            # Important:
            # Reset this every iteration so an old AI response cannot
            # accidentally be appended if the next LLM call fails.
            response = None

            try:
                response = self.llm(messages)

                print(
                    "\033[31m"
                    "****Action Agent AI message****\n"
                    f"{response.content}"
                    "\033[0m",
                    flush=True
                )

                result = self.process_ai_message(response)

                # process_ai_message() returns a string when parsing
                # or validation failed.
                if isinstance(result, str):
                    error = result

                    print(
                        "\033[35m"
                        f"{error}"
                        "\033[0m"
                    )

                    # Preserve the failed AI response.
                    messages.append(response)

                    # Give the exact error back to the model so that
                    # it can correct its generated skill.
                    messages.append(
                        HumanMessage(
                            content=(
                                f"{error}\n\n"
                                "Fix the problem and generate the "
                                "complete corrected skill again."
                            )
                        )
                    )

                    retry -= 1

                    if retry > 0:
                        time.sleep(1)

                    continue

                # Successful skill generation.
                return result

            except Exception as e:
                error = (
                    "Error while generating the action skill: "
                    f"{type(e).__name__}: {e}"
                )

                print(
                    "\033[35m"
                    f"{error}"
                    "\033[0m"
                )

                # Only append an AI response from this iteration.
                if response is not None:
                    messages.append(response)

                messages.append(
                    HumanMessage(
                        content=(
                            f"{error}\n\n"
                            "Fix the problem and generate the "
                            "complete corrected skill again."
                        )
                    )
                )

                retry -= 1

                if retry > 0:
                    time.sleep(1)

        # ---------------------------------------------------------
        # All retries failed.
        #
        # IMPORTANT:
        # Never return a string here.
        # generate_skill() ALWAYS returns a dictionary.
        # ---------------------------------------------------------

        error = error or "Unknown action-generation error."

        print(
            "\033[35m"
            "Action Agent failed after all retries.\n"
            f"{error}"
            "\033[0m"
        )

        fallback_code = f'''def failed_action_skill(state, step_func, log_fn):
    """Fallback skill generated because ActionAgent failed."""
    log_fn("ActionAgent failed to generate a valid skill.")
    return False
'''

        return {
            "program_code": fallback_code,
            "program_name": "failed_action_skill",
            "description": (
                "Fallback skill: ActionAgent failed to generate "
                f"a valid skill after {max_retries} attempts. "
                f"Error: {error}"
            ),
            "generation_failed": True,
            "error": error,
        }

    def process_ai_message(self, message):
        """
        Parse and validate the AI-generated skill.

        Returns:
            dict: Valid skill.
            str: Error message that should be fed back to the AI.
        """

        if not isinstance(message, AIMessage):
            return (
                "Error parsing action response: "
                f"Expected AIMessage, got {type(message).__name__}."
            )

        try:
            code_pattern = re.compile(
                r"```(?:python)?\s*(.*?)```",
                re.DOTALL,
            )

            code_blocks = code_pattern.findall(message.content)

            if not code_blocks:
                raise ValueError(
                    "No Python code block found. "
                    "Your response must contain the complete "
                    "skill inside a Python code block."
                )

            program_code = "\n\n".join(
                block.strip()
                for block in code_blocks
            )

            # Use a separate namespace for generated code.
            #
            # This prevents imported/global callables from being
            # accidentally selected as the generated skill.
            namespace = {
                "__builtins__": __builtins__,
            }

            try:
                exec(
                    compile(
                        program_code,
                        "<generated_skill>",
                        "exec",
                    ),
                    namespace,
                )
            except Exception as e:
                raise ValueError(
                    "Generated Python code is invalid and could "
                    "not be compiled/executed:\n"
                    f"{type(e).__name__}: {e}"
                ) from e

            # Only functions defined by the generated code.
            functions = [
                (name, value)
                for name, value in namespace.items()
                if inspect.isfunction(value)
                and not name.startswith("__")
            ]

            if not functions:
                raise ValueError(
                    "No function found in the generated code."
                )

            if len(functions) > 1:
                raise ValueError(
                    "Generated code must contain exactly one "
                    "skill function. "
                    f"Found {len(functions)} functions: "
                    + ", ".join(name for name, _ in functions)
                )

            program_name, main_function = functions[0]

            if not hasattr(main_function, "__code__"):
                raise ValueError(
                    f"'{program_name}' is not a valid Python function."
                )

            # Validate the exact function signature.
            code = main_function.__code__

            argcount = code.co_argcount

            if argcount != 3:
                raise ValueError(
                    f"Main function '{program_name}' must take exactly "
                    f"three arguments: state, step_func, and log_fn. "
                    f"It currently takes {argcount}."
                )

            argument_names = code.co_varnames[:argcount]

            expected_arguments = (
                "state",
                "step_func",
                "log_fn",
            )

            if argument_names != expected_arguments:
                raise ValueError(
                    f"Main function '{program_name}' must have the "
                    f"exact signature:\n"
                    f"    def {program_name}"
                    f"(state, step_func, log_fn)\n"
                    f"It currently has arguments: "
                    f"{argument_names}."
                )

            return {
                "program_code": program_code,
                "program_name": program_name,
                "description": self.extract_description(
                    message.content
                ),
                "generation_failed": False,
                "error": None,
            }

        except Exception as e:
            return (
                "Error parsing action response "
                "(before program execution): "
                f"{type(e).__name__}: {e}"
            )

    def extract_description(self, content):
        code_pattern = re.compile(
            r"```(?:python)?\s*.*?```",
            re.DOTALL,
        )

        description = code_pattern.sub(
            "",
            content,
        ).strip()

        return description or "No description provided."

    def render_current_state(self, env_state):
        return render_craftax_text(env_state)
