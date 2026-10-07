from pathlib import Path

from utils import file_utils as U
from control_primitives.explore_until import *
from control_primitives.kill_mob import *
from control_primitives.mine_block import *
from control_primitives.collect_sapling import *
from control_primitives.place import *
from control_primitives.craft import *
from control_primitives.enchant import *
from control_primitives.drink import *
from control_primitives.sleep import *


def load_control_primitives(primitive_names=None):
    package_path = Path(__file__).resolve().parent

    if primitive_names is None:
        primitive_names = [
            primitive.stem
            for primitive in package_path.iterdir()
            if primitive.suffix == ".py" and primitive.name != "__init__.py"
        ]

    primitives = [
        U.load_text(package_path / f"{primitive_name}.py")
        for primitive_name in primitive_names
    ]

    return primitives