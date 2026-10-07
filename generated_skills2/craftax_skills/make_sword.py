# Skill: make_sword
# Purpose: Crafts a sword of specified level
# Required inputs: sword_level (int), max_steps (int)
# Preconditions: Player must be at a crafting table, have required materials
# Expected effects: Sword is crafted and added to inventory, materials consumed
# Failure conditions: No crafting table, insufficient materials, invalid level
# Explanation: Uses state.map for crafting table detection, state.inventory for materials,
#             Action.MAKE_* for crafting interaction

import jax
from craftax.craftax.constants import BlockType, Action
from craftax.craftax.craftax_state import EnvState
from craftax.craftax.util.game_logic_utils import is_near_block


def make_sword(state: EnvState, sword_level: int, max_steps: int = 100) -> bool:
    """
    Crafts a sword of specified level.

    Returns True if sword was crafted, False otherwise.
    """
    # Define sword crafting recipes
    sword_recipes = {
        1: {"wood": 1, "sword": 0},
        2: {"wood": 1, "stone": 1, "sword": 1},
        3: {"wood": 1, "iron": 1, "stone": 1, "coal": 1, "sword": 2},
        4: {"wood": 1, "diamond": 2, "sword": 3},
    }

    recipe = sword_recipes.get(sword_level)
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

    # Craft the sword by pressing the appropriate key
    craft_keys = {
        1: Action.MAKE_WOOD_SWORD.value,
        2: Action.MAKE_STONE_SWORD.value,
        3: Action.MAKE_IRON_SWORD.value,
        4: Action.MAKE_DIAMOND_SWORD.value,
    }

    craft_key = craft_keys.get(sword_level)
    if not craft_key:
        return False

    # Craft the sword
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

        # Check if sword was crafted
        if state.inventory.sword >= sword_level:
            return True

        # Check if we're stuck
        if step > 0 and step > max_steps // 2:
            return False

    return False
