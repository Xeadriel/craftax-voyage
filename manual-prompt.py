from pathlib import Path
from openai import OpenAI
import argparse


PROJECT_ROOT = Path.home() / "craftax-voyage"
CRAFTAX_ROOT = PROJECT_ROOT / "Craftax-1.6.1"

MODEL = "Qwen/Qwen3.5-4B"
BASE_URL = "http://localhost:8000/v1"


def collect_craftax_source():
    parts = []

    source_path = CRAFTAX_ROOT / "craftax"

    if not source_path.exists():
        raise FileNotFoundError(
            f"Craftax source directory not found: {source_path}"
        )

    for path in sorted(source_path.rglob("*.py")):
        if not path.is_file():
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

    if not parts:
        raise RuntimeError(
            f"No Python files found in: {source_path}"
        )

    return "\n".join(parts)


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Send a prompt with the complete Craftax Python source "
            "to the local vLLM server."
        )
    )

    parser.add_argument(
        "prompt",
        type=str,
        help="The prompt to send to the LLM.",
    )

    args = parser.parse_args()

    print("Collecting Craftax source...")

    craftax_source = collect_craftax_source()

    print(
        f"Collected Craftax source: "
        f"{len(craftax_source):,} characters"
    )

    full_prompt = f"""
    You are a Python Programming Expert.

    Below is the complete Python source code from the Craftax video game
    and RL environment. Read it carefully and answer the User's prompt
    truthfully.

    Do not make up information and only answer based on what you can see
    in the code.

    <Craftax source>
    {craftax_source}
    </Craftax source>

    <User prompt>
    {args.prompt}
    </User prompt>
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
                "role": "user",
                "content": full_prompt,
            },
        ],
        temperature=0.2,
    )

    print(response.choices[0].message.content)


if __name__ == "__main__":
    main()