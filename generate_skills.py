from pathlib import Path
from openai import OpenAI
import re
import argparse


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
"""


def collect_craftax_source():
    parts = []

    extensions = {
        ".py",
        ".md",
        ".toml",
        ".txt",
        ".json",
        ".yaml",
        ".yml",
    }

    ignored_directories = {
        ".git",
        ".venv",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "build",
        "dist",
        "craftax_classic",
    }

    for path in sorted(CRAFTAX_ROOT.rglob("*")):
        if not path.is_file():
            continue

        if path.suffix.lower() not in extensions:
            continue

        if any(part in ignored_directories for part in path.parts):
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


def collect_voyager_skills():
    parts = []

    for path in sorted(VOYAGER_BASE_SKILLS_ROOT.rglob("*.js")):
        if not path.is_file():
            continue

        relative_path = path.relative_to(VOYAGER_BASE_SKILLS_ROOT)

        try:
            source = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            print(f"Skipping non-UTF8 file: {relative_path}")
            continue

        parts.append(
            f"""
    ===== VOYAGER FILE: {relative_path} =====

    {source}

    ===== END VOYAGER FILE: {relative_path} =====
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
        default=PROJECT_ROOT / "generated_skills",
    )
    args = parser.parse_args()

    global OUTPUT_DIR
    OUTPUT_DIR = Path(args.output_dir).expanduser().resolve()

    print("Collecting Craftax source...")
    craftax_source = collect_craftax_source()
    print(f"Craftax source size: {len(craftax_source):,} characters")

    print("Collecting Voyager Base Skills source...")
    voyager_base_skills_source = collect_voyager_skills()
    print(
        f"Voyager Base Skills source size: {len(voyager_base_skills_source):,} characters"
    )

    user_prompt = f"""
        Below is the Craftax source code.

        Analyze it carefully before designing the skills.

        <Craftax source>
        {craftax_source}
        </Craftax source>

        Below is the source code of Voyager base skills for minecraft.

        Analyze it carefully before designing the skills but only use them as inspiration.
        <Voyager source>
        {voyager_base_skills_source}
        </Voyager source>

        Now design the initial Craftax base skill set.

        For each skill choose an appropriate and descriptive but short Skill name,
        write a top-level comment to explain the skill, and liberally 
        add comments to explain various parts of the code.

        All skills must receive the env.step function and the current state. 
        Skills may but generally should not be single actions that can be done in a single craftax step.
        Instead they should execute multi-step conditional actions either until the task has failed 
        or a maximum number of steps has been reached. Do not create infinite loops or recursive functions. 
        Do not use invalid actions. Do not invent objects or mobs not defined by craftax. Use enums and constants provided by craftax.
        Do not blindly spam one action, but rather write smart conditionals based on the current state. Do not directly edit the state.
        
        Make sure to make use of every necessary piece of information provided in the env state and choose actions adequately
        in order to succeed a skill's goal. For example a skill to mine a block should contain conditionals whether there even is one in sight, 
        how to move towards it, mine other blocks in the way, clear water, fail the skill if enemies get close etc. etc. Be smart
        and make generally applicable but very basic skills.

        Furthermore, make it very clear, whether the skill has failed by throwing an error with an appropriate explanation.
        Also make it very clear if the skill has succeeded by returning true. Do not return false. 

        For every generated skill/file, use exactly this format:

        === FILE: craftax_skills/<filename>.py ===
        <complete Python source code>

        For example:

        === FILE: craftax_skills/mine_block.py ===
        # Description:
        # Moves to and Mines a specified block...

        def mine_block(...):
            ...

        === FILE: craftax_skills/explore.py ===
        # Description:
        # Explores the environment...

        def explore(...):
            ...

        Every file must be complete and directly saveable as a .py file.
        Comments/docstrings may explain the implementation, but do not output
        prose outside the Python files. Every file must contain functioning code + appropriate and accurate comments. 
        Do not create python files that are comment only.
    """

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
