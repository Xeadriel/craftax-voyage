"""
Static checks on a generated skill, run before it touches the game. They only
catch API mistakes (wrong calls, unknown enum members, reused primitive names,
log lines posing as primitive reports); they never judge the task itself.
"""

import ast

from craftax.craftax.constants import Achievement, Action, BlockType, ItemType, MobType

ENUMS = {
    "Achievement": Achievement,
    "Action": Action,
    "BlockType": BlockType,
    "ItemType": ItemType,
    "MobType": MobType,
}


def check_skill_code(code, program_name, reserved_names):
    """
    Args:
        code: Source of the generated skill
        program_name: Name of its main function
        reserved_names: Names of the control primitives and knowledge functions

    Returns:
        List of error messages, empty if the code passed every check
    """
    errors = []
    tree = ast.parse(code)

    if program_name in reserved_names:
        errors.append(
            f"The skill is named `{program_name}`, which is the name of a program in the list. "
            f"Give it a different name."
        )

    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store) and node.id in reserved_names:
            errors.append(
                f"`{node.id}` is assigned inside the skill, which hides the program of that name. "
                f"Use a different variable name."
            )

        elif (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name != program_name
            and node.name in reserved_names
        ):
            errors.append(f"A helper function is named `{node.name}`, which hides the program of that name.")

        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id == "step_func" and len(node.args) + len(node.keywords) != 1:
                errors.append(
                    "`step_func` takes exactly one argument, the action id, e.g. "
                    "`state = step_func(Action.DO.value)`."
                )
            if node.func.id == "log_fn" and node.args and _starts_with_bracket(node.args[0]):
                errors.append(
                    "Log lines starting with `[` are reserved for the programs. Do not start a log line with `[`."
                )

        elif (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id in ENUMS
            and not node.attr.startswith("_")
            and node.attr not in ENUMS[node.value.id].__members__
        ):
            errors.append(f"`{node.value.id}.{node.attr}` does not exist.")

    # One message per mistake, in the order found
    return list(dict.fromkeys(errors))


def _starts_with_bracket(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value.startswith("[")
    if isinstance(node, ast.JoinedStr) and node.values:
        first = node.values[0]
        return isinstance(first, ast.Constant) and isinstance(first.value, str) and first.value.startswith("[")
    return False
