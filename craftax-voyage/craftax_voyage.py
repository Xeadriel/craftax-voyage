from __future__ import annotations

import argparse
import bz2
import pickle
import sys
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
    MobType
)
from craftax.craftax.envs.craftax_symbolic_env import CraftaxSymbolicEnv as CraftaxEnv
from craftax.craftax.renderer import make_craftax_pixel_renderer
from craftax.craftax_env import make_craftax_env_from_name
from craftax.craftax.renderer import render_craftax_text

from agents.curriculum import CurriculumAgent
from agents.action import ActionAgent
from agents.critic import CriticAgent
from agents.skill import SkillManager
from control_primitives import *

import utils as U


def save_compressed_pickle(title: str, data: Any):
    with bz2.BZ2File(title + ".pbz2", "w") as f:
        pickle.dump(data, f)


def load_compressed_pickle(path: str):
    with bz2.BZ2File(path, "r") as f:
        return pickle.load(f)


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
                f"({new_achievements.sum()}/{len(Achievement)})"
            )


def render_trajectory(path: str, delay: float):
    trajectory = load_compressed_pickle(path)
    states = trajectory["state"]

    print(f"Loaded trajectory: {path}")
    print(f"States: {len(states)}")
    print(f"Delay: {delay}s")

    renderer = CraftaxRenderer()

    for i, state in enumerate(states):
        renderer.render(state)
        renderer.update()

        if renderer.is_quit_requested():
            break

        print(f"\rRendering state {i + 1}/{len(states)}", end="", flush=True)

        if i < len(states) - 1:
            time.sleep(delay)

    print()

    while not renderer.is_quit_requested():
        renderer.update()
        time.sleep(0.01)

    pygame.quit()


class CraftaxVoyage:
    def __init__(self, args):
        self.args = args

        self.env = make_craftax_env_from_name(
            "Craftax-Symbolic-v1",
            auto_reset=True,
        )
        self.env_params = self.env.default_params

        self.rng = jax.random.PRNGKey(np.random.randint(2**31))
        self.rng, reset_rng = jax.random.split(self.rng)
        self.obs, self.env_state = self.env.reset(
            reset_rng,
            self.env_params,
        )

        self.reward = 0.0
        self.done = False
        self.info = ""

        self.step_fn = jax.jit(self.env.step)

        self.traj_history = {
            "state": [self.env_state],
            "action": [],
            "reward": [],
            "done": [],
        }

        self.curriculum_agent = CurriculumAgent(
            model_name=args.curriculum_model_name,
            temperature=args.curriculum_temperature,
            api_base=args.api_base,
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
        )

        self.skill_manager = SkillManager(
            model_name=args.skill_manager_model_name,
            temperature=args.skill_manager_temperature,
            api_base=args.api_base,
        )

        self.current_task = None
        self.current_context = ""
        self.current_skill = None
        self.current_critique = None

        self.log = ""
        self.clock = pygame.time.Clock()

    def log_message(self, message):
        self.log += f"\n{message}"
        print(message)

    def step(self, action):
        self.rng, step_rng = jax.random.split(self.rng)
        old_achievements = self.env_state.achievements
        
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
            print(f"Reward: {self.reward}\n")

        self.traj_history["state"].append(self.env_state)
        self.traj_history["action"].append(action)
        self.traj_history["reward"].append(self.reward)
        self.traj_history["done"].append(self.done)

        # self.log_message(render_craftax_text(self.env_state))

        print_new_achievements(
            old_achievements,
            self.env_state.achievements,
        )

        self.clock.tick(self.args.fps)

        return self.env_state

    def pass_through_ai_agents(self):
        self.env_state = self.env_state.replace(
            inventory=self.env_state.inventory.replace(
                pickaxe=jnp.asarray(4, dtype=self.env_state.inventory.pickaxe.dtype)
            )
        )
        try:
            explore_until(self.env_state, self.log_message, self.step, BlockType.COAL, max_steps=200)
        except Exception as e:
            self.log_message(f"Error: {e}")
        
        try:
            mine_block(self.env_state, self.log_message, self.step, BlockType.COAL, 5, max_steps=200)
        except Exception as e:
            self.log_message(f"Error: {e}")
            
        # explore_until_target_found(self.env_state, self.log_message, self.step, BlockType.STONE, max_steps=10)
        # print("\n========== CURRICULUM AGENT ==========")

        # textual_state = render_craftax_text(self.env_state)

        # self.current_task, self.current_context = (
        #     self.curriculum_agent.propose_next_task(
        #         env_state=self.env_state,
        #         textual_state=textual_state,
        #     )
        # )

        # print(f"Task: {self.current_task}", flush=True)
        # print(f"Context: {self.current_context}")

        # print("\n========== SKILL MANAGER ==========")

        # skills = self.skill_manager.retrieve_skills(
        #     query=self.current_task,
        # )

        # print("\n========== ACTION AGENT ==========")

        # self.current_skill = self.action_agent.generate_skill(
        #     task=self.current_task,
        #     context=self.current_context,
        #     textual_state=textual_state,
        #     skills=skills,
        #     critique=self.current_critique
        # )

        # print("\nGenerated skill:")
        # print(self.current_skill["description"])
        # print(self.current_skill["program_code"])

        # print("\n========== SKILL EXECUTION ==========")

        # errorMessage = self.execute_skill(self.current_skill)

        # print("\n========== CRITIC AGENT ==========")

        # textual_state_after = render_craftax_text(self.env_state)
        # print(textual_state_after)

        # success, critique = self.critic_agent.check_task_success(
        #     task=self.current_task,
        #     context=self.current_context,
        #     textual_state=textual_state_after,
        #     errorMessage=errorMessage
        # )

        # self.current_critique = critique

        # print(f"Success: {success}")
        # print(f"Critique: {critique}")

        # self.curriculum_agent.update_exploration_progress(
        #     {
        #         "task": self.current_task,
        #         "success": success,
        #     }
        # )

        # if success:
        #     print("\n========== ADDING SKILL ==========")
        #     self.skill_manager.add_new_skill(
        #         skill=self.current_skill
        #     )

        # return success

    def execute_skill(self, skill):
        namespace = {"Action": Action}
        namespace.update({
            name: value
            for name, value in globals().items()
            if not name.startswith("__")
        })

        try:
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
                self.step,
                self.log_message,
            )
        except Exception as e:
            error = f"{type(e).__name__}: {e}"
            print(f"\nGenerated skill failed: {error}")
            return error

        return "None"

    def game_loop(self, max_turns=-1):
        turn_count = 0

        while max_turns == -1 or turn_count < max_turns:
            turn_count += 1

            print(f"\n========== TURN {turn_count} ==========")

            self.pass_through_ai_agents()

            if self.done:
                print("Environment finished.")
                break

        if self.args.save_trajectories:
            timestamp = int(time.time())
            save_name = f"play_data/trajectories_{timestamp}"

            if self.args.god_mode:
                save_name += "_GM"

            Path("play_data").mkdir(
                parents=True,
                exist_ok=True,
            )

            save_compressed_pickle(
                save_name,
                self.traj_history,
            )

            with open(
                f"play_data/log_{timestamp}.txt",
                "w",
                encoding="utf-8",
            ) as f:
                f.write(self.log)


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
    parser.add_argument("--max_turns", type=int, default=-1)

    parser.add_argument(
        "--curriculum_model_name",
        type=str,
        default="Qwen/Qwen3.5-4B",
    )
    parser.add_argument(
        "--curriculum_temperature",
        type=float,
        default=0.0,
    )

    parser.add_argument(
        "--action_model_name",
        type=str,
        default="Qwen/Qwen3.5-4B",
    )
    parser.add_argument(
        "--action_temperature",
        type=float,
        default=0.0,
    )

    parser.add_argument(
        "--critic_model_name",
        type=str,
        default="Qwen/Qwen3.5-4B",
    )
    parser.add_argument(
        "--critic_temperature",
        type=float,
        default=0.0,
    )

    parser.add_argument(
        "--skill_manager_model_name",
        type=str,
        default="Qwen/Qwen3.5-4B",
    )
    parser.add_argument(
        "--skill_manager_temperature",
        type=float,
        default=0.0,
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
    args = parse_args()

    if args.render_trajectory:
        render_trajectory(
            args.render_trajectory,
            args.render_delay,
        )
        return

    if args.debug:
        with jax.disable_jit():
            craftax_voyage = CraftaxVoyage(args)
            craftax_voyage.game_loop(args.max_turns)
    else:
        craftax_voyage = CraftaxVoyage(args)
        craftax_voyage.game_loop(args.max_turns)


if __name__ == "__main__":
    main()