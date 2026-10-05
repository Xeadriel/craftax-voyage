from pathlib import Path

from utils import file_utils as U
from control_primitives.mine_blocks import *
from control_primitives.explore_until_target_found import *
from control_primitives.drink_water import *
from control_primitives.sleep_or_rest import *


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