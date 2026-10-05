from __future__ import annotations

import random
import re

import utils as U
from prompts import load_prompt
from utils.json_utils import fix_and_parse_json
from langchain.chat_models import ChatOpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.schema import HumanMessage, SystemMessage
from langchain.vectorstores import Chroma


class CurriculumAgent:
    FLOOR_NAMES = [
        "Overworld",
        "Dungeon",
        "Gnomish Mines",
        "Sewers",
        "Vaults",
        "Troll Mines",
        "Fire Realm",
        "Ice Realm",
        "Graveyard",
    ]

    def __init__(
        self,
        model_name="Qwen/Qwen3.5-4B",
        temperature=0,
        qa_model_name="Qwen/Qwen3.5-4B",
        qa_temperature=0,
        request_timeout=120,
        api_base="http://localhost:8000/v1",
        ckpt_dir="ckpt",
        resume=False,
        mode="auto",
        warm_up=None,
    ):
        self.llm = ChatOpenAI(
            model_name=model_name,
            temperature=temperature,
            request_timeout=request_timeout,
            openai_api_base=api_base,
            openai_api_key="EMPTY",
        )

        self.qa_llm = ChatOpenAI(
            model_name=qa_model_name,
            temperature=qa_temperature,
            request_timeout=request_timeout,
            openai_api_base=api_base,
            openai_api_key="EMPTY",
        )

        assert mode in [
            "auto",
            "manual",
        ], f"mode {mode} not supported"

        self.mode = mode
        self.ckpt_dir = ckpt_dir

        U.f_mkdir(f"{ckpt_dir}/curriculum/vectordb")

        if resume:
            print(
                f"\033[35mLoading Curriculum Agent from "
                f"{ckpt_dir}/curriculum\033[0m"
            )

            self.completed_tasks = U.load_json(
                f"{ckpt_dir}/curriculum/completed_tasks.json"
            )

            self.failed_tasks = U.load_json(f"{ckpt_dir}/curriculum/failed_tasks.json")

            self.qa_cache = U.load_json(f"{ckpt_dir}/curriculum/qa_cache.json")
        else:
            self.completed_tasks = []
            self.failed_tasks = []
            self.qa_cache = {}

        self.qa_cache_questions_vectordb = Chroma(
            collection_name="qa_cache_questions_vectordb",
            embedding_function=OpenAIEmbeddings(
                model="Qwen/Qwen3-Embedding-0.6B",
                openai_api_base=api_base,
                openai_api_key="EMPTY",
            ),
            persist_directory=f"{ckpt_dir}/curriculum/vectordb",
        )

        assert self.qa_cache_questions_vectordb._collection.count() == len(
            self.qa_cache
        ), (
            "Curriculum Agent's QA cache question vectordb is not "
            "synced with qa_cache.json.\n"
            f"There are "
            f"{self.qa_cache_questions_vectordb._collection.count()} "
            f"questions in vectordb but {len(self.qa_cache)} questions "
            f"in qa_cache.json.\n"
            "Did you set resume=False when initializing the agent?\n"
            "You may need to manually delete the QA cache vectordb "
            "directory for running from scratch."
        )

        if not warm_up:
            warm_up = self.default_warmup

        self.warm_up = {}

        for key in self.curriculum_observations:
            self.warm_up[key] = warm_up.get(
                key,
                self.default_warmup[key],
            )

        self.warm_up["completed_tasks"] = 0
        self.warm_up["failed_tasks"] = 0

    @property
    def default_warmup(self):
        return {
            "floor": 0,
            "state": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "context": 15,
        }

    @property
    def curriculum_observations(self):
        return [
            "floor",
            "state",
            "context",
            "completed_tasks",
            "failed_tasks",
        ]

    @property
    def progress(self):
        return len(self.completed_tasks)

    def render_system_message(self):
        system_message = SystemMessage(content=load_prompt("curriculum"))

        assert isinstance(system_message, SystemMessage)

        return system_message

    def render_observation(
        self,
        *,
        env_state,
        textual_state,
    ):
        floor = int(env_state.player_level)

        if 0 <= floor < len(self.FLOOR_NAMES):
            floor_name = self.FLOOR_NAMES[floor]
        else:
            floor_name = f"Unknown floor ({floor})"

        completed_tasks = (
            ", ".join(self.completed_tasks) if self.completed_tasks else "None"
        )

        failed_tasks = ", ".join(self.failed_tasks) if self.failed_tasks else "None"

        observation = {
            "floor": (f"Current floor: {floor} ({floor_name})\n\n"),
            "state": (f"Current Craftax state:\n" f"{textual_state}\n\n"),
            "context": "",
            "completed_tasks": (f"Completed tasks so far: " f"{completed_tasks}\n\n"),
            "failed_tasks": (f"Failed tasks that are too hard: " f"{failed_tasks}\n\n"),
        }

        return observation

    def render_human_message(
        self,
        *,
        env_state,
        textual_state,
    ):
        content = ""

        observation = self.render_observation(
            env_state=env_state,
            textual_state=textual_state,
        )

        if self.progress >= self.warm_up["context"]:
            questions, answers = self.run_qa(
                env_state=env_state,
                textual_state=textual_state,
            )

            i = 1

            for question, answer in zip(questions, answers):
                if "Answer: Unknown" in answer or "language model" in answer:
                    continue

                observation["context"] += f"Question {i}: {question}\n"

                observation["context"] += f"{answer}\n\n"

                i += 1

                if i > 5:
                    break

        for key in self.curriculum_observations:
            if self.progress >= self.warm_up[key]:
                if self.warm_up[key] != 0:
                    should_include = random.random() < 0.8
                else:
                    should_include = True

                if should_include:
                    content += observation[key]

        print("\033[35m****Curriculum Agent human message****\n" f"{content}\033[0m")

        return HumanMessage(content=content)

    def propose_next_task(
        self,
        *,
        env_state,
        textual_state,
        max_retries=5,
    ):
        if self.progress == 0 and self.mode == "auto":
            return (
                "Mine 1 wood",
                "Collect one piece of wood from a tree on the overworld.",
            )

        messages = [
            self.render_system_message(),
            self.render_human_message(
                env_state=env_state,
                textual_state=textual_state,
            ),
        ]

        if self.mode == "auto":
            return self.propose_next_ai_task(
                messages=messages,
                max_retries=max_retries,
            )

        if self.mode == "manual":
            return self.propose_next_manual_task()

        raise ValueError(f"Invalid curriculum agent mode: {self.mode}")

    def propose_next_ai_task(
        self,
        *,
        messages,
        max_retries=5,
    ):
        if max_retries == 0:
            raise RuntimeError("Max retries reached, failed to propose ai task.")

        curriculum = self.llm(messages).content

        print("\033[31m****Curriculum Agent ai message****\n" f"{curriculum}\033[0m")

        try:
            response = self.parse_ai_message(curriculum)

            assert "next_task" in response

            context = self.get_task_context(response["next_task"])

            return response["next_task"], context

        except Exception as e:
            print(
                "\033[35mError parsing curriculum response: "
                f"{e}. Trying again!\033[0m"
            )

            return self.propose_next_ai_task(
                messages=messages,
                max_retries=max_retries - 1,
            )

    def parse_ai_message(self, message):
        task = ""

        for line in message.split("\n"):
            if line.startswith("Task:"):
                task = line[5:].replace(".", "").strip()

        assert task, "Task not found in Curriculum Agent response"

        return {"next_task": task}

    def propose_next_manual_task(self):
        confirmed = False
        task = ""
        context = ""

        while not confirmed:
            task = input("Enter task: ")
            context = input("Enter context: ")

            print(f"Task: {task}\n" f"Context: {context}")

            confirmed = input("Confirm? (y/n)").lower() in ["y", ""]

        return task, context

    def update_exploration_progress(self, info):
        task = info["task"]

        if info["success"]:
            print(f"\033[35mCompleted task {task}.\033[0m")

            self.completed_tasks.append(task)

        else:
            print(
                f"\033[35mFailed to complete task {task}. "
                f"Skipping to next task.\033[0m"
            )

            self.failed_tasks.append(task)

        self.clean_up_tasks()

    def clean_up_tasks(self):
        updated_completed_tasks = []
        updated_failed_tasks = self.failed_tasks

        for task in self.completed_tasks:
            if task not in updated_completed_tasks:
                updated_completed_tasks.append(task)

        for task in updated_completed_tasks:
            while task in updated_failed_tasks:
                updated_failed_tasks.remove(task)

        self.completed_tasks = updated_completed_tasks
        self.failed_tasks = updated_failed_tasks

        U.dump_json(
            self.completed_tasks,
            f"{self.ckpt_dir}/curriculum/" "completed_tasks.json",
        )

        U.dump_json(
            self.failed_tasks,
            f"{self.ckpt_dir}/curriculum/" "failed_tasks.json",
        )

    def decompose_task(
        self,
        task,
        env_state,
        textual_state,
    ):
        messages = [
            SystemMessage(
                content=load_prompt("curriculum_task_decomposition"),
            ),
            self.render_human_message(
                env_state=env_state,
                textual_state=textual_state,
            ),
            HumanMessage(content=f"Final task: {task}"),
        ]

        print(
            "\033[31m****Curriculum Agent "
            "task decomposition****\n"
            f"Final task: {task}\033[0m"
        )

        response = self.llm(messages).content

        print(
            "\033[31m****Curriculum Agent "
            "task decomposition****\n"
            f"{response}\033[0m"
        )

        return fix_and_parse_json(response)

    # ------------------------------------------------------------------
    # QA
    # ------------------------------------------------------------------

    def run_qa(
        self,
        *,
        env_state,
        textual_state,
    ):
        """
        Run the two-stage curriculum QA process.

        Stage 1:
            Generate knowledge questions relevant to the current
            Craftax floor.

        Stage 2:
            Answer those questions and cache the answers.
        """

        questions_new, _ = self.run_qa_step1_ask_questions(
            env_state=env_state,
            textual_state=textual_state,
        )

        questions = []
        answers = []

        for question in questions_new:
            if self.qa_cache_questions_vectordb._collection.count() > 0:
                docs_and_scores = (
                    self.qa_cache_questions_vectordb.similarity_search_with_score(
                        question,
                        k=1,
                    )
                )

                if docs_and_scores and docs_and_scores[0][1] < 0.05:
                    question_cached = docs_and_scores[0][0].page_content

                    assert question_cached in self.qa_cache

                    answer_cached = self.qa_cache[question_cached]

                    questions.append(question_cached)
                    answers.append(answer_cached)

                    continue

            answer = self.run_qa_step2_answer_questions(question=question)

            assert question not in self.qa_cache

            self.qa_cache[question] = answer

            self.qa_cache_questions_vectordb.add_texts(
                texts=[question],
            )

            U.dump_json(
                self.qa_cache,
                f"{self.ckpt_dir}/curriculum/" "qa_cache.json",
            )

            self.qa_cache_questions_vectordb.persist()

            questions.append(question)
            answers.append(answer)

        assert len(questions_new) == len(questions) == len(answers)

        return questions, answers

    def run_qa_step1_ask_questions(
        self,
        *,
        env_state,
        textual_state,
    ):
        """
        Stage 1 of curriculum QA.

        The current Craftax floor is used as the main source
        of environment context instead of the Minecraft biome.
        """

        floor = int(env_state.player_level)

        if 0 <= floor < len(self.FLOOR_NAMES):
            floor_name = self.FLOOR_NAMES[floor]
        else:
            floor_name = f"floor {floor}"

        questions = [
            (
                f"What blocks can I find "
                f"on the {floor_name} in Craftax?"
            ),
            (
                f"What items and resources can I "
                f"find on the {floor_name} in Craftax?"
            ),
            (
                f"What creatures and enemies can I encounter "
                f"on the {floor_name} in Craftax?"
            ),
        ]

        concepts = [floor_name, floor_name, floor_name]

        messages = [
            self.render_system_message_qa_step1_ask_questions(),
            self.render_human_message_qa_step1_ask_questions(
                env_state=env_state,
                textual_state=textual_state,
            ),
        ]

        qa_response = self.qa_llm(messages).content

        print("\033[31m****Curriculum Agent QA step 1****\n" f"{qa_response}\033[0m")

        try:
            pattern = r"Question \d+: (.+)\n" r"Concept \d+: (.+)"

            pairs = re.findall(
                pattern,
                qa_response,
            )

            questions_new = [pair[0] for pair in pairs]

            concepts_new = [pair[1] for pair in pairs]

            assert len(questions_new) == len(concepts_new)

            questions.extend(questions_new)
            concepts.extend(concepts_new)

        except Exception as e:
            print(
                "\033[35mError parsing curriculum response "
                "for QA step 1 ask questions: "
                f"{e}.\033[0m"
            )

        return questions, concepts

    def render_system_message_qa_step1_ask_questions(self):
        return SystemMessage(content=load_prompt("curriculum_qa_step1_ask_questions"))

    def render_human_message_qa_step1_ask_questions(
        self,
        *,
        env_state,
        textual_state,
    ):
        observation = self.render_observation(
            env_state=env_state,
            textual_state=textual_state,
        )

        content = ""

        for key in self.curriculum_observations:
            content += observation[key]

        return HumanMessage(content=content)

    def run_qa_step2_answer_questions(
        self,
        question,
    ):
        messages = [
            self.render_system_message_qa_step2_answer_questions(),
            self.render_human_message_qa_step2_answer_questions(question=question),
        ]

        print(f"\033[35mCurriculum Agent Question: " f"{question}\033[0m")

        qa_answer = self.qa_llm(messages).content

        print(f"\033[31mCurriculum Agent " f"{qa_answer}\033[0m")

        return qa_answer

    def get_task_context(self, task):
        question = f"How to {task.replace('_', ' ')} " f"in Craftax?"

        if question in self.qa_cache:
            answer = self.qa_cache[question]

        else:
            answer = self.run_qa_step2_answer_questions(question=question)

            self.qa_cache[question] = answer

            self.qa_cache_questions_vectordb.add_texts(
                texts=[question],
            )

            U.dump_json(
                self.qa_cache,
                f"{self.ckpt_dir}/curriculum/" "qa_cache.json",
            )

            self.qa_cache_questions_vectordb.persist()

        return f"Question: {question}\n" f"{answer}"

    def render_system_message_qa_step2_answer_questions(self):
        return SystemMessage(
            content=load_prompt("curriculum_qa_step2_answer_questions")
        )

    def render_human_message_qa_step2_answer_questions(
        self,
        question,
    ):
        return HumanMessage(content=f"Question: {question}")
