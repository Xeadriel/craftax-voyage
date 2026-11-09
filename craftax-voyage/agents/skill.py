import os

import utils as U
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

from prompts import load_prompt


class SkillManager:
    """
    Skill library without retrieval: every learned skill is handed to the
    agents in full (code for the action agent, descriptions for the
    curriculum agent) instead of being looked up through embeddings.
    """

    def __init__(
        self,
        model_name="Qwen/Qwen3.5-4B",
        temperature=0,
        request_timeout=120,
        api_base="http://localhost:8000/v1",
        ckpt_dir="ckpt",
    ):
        self.llm = ChatOpenAI(
            model_name=model_name,
            temperature=temperature,
            request_timeout=request_timeout,
            openai_api_base=api_base,
            openai_api_key="EMPTY",
            # A one-line description needs no reasoning; with thinking on,
            # greedy decoding can loop until the request times out
            max_tokens=512,
            model_kwargs={
                "extra_body": {"chat_template_kwargs": {"enable_thinking": False}}
            },
        )

        self.ckpt_dir = ckpt_dir

        U.f_mkdir(f"{ckpt_dir}/skill/code")
        U.f_mkdir(f"{ckpt_dir}/skill/description")

        skills_path = f"{ckpt_dir}/skill/skills.json"

        # Learned skills are always kept, with or without --resume: a new
        # world continues learning from the existing library
        if U.f_exists(skills_path):
            print(
                f"\033[33mLoading Skill Manager from "
                f"{ckpt_dir}/skill\033[0m", flush=True
            )
            self.skills = U.load_json(skills_path)
        else:
            self.skills = {}

    @property
    def programs(self):
        """
        Return all learned skills as executable Python code.
        """

        return "\n\n".join(
            entry["code"] for entry in self.skills.values()
        )

    def skill_code_list(self):
        """
        Source code of every learned skill, for the action agent's prompt.
        """

        return [entry["code"] for entry in self.skills.values()]

    def skill_summaries(self):
        """
        One line per learned skill, for the curriculum agent's prompt.
        """

        if not self.skills:
            return "None"

        return "\n".join(
            f"{skill_name}: {entry['description']}"
            for skill_name, entry in self.skills.items()
        )

    def add_new_skill(self, info):
        """
        Add a newly generated skill to the skill library.

        info must contain:
            program_name
            program_code
        """

        program_name = info["program_name"]
        program_code = info["program_code"]

        skill_description = self.generate_skill_description(
            program_name,
            program_code,
        )

        print(
            f"\033[33mSkill Manager generated description for "
            f"{program_name}:\n{skill_description}\033[0m", flush=True
        )

        if program_name in self.skills:
            print(
                f"\033[33mSkill {program_name} already exists. "
                f"Rewriting!\033[0m", flush=True
            )

            i = 2
            while (
                f"{program_name}V{i}.py"
                in os.listdir(f"{self.ckpt_dir}/skill/code")
            ):
                i += 1

            dumped_program_name = f"{program_name}V{i}"

        else:
            dumped_program_name = program_name

        self.skills[program_name] = {
            "code": program_code,
            "description": skill_description,
        }

        U.dump_text(
            program_code,
            f"{self.ckpt_dir}/skill/code/"
            f"{dumped_program_name}.py",
        )

        U.dump_text(
            skill_description,
            f"{self.ckpt_dir}/skill/description/"
            f"{dumped_program_name}.txt",
        )

        U.dump_json(
            self.skills,
            f"{self.ckpt_dir}/skill/skills.json",
        )

    def generate_skill_description(
        self,
        program_name,
        program_code,
    ):
        """
        Ask the LLM to describe a Python skill in a single line.

        The description is shown to the curriculum agent so it knows
        which skills have already been learned.
        """

        messages = [
            SystemMessage(
                content=load_prompt("skill")
            ),
            HumanMessage(
                content=(
                    program_code
                    + "\n\n"
                    + f"The main function is `{program_name}`."
                )
            ),
        ]

        return " ".join(
            self.llm(messages).content.split()
        )
