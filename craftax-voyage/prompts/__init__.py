from pathlib import Path

from utils import file_utils as U


def load_prompt(prompt_name):
    package_path = Path(__file__).resolve().parent
    prompt_path = package_path / f"{prompt_name}.txt"
    return U.load_text(prompt_path)