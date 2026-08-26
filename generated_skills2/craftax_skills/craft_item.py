# Skill: craft_item
# Purpose: Crafts a specified item at a crafting table
# Required inputs: item_name (string), count (int), max_steps (int)
# Preconditions: Player must be at a crafting table, have required materials
# Expected effects: Item is crafted and added to inventory, materials consumed
# Failure conditions: No crafting table, insufficient materials, invalid item
# Explanation: Uses state.map to find crafting table, state.inventory for materials,
#             Action.PLACE_TABLE for crafting interaction

import jax
from craftax.craftax.constants import BlockType, Action
from craftax.craftax.craftax_state import EnvState
from craftax.craftax.util.game_logic_utils import is_near_block


def craft_item(
    state: EnvState, item_name: str, count: int = 1, max_steps: int = 100
) -> bool:
    """
    Crafts a specified item at a crafting table.

    Returns True if crafting succeeded, False otherwise.
    """
    # Define crafting recipes based on item name
    crafting_recipes = {
        "wood_pickaxe": {"wood": 1, "pickaxe": 0},
        "stone_pickaxe": {"wood": 1, "stone": 1, "pickaxe": 1},
        "iron_pickaxe": {"wood": 1, "stone": 1, "iron": 1, "coal": 1, "pickaxe": 2},
        "diamond_pickaxe": {"wood": 1, "diamond": 3, "pickaxe": 3},
        "wood_sword": {"wood": 1, "sword": 0},
        "stone_sword": {"wood": 1, "stone": 1, "sword": 1},
        "iron_sword": {"wood": 1, "iron": 1, "stone": 1, "coal": 1, "sword": 2},
        "diamond_sword": {"wood": 1, "diamond": 2, "sword": 3},
        "torch": {"wood": 1, "coal": 1, "torches": 0},
        "arrow": {"wood": 1, "stone": 1, "arrows": 0},
    }

    recipe = crafting_recipes.get(item_name)
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

    # Craft the item by pressing the appropriate key
    # The key depends on the item type
    craft_keys = {
        "wood_pickaxe": Action.MAKE_WOOD_PICKAXE.value,
        "stone_pickaxe": Action.MAKE_STONE_PICKAXE.value,
        "iron_pickaxe": Action.MAKE_IRON_PICKAXE.value,
        "diamond_pickaxe": Action.MAKE_DIAMOND_PICKAXE.value,
        "wood_sword": Action.MAKE_WOOD_SWORD.value,
        "stone_sword": Action.MAKE_STONE_SWORD.value,
        "iron_sword": Action.MAKE_IRON_SWORD.value,
        "diamond_sword": Action.MAKE_DIAMOND_SWORD.value,
        "torch": Action.MAKE_TORCH.value,
        "arrow": Action.MAKE_ARROW.value,
    }

    craft_key = craft_keys.get(item_name)
    if not craft_key:
        return False

    # Perform crafting action
    for step in range(max_steps):
        key = jax.random.PRNGKey(0)
        _, new_state, reward, done, info = state.step(
            key, state, craft_key, state.default_params
        )
        state = new_state

        # Check if we got the item
        if getattr(state.inventory, item_name.lower()) > 0:
            return True

        # Check if we're stuck
        if step > 0 and step > max_steps // 2:
            return False

    return False
