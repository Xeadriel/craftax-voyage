# Skill: smelt_item
# Purpose: Smelts an item in a furnace
# Required inputs: item_name (string), fuel_name (string), count (int), max_steps (int)
# Preconditions: Player must be at a furnace, have fuel and item to smelt
# Expected effects: Item is smelted and converted to desired form, fuel consumed
# Failure conditions: No furnace, insufficient fuel, invalid item
# Explanation: Uses state.map to find furnace, state.inventory for fuel and items,
#             Action.PLACE_FURNACE for furnace interaction

import jax
from craftax.craftax.constants import BlockType, Action
from craftax.craftax.craftax_state import EnvState
from craftax.craftax.util.game_logic_utils import is_near_block


def smelt_item(
    state: EnvState,
    item_name: str,
    fuel_name: str,
    count: int = 1,
    max_steps: int = 100,
) -> bool:
    """
    Smelts an item in a furnace.

    Returns True if smelting succeeded, False otherwise.
    """
    # Define smelting recipes
    smelting_recipes = {
        "coal": {"coal": 1, "iron": 1},
        "iron": {"iron": 1, "iron": 1},
        "diamond": {"diamond": 1, "diamond": 1},
        "sapphire": {"sapphire": 1, "sapphire": 1},
        "ruby": {"ruby": 1, "ruby": 1},
    }

    recipe = smelting_recipes.get(item_name)
    if not recipe:
        return False

    # Check if we have required fuel
    fuel_amount = recipe.get(fuel_name, 1)
    current_fuel = getattr(state.inventory, fuel_name)
    if current_fuel < fuel_amount:
        return False

    # Check if we have the item to smelt
    item_amount = recipe.get(item_name, 1)
    current_item = getattr(state.inventory, item_name)
    if current_item < item_amount:
        return False

    # Find a furnace
    if not is_near_block(state, BlockType.FURNACE.value):
        return False

    # Check if we're at a furnace
    if not is_near_block(state, BlockType.FURNACE.value):
        return False

    # Smelt the item by placing it in the furnace
    # Note: In Craftax, smelting is done by placing items in a furnace
    # The environment handles the actual smelting logic

    for step in range(max_steps):
        key = jax.random.PRNGKey(0)
        # Place the item in the furnace
        action = Action.DO.value
        _, new_state, reward, done, info = state.step(
            key, state, action, state.default_params
        )
        state = new_state

        # Check if we got the smelted item
        if getattr(state.inventory, item_name) > 0:
            return True

        # Check if we're stuck
        if step > 0 and step > max_steps // 2:
            return False

    return False
