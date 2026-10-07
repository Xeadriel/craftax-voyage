from pathlib import Path
from openai import OpenAI
import re
import argparse
import time


PROJECT_ROOT = Path.home() / "craftax-voyage"
CRAFTAX_ROOT = PROJECT_ROOT / "craftax-voyage"
VOYAGER_CONTROL_PRIMITIVES_ROOT = PROJECT_ROOT / "Voyager-main" / "voyager" / "control_primitives"

MODEL = "Qwen/Qwen3.5-4B"
BASE_URL = "http://localhost:8000/v1"

OUTPUT_DIR = PROJECT_ROOT / "generated_control_primitives" / str(int(time.time()))


SYSTEM_PROMPT = """
You are an expert software engineer.

Your task is to design a set of reusable low-level control primitives
for the Craftax environment.

You are given the part of the Craftax source code.

Carefully examine the given code and make use of the game state's content while writing the control primitives.

Your control primitive functions will be reused for building more complex functions. Therefore, you should make it generic and reusable. 
You should not make strong assumption about the game state (as it may be changed at a later time),
and therefore you should always check whether you have the required items before using them. 

A control primitive must fail if you do not have its prerequisites. You may also define custom situations like for example being 
interrupted mining or exploring by an enemy getting too close. Always provide an explanation when failing and throwing errors.
Also make it very clear if the control primitive has succeeded by returning true. Never return false or anything else.
Sleeping and resting cannot be interrupted and therefore must run
step functions until a sufficient number of steps has been taken and the game logic concludes the sleep/rest.

For each control primitive choose an appropriate and descriptive but short control primitive name, write a top-level comment to describe what the control primitive does.
control primitives may but generally should not be single actions that can be done in a single craftax step. Instead they should execute multi-step conditional actions either until the task has failed 
or a maximum number of steps has been reached. 
Do not create infinite loops or recursive functions. 
Do not use invalid actions. Do not invent objects or mobs not defined by craftax. Use enums and constants provided by craftax.
Do not blindly spam one action, but rather write smart conditionals based on the current state. Do not directly edit the state. 
Always consider the character's current direction because it matters for many actions.
Every control primitive must at least take the game state as a parameter as you will heavily make use of it in the code.
Every control primitive must also take a step function which takes one argument, which is a value from the action enum. 
Furthermore every control primitive must take a log function for logging purposes.
Use this log function to log what you make the player character do.
You may not actively change the game state via any other function other than via the step function.
The step function returns a new state that you can use.
Every action you take in a control primitive must be taken via the step function. 
Do not write helper functions and keep everything inside one minimal function.
Your reply should contain the python code for exactly ONE control primitive.

As a reminder, this is the action enum:

class Action(Enum):
    NOOP = 0  #
    LEFT = 1  # a
    RIGHT = 2  # d
    UP = 3  # w
    DOWN = 4  # s
    DO = 5  # space
    SLEEP = 6  # tab
    PLACE_STONE = 7  # r
    PLACE_TABLE = 8  # t
    PLACE_FURNACE = 9  # f
    PLACE_PLANT = 10  # p
    MAKE_WOOD_PICKAXE = 11  # 1
    MAKE_STONE_PICKAXE = 12  # 2
    MAKE_IRON_PICKAXE = 13  # 3
    MAKE_WOOD_SWORD = 14  # 5
    MAKE_STONE_SWORD = 15  # 6
    MAKE_IRON_SWORD = 16  # 7
    REST = 17  # e
    DESCEND = 18  # >
    ASCEND = 19  # <
    MAKE_DIAMOND_PICKAXE = 20  # 4
    MAKE_DIAMOND_SWORD = 21  # 8
    MAKE_IRON_ARMOUR = 22  # y
    MAKE_DIAMOND_ARMOUR = 23  # u
    SHOOT_ARROW = 24  # i
    MAKE_ARROW = 25  # o
    CAST_FIREBALL = 26  # g
    CAST_ICEBALL = 27  # h
    PLACE_TORCH = 28  # j
    DRINK_POTION_RED = 29  # z
    DRINK_POTION_GREEN = 30  # x
    DRINK_POTION_BLUE = 31  # c
    DRINK_POTION_PINK = 32  # v
    DRINK_POTION_CYAN = 33  # b
    DRINK_POTION_YELLOW = 34  # n
    READ_BOOK = 35  # m
    ENCHANT_SWORD = 36  # k
    ENCHANT_ARMOUR = 37  # l
    MAKE_TORCH = 38  # [
    LEVEL_UP_DEXTERITY = 39  # ]
    LEVEL_UP_STRENGTH = 40  # -
    LEVEL_UP_INTELLIGENCE = 41  # =
    ENCHANT_BOW = 42  # ;

    For every generated control primitive/file, use exactly this format:

    === FILE: <filename>.py ===
    <complete Python source code>

    For example:

    === FILE: mine_block.py ===
    # Description:
    # Moves, clears path to and Mines a specified block...

    def mine_block(state, log, step_func, ...):
        ...

    === FILE: explore.py ===
    # Description:
    # Explores the environment until...

    def exploreUntil(state, log, step_func, ...):
        ...

    Every file must be complete and directly saveable as a .py file.
    Comments/docstrings may explain the implementation, but do not output
    prose outside the Python files. Every file must contain functioning code + appropriate and accurate comments. 
    Do not create python files that are comment only.
=======


PROJECT_ROOT = Path.home() / "craftax-voyage"
CRAFTAX_ROOT = PROJECT_ROOT / "Craftax-1.6.1"
VOYAGER_BASE_SKILLS_ROOT = (
    PROJECT_ROOT / "Voyager-main" / "voyager" / "control_primitives"
)

MODEL = "unsloth/Qwen3.5-9B-GGUF"
BASE_URL = "http://localhost:8000/v1"

OUTPUT_DIR = PROJECT_ROOT / "generated_skills"


SYSTEM_PROMPT = r"""
You are an expert software engineer.

Your task is to design a set of reusable low-level control primitives ("base
skills") for the Craftax environment.

You are given the complete Craftax source code and some example skills
from voyager which did the same for minecraft.

Treat the Craftax source code as the authoritative
specification of the environment and its APIs. 
The Voyager code is only an example of how reusable control primitives can be
structured. Do not assume Minecraft APIs exist in Craftax.

The goal is NOT to copy Minecraft/Voyager functionality mechanically.

Instead, infer what useful reusable control primitives should exist for
Craftax based on:
- the actual Craftax state representation,
- the actual Craftax action space,
- the actual Craftax environment API,
- Craftax's items, blocks, resources, entities, crafting and progression
  mechanics,
- and the way the environment is actually implemented.

Important requirements:

1. Only use APIs and concepts that actually exist in Craftax.
2. Do not assume Craftax has Minecraft's bot APIs, Mineflayer, pathfinder,
   Vec3, chests, Minecraft commands, etc.
3. Skills must be implemented in Python. You may create helper functions but try to avoid them.
4. Prefer small, composable skills with clear purposes.
5. A skill should perform a clear short-term objective rather than attempting
   to solve an entire long-horizon objective.
6. Reuse existing Craftax functions and abstractions whenever appropriate.
7. Do not invent APIs merely because they would be convenient.
8. Explain the assumptions behind each proposed skill as code comments ONLY.
9. Produce actual Python implementations for the skills that can be
    implemented reliably from the supplied source code.
10. Do not reply with anything other than commented code.
11. Definitely use the constants given in craftax.craftax.constants whenever applicable.

Before writing the final skills, inspect the Craftax source carefully and
derive the relevant environment interfaces.
>>>>>>> 90f000267c4b3500e6f409a54007a4e2fc6e4fcc
"""


def collect_craftax_source():
    parts = []

    files_to_include = {
        "craftax_symbolic_env.py",
        "game_logic_utils.py",
        "math_utils.py",
        "constants.py",
        "craftax_state.py",
        "game_logic.py",
        "tutorial.md",
        "obs_description.md",
    }

    for path in sorted(CRAFTAX_ROOT.rglob("*")):
        if not path.is_file():
            continue

        if path.name not in files_to_include:
            continue

        relative_path = path.relative_to(CRAFTAX_ROOT)

        try:
            source = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            print(f"Skipping non-UTF8 file: {relative_path}")
            continue

        parts.append(
            f"""
        ===== FILE: {relative_path} =====

        {source}

        ===== END FILE: {relative_path} =====
        """
        )

    return "\n".join(parts)

def save_generated_files(result):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    pattern = r"=== FILE: (.+?) ===\n(.*?)(?=\n=== FILE: |\Z)"
    matches = re.findall(pattern, result, re.DOTALL)

    if not matches:
        raise RuntimeError(
            "No generated files found. Expected output in the format:\n"
            "=== FILE: filename.py ===\n"
            "# code..."
        )

    for filename, content in matches:
        filename = filename.strip()

        # Prevent the model from writing outside OUTPUT_DIR.
        output_file = (OUTPUT_DIR / filename).resolve()
        output_root = OUTPUT_DIR.resolve()

        if output_root not in output_file.parents:
            raise RuntimeError(
                f"Refusing to write outside output directory: {filename}"
            )

        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(content.strip() + "\n", encoding="utf-8")

        print(f"Generated: {output_file}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "output_dir",
        nargs="?",
        default=PROJECT_ROOT / "generated_control primitives",
    )
    args = parser.parse_args()

    global OUTPUT_DIR
    OUTPUT_DIR = Path(args.output_dir).expanduser().resolve()

    print("Collecting Craftax source...")
    craftax_source = collect_craftax_source()
    print(f"Craftax source size: {len(craftax_source):,} characters")


    user_prompt = f"""
        Below is the Craftax source code.

        Read it carefully before designing the control primitives.

        <Craftax source>
        {craftax_source}
        </Craftax source>
        
    
    Now design the following control primitive:
    A control primitive to explore and walk around until a certain specified thing is found or X number of steps are reached. This can be a block or entity.  
        It should return true at the end if no error was thrown.
        It should throw an error if max_steps number of steps are reached before finding the specified object.
    """
        # It should throw an error if food, drink or energy fall to 3 or below.

    # - A control primitive to sleep or rest.
    #         It should move to a place of safety.
    #         If possible it should try to close the entrance to that safe spot by placing a block.
    #         Lastly it should enter the sleep or rest state as specified and run steps until the state is concluded.
    #         It should throw an error if the character has less hp than before sleeping/resting.
    #         It should return true at the end if no error was thrown.
    #         It should throw an error if the character died.

    # - A control primitive to drink water.
    #         It should move to the closest water source and drink it until maximum capacity.
    #         It should be able to clear blocks and lave (by placing and removing a block where the lava is) that are in the way.
    #         It should throw an error if if there is no water source nearby.
    #         It should throw an error if an enemy gets too close (1 blocks radius).
    #         It should return true at the end if no error was thrown.
    #         It should throw an error after X (default 20) steps if not succeeded.
    #         It should throw an error if the character died.
    # - A control primitive to mine a specified number X (default value 1) of specified blocks/trees/resources. 
    #         It should move to the nearest block of the given type and mine it and do this X times.
    #         It should be able to clear blocks (by mining it) or water/lava (by placing and removing a block where the water/lava is) that are in the way. 
    #         It should return true at the end if no error was thrown.
    #         It should throw an error if X has not been reached yet but no more blocks of that type exist.
    #         It should throw an error if hunger, thirst or energy fall to 3 or below.
    #         It should throw an error if hp falls to 5 or below.
    #         It should throw an error if an enemy gets too close (3 blocks radius).
    #         It should throw an error after X (default 50) steps if not succeeded.
    #         It should throw an error if the character died.
    
        
      
    #     - 3 A control primitive to fight an enemy type or passive mob via melee attacks.
    #         It should decide when to use a melee attack, when to move in, when to retreat, 
    #         when to bait, when to reposition in order to adjust the player character's direction and when to dodge enemy projectiles
    #         It should also attempt to bait the enemy to enter the location the player character is currently facing by making use of the NOOP action when applicable. 
    #         It should return true at the end if the enemy has been defeated.
    #         It should throw an error if hunger, thirst, hp or energy fall to 3 or below.
    #         It should throw an error after X (default 20) steps if not succeeded.
    #         It should throw an error if the character died.
    #     - 4 A control primitive to fight a given enemy type via ranged attacks.
    #         It should check the game state for which ranged attacks are available, i.e. check for arrows, whether and which spells are learned, check if the character has enough mana etc. when applicable.
    #         It should consider resistances and damage vectors (damage types) and choose the best attack for the job. 
    #         It should decide which ranged attack to use, when to use a chosen ranged attack, when and how to move, when to retreat, 
    #         when to bait, when to reposition in order to adjust the player character's direction and when to dodge enemy projectiles.
    #         It should also attempt to bait the enemy to enter the location the player character is currently facing by making use of the NOOP action when applicable. 
    #         It should throw an error if hunger, thirst, hp or energy fall to 3 or below.
    #         It should return true at the end if the enemy was defeated.
    #         It should throw an error after X (default 20) steps if not succeeded.
    #         It should throw an error if the character died.
    #     - 5 A control primitive to flee to relative safety. 
    #         It should try to avoid enemies, dodge projectiles and try to build as much distance as possible. 
    #         It should succeed when a distance of 5 or more to the closest enemy has been established or there are no enemies in sight.
    #         It should be able to ascend and descend ladders.
    #         It should be able to mine blocks and remove water (by placing and removing where the water is) that are in the way.
    #         It should return true at the end if no error was thrown.
    #         It should throw an error after X (default 20) steps if not succeeded.
    #         It should throw an error if the character died.
    #     - 7 A control primitive to sleep or rest.
    #         It should move to a place of safety.
    #         If possible it should try to close the entrance to that safe spot by placing a block.
    #         Lastly it should enter the sleep or rest state as specified and run steps until the state is concluded.
    #         It should throw an error if the character has less hp than before sleeping/resting.
    #         It should return true at the end if no error was thrown.
    #         It should throw an error if the character died.
    #     - 8 A control primitive to craft an item.
    #         It should check for the items ingredient requirements.
    #         It should move to the necessary crafting station (crafting table, furnace, enchantment table etc.) if available or build one if not and if possible (enchantment tables cannot be built).
    #         It should craft the item.
    #         It should throw an error if there are not enough items in the inventory.
    #         It should throw an error if the necessary crafting station is not available and cannot be built (either because it's not possible or because there is not enough material for the crafting table/furnace).
    #         It should return true at the end if no error was thrown.
    #         It should throw an error after X (default 15) steps if not succeeded.
    #         It should throw an error if the character died.
    #     - 9 A control primitive to level up a given attribute.
    #         It should level up the specified attribute.
    #         It should throw an error if there are no XP points available.
    #         It should throw an error if the character died.
    #     -10 A control primitive to read a book.
    #         It should read the specified book.
    #         It should throw an error if there are no books in the inventory.
    #         It should throw an error if the character died.
    #     -11 A control primitive to drink a potion.
    #         It should drink the specified potion.
    #         It should throw an error if there are no potions of the given type in the inventory.
    #         It should throw an error if the character died.
    #     -12 A control primitive to place a block or plant.
    #         It should move to the given location in a way the character ends up facing it and place the block or plant.
    #         It should throw an error if the placement is not possible or moving to the spot in a way that makes placing possible is not possible.
    #         It should throw an error after X (default 15) steps if not succeeded.
    #         It should throw an error if the character died.
    # """

    client = OpenAI(
        base_url=BASE_URL,
        api_key="EMPTY",
    )

    print("Sending request to vLLM...")

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        temperature=0.2,
        max_tokens=16000,
    )

    result = response.choices[0].message.content

    save_generated_files(result)


if __name__ == "__main__":
    main()