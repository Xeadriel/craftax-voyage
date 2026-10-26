from __future__ import annotations
import inspect

import re

from langchain.chat_models import ChatOpenAI
from langchain.prompts import SystemMessagePromptTemplate
from langchain.schema import AIMessage, HumanMessage, SystemMessage

import utils as U
from control_primitives import load_control_primitives_context
from prompts import load_prompt

from .curriculum import TUTORIAL_PATH


class ActionAgent:
    def __init__(
        self,
        model_name="Qwen/Qwen3.5-4B",
        temperature=0.2,
        api_base="http://localhost:8000/v1",
        request_timeout=120,
    ):
        self.llm = ChatOpenAI(
            model_name=model_name,
            temperature=temperature,
            request_timeout=request_timeout,
            openai_api_base=api_base,
            openai_api_key="EMPTY",
            max_tokens=4096,
        )

    def render_system_message(self, skills=None):
        skills = skills or []

        system_template = load_prompt("action_template")

        programs = "\n\n".join(
            load_control_primitives_context() + skills
        )

        response_format = load_prompt("action_response_format")

        response = SystemMessagePromptTemplate.from_template(
            system_template
        ).format(
            programs=programs,
            tutorial=U.load_text(TUTORIAL_PATH),
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
        code="",
        error="",
        log="",
        critique="",
    ):
        observation = ""

        if code:
            observation += f"Code from the last round:\n{code}\n\n"
        else:
            observation += (
                "Code from the last round: No code in the first round\n\n"
            )

        if error:
            observation += f"Execution error:\n{error}\n\n"
        else:
            observation += "Execution error: No error\n\n"

        if log:
            observation += f"Log:\n{log}\n\n"
        else:
            observation += "Log: None\n\n"

        observation += f"{textual_state}\n\n"
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
        code="",
        error="",
        log="",
        critique="",
    ):
        """
        Generate and validate an action skill with a single LLM call.

        Like Voyager, every call is one iteration: a response that cannot be
        parsed or validated is not retried here. The caller feeds the error
        back in the next iteration instead.

        Always returns a dictionary.

        Successful result:
            {
                "program_code": str,
                "program_name": str,
                "description": str,
                "generation_failed": False,
                "error": None,
            }

        Failed result:
            {
                "program_code": str,   # the code that failed, "" if none
                "program_name": None,
                "description": "",
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
                code=code,
                error=error,
                log=log,
                critique=critique,
            ),
        ]

        content = ""

        try:
            response = self.llm(messages)
            content = response.content

            print(
                "\033[31m"
                "****Action Agent AI message****\n"
                f"{content}"
                "\033[0m",
                flush=True
            )

            result = self.process_ai_message(response)

        except Exception as e:
            result = (
                "Error while generating the action skill: "
                f"{type(e).__name__}: {e}"
            )

        if isinstance(result, dict):
            return result

        # process_ai_message() returns a string when parsing or
        # validation failed.
        print(
            "\033[35m"
            f"{result}"
            "\033[0m", flush=True
        )

        return {
            "program_code": self.extract_code(content),
            "program_name": None,
            "description": "",
            "generation_failed": True,
            "error": result,
        }

    def extract_code(self, content):
        code_pattern = re.compile(
            r"```(?:python)?\s*(.*?)```",
            re.DOTALL,
        )

        # Skip the reasoning: drafts in it would be executed as well
        content = content.split("</think>")[-1]

        return "\n\n".join(
            block.strip()
            for block in code_pattern.findall(content)
        )

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
            program_code = self.extract_code(message.content)

            if not program_code:
                raise ValueError(
                    "No Python code block found. "
                    "Your response must contain the complete "
                    "skill inside a Python code block."
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

            # Only functions defined by the generated code itself,
            # not functions it imported (e.g. control primitives).
            functions = [
                (name, value)
                for name, value in namespace.items()
                if inspect.isfunction(value)
                and not name.startswith("__")
                and value.__code__.co_filename == "<generated_skill>"
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
                    f"three arguments: state, log_fn, and step_func. "
                    f"It currently takes {argcount}."
                )

            argument_names = code.co_varnames[:argcount]

            expected_arguments = (
                "state",
                "log_fn",
                "step_func",
            )

            if argument_names != expected_arguments:
                raise ValueError(
                    f"Main function '{program_name}' must have the "
                    f"exact signature:\n"
                    f"    def {program_name}"
                    f"(state, log_fn, step_func)\n"
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
