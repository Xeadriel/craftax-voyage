# Skill: make_pickaxe
# Purpose: Crafts a pickaxe of specified level
# Required inputs: pickaxe_level (int), max_steps (int)
# Preconditions: Player must be at a crafting table, have required materials
# Expected effects: Pickaxe is crafted and added to inventory, materials consumed
# Failure conditions: No crafting table, insufficient materials, invalid level
# Explanation: Uses state.map for crafting table detection, state.inventory for materials,
#             Action.MAKE_* for crafting interaction

import jax
from craftax.craftax.constants import BlockType, Action
from craftax.craftax.craftax_state import EnvState
from craftax.craftax.util.game_logic_utils import is_near_block


def make_pickaxe(state: EnvState, pickaxe_level: int, max_steps: int = 100) -> bool:
    """
    Crafts a pickaxe of specified level.

    Returns True if pickaxe was crafted, False otherwise.
    """
    # Define pickaxe crafting recipes
    pickaxe_recipes = {
        1: {"wood": 1, "pickaxe": 0},
        2: {"wood": 1, "stone": 1, "pickaxe": 1},
        3: {"wood": 1, "stone": 1, "iron": 1, "coal": 1, "pickaxe": 2},
        4: {"wood": 1, "diamond": 3, "pickaxe": 3},
    }

    recipe = pickaxe_recipes.get(pickaxe_level)
    if not recipe:
        return False

    # Check if we have required materials
    for material, amount in recipe.items():
        if amount > 0:
            current_amount = getattr(state.inventory, material)
            if current_amount < amount:
                return False

    # Find a crafting table
    if not is_near_block(state, BlockType.CRAFTING_TABLE.value):
        return False

    # Check if we're at a crafting table
    if not is_near_block(state, BlockType.CRAFTING_TABLE.value):
        return False

    # Craft the pickaxe by pressing the appropriate key
    craft_keys = {
        1: Action.MAKE_WOOD_PICKAXE.value,
        2: Action.MAKE_STONE_PICKAXE.value,
        3: Action.MAKE_IRON_PICKAXE.value,
        4: Action.MAKE_DIAMOND_PICKAXE.value,
    }

    craft_key = craft_keys.get(pickaxe_level)
    if not craft_key:
        return False

    # Craft the pickaxe
    for step in range(max_steps):
        key = jax.random.PRNGKey(0)

        # Move to crafting table
        direction = 0
        if state.player_position[1] > state.player_position[1]:
            direction = 1
        elif state.player_position[1] < state.player_position[1]:
            direction = -1
        elif state.player_position[0] > state.player_position[0]:
            direction = 2
        elif state.player_position[0] < state.player_position[0]:
            direction = 3

        if direction != 0:
            _, new_state, reward, done, info = state.step(
                key, state, direction, state.default_params
            )
            state = new_state

        # Craft
        action = craft_key
        _, new_state, reward, done, info = state.step(
            key, state, action, state.default_params
        )
        state = new_state

        # Check if pickaxe was crafted
        if state.inventory.pickaxe >= pickaxe_level:
            return True

        # Check if we're stuck
        if step > 0 and step > max_steps // 2:
            return False

    return False
