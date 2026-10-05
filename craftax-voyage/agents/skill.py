import os

import utils as U
from langchain.chat_models import ChatOpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.schema import HumanMessage, SystemMessage
from langchain.vectorstores import Chroma

from prompts import load_prompt
from control_primitives import load_control_primitives


class SkillManager:
    def __init__(
        self,
        model_name="Qwen/Qwen3.5-4B",
        temperature=0,
        retrieval_top_k=5,
        request_timeout=120,
        api_base="http://localhost:8000/v1",
        embedding_model_name="Qwen/Qwen3-Embedding-0.6B",
        embedding_api_base="http://localhost:8001/v1",
        ckpt_dir="ckpt",
        resume=False,
    ):
        self.llm = ChatOpenAI(
            model_name=model_name,
            temperature=temperature,
            request_timeout=request_timeout,
            openai_api_base=api_base,
            openai_api_key="EMPTY",
        )

        self.embedding_model = OpenAIEmbeddings(
            model=embedding_model_name,
            openai_api_base=embedding_api_base,
            openai_api_key="EMPTY",
        )

        self.retrieval_top_k = retrieval_top_k
        self.ckpt_dir = ckpt_dir

        U.f_mkdir(f"{ckpt_dir}/skill/code")
        U.f_mkdir(f"{ckpt_dir}/skill/description")
        U.f_mkdir(f"{ckpt_dir}/skill/vectordb")

        # Programs for environment execution.
        self.control_primitives = load_control_primitives()

        if resume:
            print(
                f"\033[33mLoading Skill Manager from "
                f"{ckpt_dir}/skill\033[0m"
            )
            self.skills = U.load_json(
                f"{ckpt_dir}/skill/skills.json"
            )
        else:
            self.skills = {}

        self.vectordb = Chroma(
            collection_name="skill_vectordb",
            embedding_function=self.embedding_model,
            persist_directory=f"{ckpt_dir}/skill/vectordb",
        )

        assert self.vectordb._collection.count() == len(self.skills), (
            "Skill Manager's vectordb is not synced with skills.json.\n"
            f"There are "
            f"{self.vectordb._collection.count()} skills in vectordb "
            f"but {len(self.skills)} skills in skills.json.\n"
            "Did you set resume=False when initializing the manager?\n"
            "You may need to manually delete the vectordb directory "
            "for running from scratch."
        )

    @property
    def programs(self):
        """
        Return all currently available skills and control primitives
        as executable Python code.
        """

        programs = ""

        for skill_name, entry in self.skills.items():
            programs += f"{entry['code']}\n\n"

        for primitives in self.control_primitives:
            programs += f"{primitives}\n\n"

        return programs

    def add_new_skill(self, skill):
        """
        Add a newly generated skill to the skill library.

        info must contain:
            program_name
            program_code
        """

        program_name = skill["program_name"]
        program_code = skill["program_code"]

        skill_description = self.generate_skill_description(
            program_name,
            program_code,
        )

        print(
            f"\033[33mSkill Manager generated description for "
            f"{program_name}:\n{skill_description}\033[0m"
        )

        if program_name in self.skills:
            print(
                f"\033[33mSkill {program_name} already exists. "
                f"Rewriting!\033[0m"
            )

            self.vectordb._collection.delete(
                ids=[program_name]
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

        self.vectordb.add_texts(
            texts=[skill_description],
            ids=[program_name],
            metadatas=[{"name": program_name}],
        )

        self.skills[program_name] = {
            "code": program_code,
            "description": skill_description,
        }

        assert self.vectordb._collection.count() == len(
            self.skills
        ), "vectordb is not synced with skills.json"

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

        self.vectordb.persist()

    def generate_skill_description(
        self,
        program_name,
        program_code,
    ):
        """
        Ask the LLM to describe a Python skill.

        The description is stored in the vector database and is
        used for semantic skill retrieval.
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

        skill_description = self.llm(messages).content.strip()

        return (
            f"def {program_name}(...):\n"
            f"    \"\"\"{skill_description}\"\"\""
        )

    def retrieve_skills(self, query):
        """
        Retrieve the most relevant skills for a query.

        Returns the executable Python code of the retrieved skills.
        """

        k = min(
            self.vectordb._collection.count(),
            self.retrieval_top_k,
        )

        if k == 0:
            return []

        print(
            f"\033[33mSkill Manager retrieving "
            f"for {k} skills\033[0m"
        )

        docs_and_scores = (
            self.vectordb.similarity_search_with_score(
                query,
                k=k,
            )
        )

        print(
            "\033[33mSkill Manager retrieved skills: "
            + ", ".join(
                doc.metadata["name"]
                for doc, _ in docs_and_scores
            )
            + "\033[0m"
        )

        skills = []

        for doc, _ in docs_and_scores:
            skill_name = doc.metadata["name"]
            skills.append(
                self.skills[skill_name]["code"]
            )

        return skills