from __future__ import annotations

import argparse
import bz2
import contextlib
import ctypes
import json
import os
import pickle
import signal
import sys
import threading
import time
from pathlib import Path
from typing import Any

import jax
import jax.numpy as jnp
import numpy as np
import pygame

from craftax.craftax.constants import (
    BLOCK_PIXEL_SIZE_HUMAN,
    INVENTORY_OBS_HEIGHT,
    OBS_DIM,
    Achievement,
    Action,
    BlockType,
    ItemType,
    MobType,
)
from craftax.craftax.envs.craftax_symbolic_env import CraftaxSymbolicEnv as CraftaxEnv
from craftax.craftax.renderer import make_craftax_pixel_renderer
from craftax.craftax_env import make_craftax_env_from_name

from agents.curriculum import CurriculumAgent
from agents.action import ActionAgent
from agents.critic import CriticAgent
from agents.skill import SkillManager
from control_primitives import *
from control_primitives import control_primitive_names
# The memory instance (the star import above only brings the module of the same name)
from control_primitives.knowledge import knowledge

import utils as U
from utils.execution_summary import death_critique, primitive_events, state_diff
from utils.situation_report import situation_report, vitals


def save_compressed_pickle(title: str, data: Any):
    # Written to a temporary file first, so an interrupted write (Ctrl+C)
    # never leaves a corrupt file behind
    path = title + ".pbz2"
    with bz2.BZ2File(path + ".tmp", "w") as f:
        pickle.dump(data, f)
    os.replace(path + ".tmp", path)


def load_compressed_pickle(path: str):
    with bz2.BZ2File(path, "r") as f:
        return pickle.load(f)


class Tee:
    """
    A stream that also writes everything to a log file, like piping the
    output through `tee`. Every write is flushed, so the file is live.
    """

    def __init__(self, stream, log_file):
        self.stream = stream
        self.log_file = log_file

    def write(self, text):
        self.stream.write(text)
        self.log_file.write(text)
        self.log_file.flush()
        return len(text)

    def flush(self):
        self.stream.flush()
        self.log_file.flush()

    def __getattr__(self, name):
        return getattr(self.stream, name)


def tee_output(log_path):
    """Copy stdout and stderr to log_path from now on."""

    Path(log_path).parent.mkdir(parents=True, exist_ok=True)
    log_file = open(log_path, "a", encoding="utf-8", errors="replace")
    sys.stdout = Tee(sys.stdout, log_file)
    sys.stderr = Tee(sys.stderr, log_file)
    print(f"Logging to {log_path}", flush=True)


class CraftaxRenderer:
    def __init__(self, pixel_render_size=None):
        if pixel_render_size is None:
            pixel_render_size = 64 // BLOCK_PIXEL_SIZE_HUMAN

        self.pixel_render_size = pixel_render_size
        self.pygame_events = []

        self.screen_size = (
            OBS_DIM[1] * BLOCK_PIXEL_SIZE_HUMAN * pixel_render_size,
            (OBS_DIM[0] + INVENTORY_OBS_HEIGHT)
            * BLOCK_PIXEL_SIZE_HUMAN
            * pixel_render_size,
        )

        pygame.init()
        self.screen_surface = pygame.display.set_mode(self.screen_size)
        pygame.display.set_caption("Craftax Trajectory")

        self._render = jax.jit(
            make_craftax_pixel_renderer(BLOCK_PIXEL_SIZE_HUMAN)
        )

    def update(self):
        self.pygame_events = list(pygame.event.get())
        pygame.display.flip()

    def render(self, env_state):
        self.screen_surface.fill((0, 0, 0))

        pixels = self._render(env_state)
        pixels = jnp.repeat(
            pixels,
            self.pixel_render_size,
            axis=0,
        )
        pixels = jnp.repeat(
            pixels,
            self.pixel_render_size,
            axis=1,
        )

        surface = pygame.surfarray.make_surface(
            np.array(pixels).transpose((1, 0, 2))
        )

        self.screen_surface.blit(surface, (0, 0))

    def is_quit_requested(self):
        return any(
            event.type == pygame.QUIT
            for event in self.pygame_events
        )


def print_new_achievements(old_achievements, new_achievements):
    for i in range(len(old_achievements)):
        if old_achievements[i] == 0 and new_achievements[i] == 1:
            print(
                f"{Achievement(i).name} "
                f"({new_achievements.sum()}/{len(Achievement)})", flush=True
            )


def render_trajectory(path: str, delay: float):
    trajectory = load_compressed_pickle(path)
    states = trajectory["state"]

    print(f"Loaded trajectory: {path}", flush=True)
    print(f"States: {len(states)}", flush=True)
    print(f"Delay: {delay}s", flush=True)

    renderer = CraftaxRenderer()

    for i, state in enumerate(states):
        renderer.render(state)
        renderer.update()

        if renderer.is_quit_requested():
            break

        print(f"\rRendering state {i + 1}/{len(states)}", end="", flush=True)

        if i < len(states) - 1:
            time.sleep(delay)

    print(flush=True)

    while not renderer.is_quit_requested():
        renderer.update()
        time.sleep(0.01)

    pygame.quit()


class SkillAborted(BaseException):
    # Not an Exception, so a generated `except Exception` cannot swallow it
    # and keep the skill looping
    pass


class SkillStepBudgetExceeded(SkillAborted):
    pass


class SkillTimeExceeded(SkillAborted):
    pass


class EpisodeEnded(SkillAborted):
    pass


@contextlib.contextmanager
def time_limit(seconds: float, message: str):
    """Raise SkillTimeExceeded(message) in this thread after `seconds`."""

    if hasattr(signal, "SIGALRM"):
        def _on_timeout(signum, frame):
            raise SkillTimeExceeded(message)

        previous_handler = signal.signal(signal.SIGALRM, _on_timeout)
        signal.setitimer(signal.ITIMER_REAL, seconds)
        try:
            yield
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, previous_handler)
        return

    # No SIGALRM on Windows: a timer thread injects the exception into this
    # thread instead. An injected exception is created without arguments, so
    # a subclass carries the message
    class _Timeout(SkillTimeExceeded):
        def __init__(self):
            super().__init__(message)

    _Timeout.__name__ = SkillTimeExceeded.__name__
    thread_id = ctypes.c_ulong(threading.get_ident())
    lock = threading.Lock()
    done = False

    def _on_timeout():
        with lock:
            if not done:
                ctypes.pythonapi.PyThreadState_SetAsyncExc(
                    thread_id, ctypes.py_object(_Timeout)
                )

    timer = threading.Timer(seconds, _on_timeout)
    timer.daemon = True
    timer.start()
    try:
        yield
    finally:
        with lock:
            done = True
        timer.cancel()
        # Drop an exception that was injected but not raised yet
        ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, None)


class CraftaxVoyage:
    def __init__(self, args):
        self.args = args

        self.env = make_craftax_env_from_name(
            "Craftax-Symbolic-v1",
            auto_reset=True,
        )
        self.env_params = self.env.default_params

        self.env_ckpt_path = f"{args.ckpt_dir}/env/env_state.pbz2"
        self.inference_mode = bool(args.inference_task or args.sub_goals)

        # Number of action agent attempts (generated programs) so far, the
        # unit of Voyager's max_iterations. It continues across resumes.
        self.iteration = 0

        # While learning, the trajectory is written to disk in chunks with
        # every checkpoint, so an interrupted run loses nothing that --resume
        # restores. traj_chunks counts the chunks belonging to the checkpoint.
        self.traj_dir = f"{args.ckpt_dir}/trajectory"
        self.traj_chunks = 0
        # The task in progress at the last checkpoint, resumed at its next attempt
        self.pending_rollout = None

        if (
            args.resume
            and not self.inference_mode
            and U.f_exists(self.env_ckpt_path)
        ):
            # Like Voyager's soft reset: continue in the same world with the
            # same position, inventory and intrinsics
            print(f"Resuming the world from {self.env_ckpt_path}", flush=True)
            env_ckpt = load_compressed_pickle(self.env_ckpt_path)
            self.env_state = env_ckpt["env_state"]
            self.rng = env_ckpt["rng"]
            self.iteration = env_ckpt.get("iteration", 0)
            self.traj_chunks = env_ckpt.get("traj_chunks", 0)
            self.pending_rollout = env_ckpt.get("rollout")
            # Chunks written after the checkpoint belong to steps that are redone
            for chunk_path in U.f_listdir(self.traj_dir, filter_ext=".pbz2", full_path=True):
                if self.traj_chunk_index(chunk_path) >= self.traj_chunks:
                    os.remove(chunk_path)
            # What the player has seen of this world so far
            knowledge.reset()
            if env_ckpt.get("knowledge") is not None:
                knowledge.load_state_dict(env_ckpt["knowledge"])
        else:
            knowledge.reset()
            if not self.inference_mode:
                # A new world: the trajectory of the old one does not continue
                U.f_remove(self.traj_dir)
            if args.resume and not self.inference_mode:
                print(
                    f"No saved world at {self.env_ckpt_path}, "
                    f"starting a new world", flush=True
                )
            self.rng = jax.random.PRNGKey(np.random.randint(2**31))
            self.rng, reset_rng = jax.random.split(self.rng)
            _, self.env_state = self.env.reset(
                reset_rng,
                self.env_params,
            )

        knowledge.observe(self.env_state)

        self.reward = 0.0
        self.done = False
        self.info = ""

        self.step_fn = jax.jit(self.env.step)

        # Steps since the last trajectory chunk. The resumed state is already
        # the last state of the last chunk.
        self.traj_history = {
            "state": [] if self.traj_chunks else [self.env_state],
            "action": [],
            "reward": [],
            "done": [],
        }

        self.curriculum_agent = CurriculumAgent(
            model_name=args.curriculum_model_name,
            temperature=args.curriculum_temperature,
            qa_model_name=args.qa_model_name,
            qa_temperature=args.qa_temperature,
            api_base=args.api_base,
            ckpt_dir=args.ckpt_dir,
            resume=args.resume,
            mode=args.curriculum_mode,
            use_qa=args.use_qa,
        )

        self.action_agent = ActionAgent(
            model_name=args.action_model_name,
            temperature=args.action_temperature,
            api_base=args.api_base,
        )

        self.critic_agent = CriticAgent(
            model_name=args.critic_model_name,
            temperature=args.critic_temperature,
            api_base=args.api_base,
            mode=args.critic_mode,
        )

        # As in Voyager, a separate skill library directory is loaded
        # read-only into the run (used for inference)
        self.skill_manager = SkillManager(
            model_name=args.skill_manager_model_name,
            temperature=args.skill_manager_temperature,
            api_base=args.api_base,
            ckpt_dir=args.skill_library_dir or args.ckpt_dir,
        )

        # Skills run in this module's namespace: every program the prompt names
        # has to be callable there
        missing = sorted((control_primitive_names() | {"UNKNOWN"}) - globals().keys())
        if missing:
            raise RuntimeError(
                f"Programs missing from the skill namespace: {', '.join(missing)}"
            )

        # Per skill execution: step budget, log buffer and the state before the
        # last step (the state the player died in, if the episode ends)
        self.skill_steps_taken = 0
        self.skill_step_budget = None
        self.skill_log = []
        self.pre_step_state = None

        self.log = ""
        self.clock = pygame.time.Clock()

    def skill_log_message(self, message):
        self.skill_log.append(str(message))
        self.log += f"\n{message}"
        print(message, flush=True)

    def step(self, action):
        if self.skill_step_budget is not None:
            if self.skill_steps_taken >= self.skill_step_budget:
                raise SkillStepBudgetExceeded(
                    f"The skill exceeded its budget of {self.skill_step_budget} "
                    f"environment steps. Do not write endless loops."
                )
            self.skill_steps_taken += 1

        self.rng, step_rng = jax.random.split(self.rng)
        old_achievements = self.env_state.achievements
        self.pre_step_state = self.env_state

        (
            self.obs,
            self.env_state,
            self.reward,
            self.done,
            self.info,
        ) = self.step_fn(
            step_rng,
            self.env_state,
            action,
            self.env_params,
        )

        if self.reward > 0.8:
            print(f"Reward: {self.reward}\n", flush=True)

        self.traj_history["state"].append(self.env_state)
        self.traj_history["action"].append(action)
        self.traj_history["reward"].append(self.reward)
        self.traj_history["done"].append(self.done)

        print_new_achievements(
            old_achievements,
            self.env_state.achievements,
        )

        self.clock.tick(self.args.fps)

        if self.done:
            # A new world: nothing of it has been seen yet
            knowledge.reset()
        knowledge.observe(self.env_state)

        if self.done:
            # The environment auto-resets, so the skill must not keep acting.
            # Learning continues in the new world, like Voyager's bot keeps
            # learning after it respawns.
            self.skill_log_message(
                "The episode ended, continuing in a new world."
            )
            raise EpisodeEnded(
                "The episode ended (the player died or the game is over). "
                "The game restarted in a new world with an empty inventory."
            )

        return self.env_state

    def execute_skill(self, skill):
        """
        Run a generated skill in the environment.

        Returns a dict with the state before execution, the execution error
        ("" if none), whether the player died (and the state it died in), the
        whole execution log, the primitives' events in it and the achievements
        unlocked during execution.
        """

        state_before = self.env_state
        # Rendered now: the report reads the player's memory, which the skill
        # is about to extend
        report_before = situation_report(state_before)
        achievements_before = np.asarray(self.env_state.achievements)
        self.pre_step_state = None
        died = False

        namespace = {
            name: value
            for name, value in globals().items()
            if not name.startswith("__")
        }

        self.skill_log = []
        self.skill_steps_taken = 0
        self.skill_step_budget = self.args.max_skill_steps

        error = ""

        # The step budget cannot stop a loop that never steps, so the skill
        # also gets a wall-clock limit
        timeout_message = (
            f"The skill exceeded its time limit of "
            f"{self.args.max_skill_seconds} seconds. "
            f"Do not write endless loops."
        )

        try:
            with time_limit(self.args.max_skill_seconds, timeout_message):
                # Learned skills first, so the new skill can call them
                exec(
                    compile(
                        self.skill_manager.programs,
                        "<skill_library>",
                        "exec",
                    ),
                    namespace,
                )

                exec(
                    compile(
                        skill["program_code"],
                        "<generated_skill>",
                        "exec",
                    ),
                    namespace,
                )

                skill_fn = namespace[skill["program_name"]]

                skill_fn(
                    self.env_state,
                    self.skill_log_message,
                    self.step,
                )
        except (Exception, SkillAborted) as e:
            error = f"{type(e).__name__}: {e}"
            died = isinstance(e, EpisodeEnded)
            print(f"\nGenerated skill failed: {error}", flush=True)
        finally:
            self.skill_step_budget = None

        achievements_after = np.asarray(self.env_state.achievements)
        new_achievements = [
            Achievement(i).name
            for i in range(len(achievements_after))
            if not achievements_before[i] and achievements_after[i]
        ]

        return {
            "state_before": state_before,
            "report_before": report_before,
            "error": error,
            "died": died,
            "death_state": self.pre_step_state if self.pre_step_state is not None else state_before,
            "log": "\n".join(self.skill_log),
            "events": primitive_events(self.skill_log),
            "new_achievements": new_achievements,
        }

    def rollout(self, task, context, resume=None):
        """
        Voyager's iterative prompting: generate a skill, execute it, let the
        critic judge it and feed code, error, log and critique back to the
        action agent until the task succeeds or the retries run out.

        resume is the rollout state of a checkpoint, to continue an
        interrupted rollout at its next attempt.

        If the player dies, the task fails without asking the critic and the
        rollout ends: retrying in a new, empty world makes no sense, the
        curriculum has to decide again.

        Returns the recap of the task for the curriculum: task, success,
        critique, attempts, died, vitals_before, vitals_after (plus the
        program on success).
        """

        resume = resume or {}
        code = resume.get("code", "")
        error = resume.get("error", "")
        log = resume.get("log", "")
        critique = resume.get("critique", "")
        # Checkpoints written before the recap existed have no vitals
        vitals_before = resume.get("vitals_before") or vitals(self.env_state)
        attempts = 0

        def checkpoint(next_attempt):
            self.save_checkpoint(rollout={
                "task": task,
                "context": context,
                "next_attempt": next_attempt,
                "code": code,
                "error": error,
                "log": log,
                "critique": critique,
                "vitals_before": vitals_before,
            })

        def recap(success, died=False, final_state=None, **program):
            return {
                "task": task,
                "success": success,
                "critique": critique,
                "attempts": attempts,
                "died": died,
                "vitals_before": vitals_before,
                "vitals_after": vitals(final_state if final_state is not None else self.env_state),
                **program,
            }

        for attempt in range(resume.get("next_attempt", 0), self.args.action_max_retries):
            # Every attempt counts as one iteration, including attempts whose
            # code could not be parsed (Voyager records those too)
            self.iteration += 1
            attempts = attempt + 1

            print(
                f"\n========== ITERATION {self.iteration}: ACTION AGENT "
                f"(attempt {attempt + 1}/{self.args.action_max_retries}) ==========", flush=True
            )

            skill = self.action_agent.generate_skill(
                task=task,
                context=context,
                situation=situation_report(self.env_state, include_achievements=False),
                skills=self.skill_manager.skill_code_list(),
                code=code,
                error=error,
                log=log,
                critique=critique,
            )

            if skill["generation_failed"]:
                # The iteration is used up, as in Voyager. The next one
                # sees the failed code and why it was rejected; log and
                # critique stay those of the last executed round.
                code = skill["program_code"]
                error = skill["error"]
                checkpoint(attempt + 1)
                continue

            print("\nGenerated skill:", flush=True)
            print(skill["description"], flush=True)
            print(skill["program_code"], flush=True)

            print("\n========== SKILL EXECUTION ==========", flush=True)

            execution = self.execute_skill(skill)

            if execution["died"]:
                critique = death_critique(execution["death_state"], execution["events"])

                print("\n========== PLAYER DIED ==========", flush=True)
                print("Success: False", flush=True)
                print(f"Critique: {critique}", flush=True)

                return recap(False, died=True, final_state=execution["death_state"])

            print("\n========== CRITIC AGENT ==========", flush=True)

            success, critique = self.critic_agent.check_task_success(
                task=task,
                report_before=execution["report_before"],
                report_after=situation_report(self.env_state),
                diff=state_diff(
                    execution["state_before"],
                    self.env_state,
                    execution["new_achievements"],
                ),
                events=execution["events"],
                error=execution["error"],
            )

            print(f"Success: {success}", flush=True)
            print(f"Critique: {critique}", flush=True)

            if success:
                return recap(
                    True,
                    program_name=skill["program_name"],
                    program_code=skill["program_code"],
                )

            code = skill["program_code"]
            error = execution["error"]
            log = execution["log"]
            checkpoint(attempt + 1)

        return recap(False)

    @staticmethod
    def traj_chunk_index(chunk_path):
        return int(Path(chunk_path).stem.split("_")[-1])

    def save_checkpoint(self, rollout=None):
        """
        Everything --resume needs besides the skill library and the curriculum
        (which save themselves): the world, the player's memory, the iteration
        count, the trajectory so far and the task in progress (None between
        tasks). Only while learning, inference never touches the checkpoint.
        """

        if self.inference_mode:
            return

        # Only the steps since the last checkpoint are written. Without
        # --save_trajectories they are never saved, so they are dropped.
        if self.args.save_trajectories and self.traj_history["state"]:
            U.f_mkdir(self.traj_dir)
            save_compressed_pickle(
                f"{self.traj_dir}/chunk_{self.traj_chunks:06d}",
                {**self.traj_history, "log": self.log},
            )
            self.traj_chunks += 1
        self.traj_history = {"state": [], "action": [], "reward": [], "done": []}
        self.log = ""

        U.f_mkdir(f"{self.args.ckpt_dir}/env")
        save_compressed_pickle(
            self.env_ckpt_path[: -len(".pbz2")],
            {
                "env_state": self.env_state,
                "rng": self.rng,
                "iteration": self.iteration,
                "knowledge": knowledge.state_dict(),
                "traj_chunks": self.traj_chunks,
                "rollout": rollout,
            },
        )

    def print_task_progress(self):
        print(
            "Completed tasks: "
            + ", ".join(self.curriculum_agent.completed_tasks), flush=True
        )
        print(
            "Failed tasks: "
            + ", ".join(self.curriculum_agent.failed_tasks), flush=True
        )

    def iteration_limit_reached(self, max_iterations):
        # Same check as Voyager: only between tasks, so a task in progress
        # finishes its attempts even if that passes the limit
        if max_iterations != -1 and self.iteration > max_iterations:
            print("Iteration limit reached", flush=True)
            return True
        return False

    def learn(self, max_iterations=-1):
        max_curriculum_failures = 10
        curriculum_failures = 0

        while not self.iteration_limit_reached(max_iterations):
            resume = self.pending_rollout
            self.pending_rollout = None

            if resume:
                # The run was interrupted during this task
                task, context = resume["task"], resume["context"]
                print(
                    f"\n========== RESUMING TASK at attempt "
                    f"{resume['next_attempt'] + 1}/{self.args.action_max_retries} "
                    f"(iteration {self.iteration}) ==========", flush=True
                )
            else:
                print(
                    f"\n========== CURRICULUM AGENT "
                    f"(iteration {self.iteration}) ==========", flush=True
                )

                try:
                    task, context = self.curriculum_agent.propose_next_task(
                        env_state=self.env_state,
                        skills=self.skill_manager.skill_summaries(),
                    )
                    curriculum_failures = 0
                except Exception as e:
                    # e.g. the LLM server timed out or the response never parsed.
                    # No action attempt happened, so the iteration count doesn't
                    # move; give up if the curriculum keeps failing.
                    curriculum_failures += 1
                    print(
                        f"Curriculum agent failed to propose a task "
                        f"({curriculum_failures}/{max_curriculum_failures}): "
                        f"{type(e).__name__}: {e}", flush=True
                    )
                    if curriculum_failures >= max_curriculum_failures:
                        raise
                    time.sleep(5)
                    continue

            print(f"Task: {task}", flush=True)
            print(f"Context: {context}", flush=True)

            try:
                info = self.rollout(task, context, resume=resume)
            except Exception as e:
                print(f"Rollout of task '{task}' terminated due to error: {type(e).__name__}: {e}", flush=True)
                info = {
                    "task": task,
                    "success": False,
                }

            if info["success"]:
                print("\n========== ADDING SKILL ==========", flush=True)
                self.skill_manager.add_new_skill(info)

            self.curriculum_agent.update_exploration_progress(info)
            self.save_checkpoint()

            self.print_task_progress()

        self.save_trajectories()

    def decompose_task(self, task):
        return self.curriculum_agent.decompose_task(
            task,
            env_state=self.env_state,
            skills=self.skill_manager.skill_summaries(),
        )

    def inference(self, task=None, sub_goals=None, max_iterations=-1):
        """
        Solve a given task with the learned skill library, like Voyager's
        inference: decompose the task into sub-goals and roll out each one in
        order in a fresh world. No new skills are added to the library.

        max_iterations limits the number of action agent attempts, since a
        sub-goal that keeps failing is retried. Inference stops after
        --max_sub_goal_failures failures in a row, since the later sub-goals
        build on the one that fails.

        If the player dies, the game restarts in a new world with an empty
        inventory: the task is decomposed again from there (given sub-goals
        start over).
        """

        if not task and not sub_goals:
            raise ValueError("Either task or sub_goals must be provided")

        # Inference plays a fresh world, nothing of it has been seen yet
        knowledge.reset()
        knowledge.observe(self.env_state)

        given_sub_goals = sub_goals
        sub_goals = given_sub_goals or self.decompose_task(task)

        print(f"Sub-goals: {sub_goals}", flush=True)

        self.curriculum_agent.completed_tasks = []
        self.curriculum_agent.failed_tasks = []

        # An index instead of Voyager's len(completed_tasks): completed tasks
        # are deduplicated, so a repeated sub-goal would never be passed
        sub_goal_index = 0
        failures = 0
        self.iteration = 0

        while sub_goal_index < len(sub_goals):
            if self.iteration_limit_reached(max_iterations):
                break

            next_task = sub_goals[sub_goal_index]

            print(
                f"\n========== SUB-GOAL {sub_goal_index + 1}/{len(sub_goals)}: "
                f"{next_task} ==========", flush=True
            )

            try:
                context = self.curriculum_agent.get_task_context(next_task)
                info = self.rollout(next_task, context)
            except Exception as e:
                print(f"Rollout of task '{next_task}' terminated due to error: {type(e).__name__}: {e}", flush=True)
                info = {
                    "task": next_task,
                    "success": False,
                }

            self.curriculum_agent.update_exploration_progress(info)

            if info["success"]:
                sub_goal_index += 1
                failures = 0
            else:
                failures += 1

            self.print_task_progress()

            if failures >= self.args.max_sub_goal_failures:
                print(
                    f"Sub-goal '{next_task}' failed {failures} times in a row, "
                    f"stopping inference", flush=True
                )
                break

            if info.get("died"):
                print("\n========== PLAYER DIED: PLANNING AGAIN ==========", flush=True)
                sub_goals = given_sub_goals or self.decompose_task(task)
                sub_goal_index = 0
                print(f"Sub-goals: {sub_goals}", flush=True)

        print(
            f"Inference finished: {sub_goal_index}/{len(sub_goals)} sub-goals completed", flush=True
        )

        self.save_trajectories()

    def save_trajectories(self):
        if self.args.save_trajectories:
            timestamp = int(time.time())
            save_name = f"play_data/trajectories_{timestamp}"

            if self.args.god_mode:
                save_name += "_GM"

            Path("play_data").mkdir(
                parents=True,
                exist_ok=True,
            )

            # The chunks of the checkpoint (the whole world so far, across
            # resumes) followed by the steps since the last checkpoint
            trajectory = {"state": [], "action": [], "reward": [], "done": []}
            log = ""
            for index in range(self.traj_chunks):
                chunk = load_compressed_pickle(f"{self.traj_dir}/chunk_{index:06d}.pbz2")
                for key in trajectory:
                    trajectory[key].extend(chunk[key])
                log += chunk["log"]
            for key in trajectory:
                trajectory[key].extend(self.traj_history[key])
            log += self.log

            save_compressed_pickle(
                save_name,
                trajectory,
            )

            with open(
                f"play_data/log_{timestamp}.txt",
                "w",
                encoding="utf-8",
            ) as f:
                f.write(log)


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--god_mode", action="store_true")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--save_trajectories", action="store_true")

    parser.add_argument(
        "--render_trajectory",
        type=str,
        default=None,
    )
    parser.add_argument(
        "--render_delay",
        type=float,
        default=0.05,
    )

    parser.add_argument("--fps", type=int, default=60)
    parser.add_argument("--max_iterations", type=int, default=-1)

    parser.add_argument(
        "--log_file",
        type=str,
        default=None,
        help="File the whole output is copied to while running "
        "(default: logs/run_<timestamp>.txt, 'none' to disable)",
    )

    parser.add_argument("--ckpt_dir", type=str, default="ckpt")
    parser.add_argument("--resume", action="store_true")

    # Inference: solve a given task with a learned skill library
    parser.add_argument(
        "--skill_library_dir",
        type=str,
        default=None,
        help="Checkpoint dir whose learned skills are loaded (e.g. for inference)",
    )
    parser.add_argument(
        "--inference_task",
        type=str,
        default=None,
        help="Decompose this task into sub-goals and solve them instead of learning",
    )
    parser.add_argument(
        "--sub_goals",
        type=json.loads,
        default=None,
        help='JSON list of sub-goals to solve instead of learning, e.g. \'["Mine 1 wood"]\'',
    )

    parser.add_argument(
        "--max_sub_goal_failures",
        type=int,
        default=3,
        help="Stop inference when a sub-goal fails this many times in a row",
    )

    parser.add_argument(
        "--action_max_retries",
        type=int,
        default=4,
    )
    parser.add_argument(
        "--max_skill_steps",
        type=int,
        default=1000,
    )
    parser.add_argument(
        "--max_skill_seconds",
        type=float,
        default=300,
    )

    parser.add_argument(
        "--curriculum_model_name",
        type=str,
        default="Qwen/Qwen3.5-4B",
    )
    parser.add_argument(
        "--curriculum_temperature",
        type=float,
        default=0.6,
    )
    parser.add_argument(
        "--curriculum_mode",
        type=str,
        choices=["auto", "manual"],
        default="auto",
    )

    parser.add_argument(
        "--qa_model_name",
        type=str,
        default="Qwen/Qwen3.5-4B",
    )
    parser.add_argument(
        "--qa_temperature",
        type=float,
        default=0.2,
    )
    parser.add_argument(
        "--use_qa",
        action="store_true",
        help="Let the curriculum ask and answer knowledge questions (off by default)",
    )

    parser.add_argument(
        "--action_model_name",
        type=str,
        default="Qwen/Qwen3.5-4B",
    )
    parser.add_argument(
        "--action_temperature",
        type=float,
        default=0.6,
    )

    parser.add_argument(
        "--critic_model_name",
        type=str,
        default="Qwen/Qwen3.5-4B",
    )
    parser.add_argument(
        "--critic_temperature",
        type=float,
        default=0.2,
    )
    parser.add_argument(
        "--critic_mode",
        type=str,
        choices=["auto", "manual"],
        default="auto",
    )

    parser.add_argument(
        "--skill_manager_model_name",
        type=str,
        default="Qwen/Qwen3.5-4B",
    )
    parser.add_argument(
        "--skill_manager_temperature",
        type=float,
        default=0.1,
    )

    parser.add_argument(
        "--api_base",
        type=str,
        default="http://localhost:8000/v1",
    )

    args, rest_args = parser.parse_known_args(sys.argv[1:])

    if rest_args:
        raise ValueError(f"Unknown args {rest_args}")

    return args


def main():
    # Redirected output defaults to the Windows codepage, where printing an LLM
    # response with characters like ✓ or → raises UnicodeEncodeError
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    args = parse_args()

    if args.render_trajectory:
        render_trajectory(
            args.render_trajectory,
            args.render_delay,
        )
        return

    if args.log_file != "none":
        tee_output(args.log_file or f"logs/run_{int(time.time())}.txt")

    def run():
        craftax_voyage = CraftaxVoyage(args)

        if craftax_voyage.inference_mode:
            craftax_voyage.inference(
                task=args.inference_task,
                sub_goals=args.sub_goals,
                max_iterations=args.max_iterations,
            )
        else:
            craftax_voyage.learn(args.max_iterations)

    if args.debug:
        with jax.disable_jit():
            run()
    else:
        run()


if __name__ == "__main__":
    main()
