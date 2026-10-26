import ast
from pathlib import Path

from utils import file_utils as U
from control_primitives.knowledge import (
    UNKNOWN,
    boss_vulnerable,
    is_visible,
    known_blocks,
    known_items,
    ladder_open,
    visible_mask,
    visible_mobs,
    visible_player_projectiles,
)
from control_primitives.explore_until import *
from control_primitives.kill_mob import *
from control_primitives.mine_block import *
from control_primitives.collect_sapling import *
from control_primitives.place import *
from control_primitives.craft import *
from control_primitives.enchant import *
from control_primitives.drink import *
from control_primitives.sleep import *
from control_primitives.descend_ladder import *
from control_primitives.ascend_ladder import *
from control_primitives.open_chest import *


def load_control_primitives(primitive_names=None):
    package_path = Path(__file__).resolve().parent

    if primitive_names is None:
        primitive_names = sorted(
            primitive.stem
            for primitive in package_path.iterdir()
            if primitive.suffix == ".py" and primitive.name != "__init__.py"
        )

    primitives = [
        U.load_text(package_path / f"{primitive_name}.py")
        for primitive_name in primitive_names
    ]

    return primitives


def control_primitive_names():
    """
    Names of every control primitive and knowledge function, i.e. every public
    top-level function of the primitive files (the names a skill must not reuse).
    """

    return {
        node.name
        for source in load_control_primitives()
        for node in ast.parse(source).body
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")
    }


def load_control_primitives_context(primitive_names=None):
    """
    Return the signature and docstring of every control primitive and of
    every knowledge function (control_primitives/knowledge.py).

    This is the prompt-sized counterpart of load_control_primitives():
    the LLM only needs to know how to call a primitive, not how it works.
    """

    contexts = []

    for source in load_control_primitives(primitive_names):
        for node in ast.parse(source).body:
            if not isinstance(node, ast.FunctionDef) or node.name.startswith("_"):
                continue

            signature = ast.unparse(node.args)
            docstring = ast.get_docstring(node) or ""
            docstring = "\n".join(
                f"    {line}" if line else ""
                for line in docstring.splitlines()
            )

            contexts.append(
                f"def {node.name}({signature}):\n"
                f'    """\n{docstring}\n    """'
            )

    return contexts