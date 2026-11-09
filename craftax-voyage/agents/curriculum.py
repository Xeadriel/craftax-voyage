from __future__ import annotations

import random
import re
from pathlib import Path

import utils as U
from prompts import load_prompt
from utils.json_utils import fix_and_parse_json
from utils.situation_report import FLOOR_NAMES, situation_report
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage


TUTORIAL_PATH = Path(__file__).resolve().parent.parent / "tutorial_detailed.md"


class CurriculumAgent:
    FLOOR_NAMES = FLOOR_NAMES

    DEATH_NOTICE = (
        "You died during the last task. The world was reset: inventory, equipment "
        "and floor progress are gone. Learned skills remain."
    )

    def __init__(
        self,
        model_name="Qwen/Qwen3.5-4B",
        temperature=0.2,
        qa_model_name="Qwen/Qwen3.5-4B",
        qa_temperature=0.2,
        request_timeout=120,
        api_base="http://localhost:8000/v1",
        ckpt_dir="ckpt",
        resume=False,
        mode="auto",
        warm_up=None,
        use_qa=False,
    ):
        self.llm = ChatOpenAI(
            model_name=model_name,
            temperature=temperature,
            request_timeout=request_timeout,
            openai_api_base=api_base,
            openai_api_key="EMPTY",
            max_tokens=4096,
        )

        self.qa_llm = ChatOpenAI(
            model_name=qa_model_name,
            temperature=qa_temperature,
            request_timeout=request_timeout,
            openai_api_base=api_base,
            openai_api_key="EMPTY",
            # QA answers are short lookups; with thinking on, greedy
            # decoding can loop until the request times out
            max_tokens=1024,
            model_kwargs={
                "extra_body": {"chat_template_kwargs": {"enable_thinking": False}}
            },
        )

        assert mode in [
            "auto",
            "manual",
        ], f"mode {mode} not supported"

        self.mode = mode
        self.ckpt_dir = ckpt_dir
        # The QA answers of a small model were wrong often and stay cached forever;
        # the tutorial is in every system prompt anyway
        self.use_qa = use_qa

        U.f_mkdir(f"{ckpt_dir}/curriculum")

        self.completed_tasks = []
        self.failed_tasks = []
        # Tasks completed in the current world, cleared when the player dies
        self.world_progress = []
        # Recap of the last task, shown to the curriculum in its next turn
        self.last_turn = None
        self.qa_cache = {}

        # The learning history belongs to the skill library, which is always
        # kept, so it is loaded with or without --resume
        print(
            f"\033[35mLoading Curriculum Agent from "
            f"{ckpt_dir}/curriculum\033[0m", flush=True
        )

        if U.f_exists(f"{ckpt_dir}/curriculum/completed_tasks.json"):
            self.completed_tasks = U.load_json(
                f"{ckpt_dir}/curriculum/completed_tasks.json"
            )

        if U.f_exists(f"{ckpt_dir}/curriculum/failed_tasks.json"):
            self.failed_tasks = U.load_json(
                f"{ckpt_dir}/curriculum/failed_tasks.json"
            )

        if U.f_exists(f"{ckpt_dir}/curriculum/qa_cache.json"):
            self.qa_cache = U.load_json(
                f"{ckpt_dir}/curriculum/qa_cache.json"
            )

        # What was achieved in the current world only continues with the
        # world itself (--resume); a new world starts empty
        if resume and U.f_exists(f"{ckpt_dir}/curriculum/world_progress.json"):
            self.world_progress = U.load_json(
                f"{ckpt_dir}/curriculum/world_progress.json"
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
            "recap": 0,
            "state": 0,
            "context": 0,
            "skills": 0,
            "completed_tasks": 0,
            "world_progress": 0,
            "failed_tasks": 0,
        }

    @property
    def curriculum_observations(self):
        return [
            "recap",
            "state",
            "context",
            "skills",
            "completed_tasks",
            "world_progress",
            "failed_tasks",
        ]

    @property
    def progress(self):
        return len(self.completed_tasks)

    @staticmethod
    def prompt_with_tutorial(prompt_name):
        return load_prompt(prompt_name).replace(
            "{Craftax tutorial.md file}",
            U.load_text(TUTORIAL_PATH),
        )

    def render_system_message(self):
        system_message = SystemMessage(
            content=self.prompt_with_tutorial("curriculum")
        )

        assert isinstance(system_message, SystemMessage)

        return system_message

    def render_recap(self):
        if self.last_turn is None:
            return ""

        turn = self.last_turn
        recap = ""

        if turn["died"]:
            recap += f"{self.DEATH_NOTICE}\n"

        outcome = "succeeded" if turn["success"] else "failed"
        attempts = turn["attempts"]
        recap += (
            f'Last turn: "{turn["task"]}" -> {outcome} after '
            f'{attempts} attempt{"" if attempts == 1 else "s"}'
        )

        if turn["critique"]:
            recap += f"; critique: {turn['critique']}"

        if turn["vitals_before"] and turn["vitals_after"]:
            changes = ", ".join(
                f"{name} {before[0]:g}/{before[1]} -> "
                f"{turn['vitals_after'][name][0]:g}/{turn['vitals_after'][name][1]}"
                for name, before in turn["vitals_before"].items()
                if name in ("health", "food", "drink", "energy")
            )
            recap += f"; {changes}"

        return recap + "\n\n"

    def render_observation(
        self,
        *,
        env_state,
        skills="None",
    ):
        completed_tasks = (
            ", ".join(self.completed_tasks) if self.completed_tasks else "None"
        )

        world_progress = (
            ", ".join(self.world_progress) if self.world_progress else "None"
        )

        failed_tasks = ", ".join(self.failed_tasks) if self.failed_tasks else "None"

        observation = {
            "recap": self.render_recap(),
            "state": (f"Current situation:\n" f"{situation_report(env_state)}\n\n"),
            "context": "",
            "skills": (f"Learned skills:\n" f"{skills}\n\n"),
            "completed_tasks": (f"Completed tasks so far (all worlds): " f"{completed_tasks}\n\n"),
            "world_progress": (f"Completed in the current world: " f"{world_progress}\n\n"),
            "failed_tasks": (f"Failed tasks that are too hard: " f"{failed_tasks}\n\n"),
        }

        return observation

    def render_human_message(
        self,
        *,
        env_state,
        skills="None",
    ):
        content = ""

        observation = self.render_observation(
            env_state=env_state,
            skills=skills,
        )

        if self.use_qa and self.progress >= self.warm_up["context"]:
            questions, answers = self.run_qa(
                env_state=env_state,
                skills=skills,
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

        print("\033[35m****Curriculum Agent human message****\n" f"{content}\033[0m", flush=True)

        return HumanMessage(content=content)

    def propose_next_task(
        self,
        *,
        env_state,
        skills="None",
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
                skills=skills,
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

        print("\033[31m****Curriculum Agent ai message****\n" f"{curriculum}\033[0m", flush=True)

        try:
            response = self.parse_ai_message(curriculum)

            assert "next_task" in response

            context = self.get_task_context(response["next_task"])

            return response["next_task"], context

        except Exception as e:
            print(
                "\033[35mError parsing curriculum response: "
                f"{e}. Trying again!\033[0m", flush=True
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

            print(f"Task: {task}\n" f"Context: {context}", flush=True)

            confirmed = input("Confirm? (y/n)").lower() in ["y", ""]

        return task, context

    def update_exploration_progress(self, info):
        task = info["task"]
        died = info.get("died", False)

        if info["success"]:
            print(f"\033[35mCompleted task {task}.\033[0m", flush=True)

            self.completed_tasks.append(task)
            self.world_progress.append(task)

        else:
            print(
                f"\033[35mFailed to complete task {task}. "
                f"Skipping to next task.\033[0m", flush=True
            )

            self.failed_tasks.append(task)

        if died:
            # A new world: nothing done in the old one counts anymore
            self.world_progress = []

        self.last_turn = {
            "task": task,
            "success": info["success"],
            "critique": info.get("critique", ""),
            "attempts": info.get("attempts", 1),
            "died": died,
            "vitals_before": info.get("vitals_before"),
            "vitals_after": info.get("vitals_after"),
        }

        self.clean_up_tasks()

    def clean_up_tasks(self):
        updated_completed_tasks = []
        updated_world_progress = []
        updated_failed_tasks = self.failed_tasks

        for task in self.completed_tasks:
            if task not in updated_completed_tasks:
                updated_completed_tasks.append(task)

        for task in self.world_progress:
            if task not in updated_world_progress:
                updated_world_progress.append(task)

        for task in updated_completed_tasks:
            while task in updated_failed_tasks:
                updated_failed_tasks.remove(task)

        self.completed_tasks = updated_completed_tasks
        self.world_progress = updated_world_progress
        self.failed_tasks = updated_failed_tasks

        U.dump_json(
            self.completed_tasks,
            f"{self.ckpt_dir}/curriculum/" "completed_tasks.json",
        )

        U.dump_json(
            self.world_progress,
            f"{self.ckpt_dir}/curriculum/" "world_progress.json",
        )

        U.dump_json(
            self.failed_tasks,
            f"{self.ckpt_dir}/curriculum/" "failed_tasks.json",
        )

    def decompose_task(
        self,
        task,
        env_state,
        skills="None",
        max_retries=5,
    ):
        messages = [
            self.render_system_message_task_decomposition(),
            self.render_human_message_task_decomposition(
                env_state=env_state,
                skills=skills,
                task=task,
            ),
        ]

        print(
            "\033[31m****Curriculum Agent "
            "task decomposition****\n"
            f"Final task: {task}\033[0m", flush=True
        )

        for attempt in range(max_retries):
            response = self.llm(messages).content

            print(
                "\033[31m****Curriculum Agent "
                "task decomposition****\n"
                f"{response}\033[0m", flush=True
            )

            try:
                # Only the list after "Sub-goals:", so a "[quantity]" in the
                # reasoning is not taken for it
                _, _, sub_goals_text = response.rpartition("Sub-goals:")
                sub_goals = fix_and_parse_json(sub_goals_text)

                if not (
                    isinstance(sub_goals, list)
                    and sub_goals
                    and all(isinstance(goal, str) for goal in sub_goals)
                ):
                    raise ValueError("Expected a non-empty JSON list of strings")

                return [goal.strip() for goal in sub_goals]

            except Exception as e:
                print(
                    "\033[35mError parsing task decomposition: "
                    f"{e}. Trying again ({attempt + 1}/{max_retries})!\033[0m", flush=True
                )

        raise RuntimeError("Max retries reached, failed to decompose the task.")

    def render_system_message_task_decomposition(self):
        return SystemMessage(
            content=self.prompt_with_tutorial("curriculum_task_decomposition")
        )

    def render_human_message_task_decomposition(
        self,
        *,
        env_state,
        task,
        skills="None",
    ):
        # Only the situation now: the task lists and recap belong to the
        # learning run, not to the world the task is solved in
        return HumanMessage(
            content=(
                f"Current situation:\n{situation_report(env_state)}\n\n"
                f"Learned skills:\n{skills}\n\n"
                f"Final task: {task}"
            )
        )

    # ------------------------------------------------------------------
    # QA
    # ------------------------------------------------------------------

    def run_qa(
        self,
        *,
        env_state,
        skills="None",
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
            skills=skills,
        )

        questions = []
        answers = []

        for question in questions_new:
            questions.append(question)
            answers.append(self.answer_question_cached(question))

        assert len(questions_new) == len(questions) == len(answers)

        return questions, answers

    def run_qa_step1_ask_questions(
        self,
        *,
        env_state,
        skills="None",
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
                    skills=skills,
            ),
        ]

        qa_response = self.qa_llm(messages).content

        print("\033[31m****Curriculum Agent QA step 1****\n" f"{qa_response}\033[0m", flush=True)

        try:
            # The number after "Concept" is optional: the prompt's examples
            # write "Concept:", and small models copy them
            pattern = r"Question \d+: (.+)\n" r"Concept(?: \d+)?: (.+)"

            pairs = re.findall(
                pattern,
                qa_response,
            )

            questions_new = [pair[0].strip() for pair in pairs]

            concepts_new = [pair[1].strip() for pair in pairs]

            assert len(questions_new) == len(concepts_new)

            if not pairs:
                print(
                    "\033[35mQA step 1: no questions could be parsed "
                    "from the response.\033[0m", flush=True
                )

            questions.extend(questions_new)
            concepts.extend(concepts_new)

        except Exception as e:
            print(
                "\033[35mError parsing curriculum response "
                "for QA step 1 ask questions: "
                f"{e}.\033[0m", flush=True
            )

        return questions, concepts

    def render_system_message_qa_step1_ask_questions(self):
        return SystemMessage(content=load_prompt("curriculum_qa_step1_ask_questions"))

    def render_human_message_qa_step1_ask_questions(
        self,
        *,
        env_state,
        skills="None",
    ):
        observation = self.render_observation(
            env_state=env_state,
            skills=skills,
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

        print(f"\033[35mCurriculum Agent Question: " f"{question}\033[0m", flush=True)

        qa_answer = self.qa_llm(messages).content

        print(f"\033[31mCurriculum Agent " f"{qa_answer}\033[0m", flush=True)

        return qa_answer

    def answer_question_cached(self, question):
        """
        Answer a question, reusing the cached answer for an identical question.
        """

        if question in self.qa_cache:
            return self.qa_cache[question]

        answer = self.run_qa_step2_answer_questions(question=question)

        self.qa_cache[question] = answer

        U.dump_json(
            self.qa_cache,
            f"{self.ckpt_dir}/curriculum/" "qa_cache.json",
        )

        return answer

    def get_task_context(self, task):
        if not self.use_qa:
            return ""

        # Normalised like Voyager so the cache hits regardless of case
        task_phrase = task.replace("_", " ").replace(".", "").strip().lower()
        question = f"How to {task_phrase} in Craftax?"

        answer = self.answer_question_cached(question)

        return f"Question: {question}\n" f"{answer}"

    def render_system_message_qa_step2_answer_questions(self):
        return SystemMessage(
            content=self.prompt_with_tutorial("curriculum_qa_step2_answer_questions")
        )

    def render_human_message_qa_step2_answer_questions(
        self,
        question,
    ):
        return HumanMessage(content=f"Question: {question}")
