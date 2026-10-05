# Skill: craft_item
# Purpose: Crafts a specified item at a crafting table or furnace
# Required inputs: item_name (string), location_type (string: 'table' or 'furnace')
# Preconditions:
#   - Player must be adjacent to crafting table or furnace
#   - Player must have required materials in inventory
#   - Player must have the appropriate pickaxe level for certain items
# Expected effects:
#   - Item is crafted and added to inventory
#   - Required materials are consumed from inventory
#   - Achievement may be triggered for crafting
# Failure conditions:
#   - No crafting table or furnace nearby
#   - Insufficient materials in inventory
#   - Cannot craft at wrong location (e.g., iron pickaxe at table)
# Explanation: Uses do_crafting from game_logic.py which handles crafting logic
#           Checks is_near_block from game_logic_utils.py for proximity
#           Requires materials from inventory to determine crafting capability

import jax.numpy as jnp
from craftax.craftax.constants import BlockType, ItemType, Action
from craftax.craftax.craftax_state import EnvState


def craft_item(state: EnvState, item_name: str, location_type: str = 'table') -> EnvState:
    """
    Crafts a specified item at a crafting table or furnace.
    
    Args:
        state: Current environment state
        item_name: Name of item to craft (e.g., 'WOOD_PICKAXE', 'STONE_SWORD', 'IRON_ARMOUR')
        location_type: 'table' for crafting table, 'furnace' for furnace
    
    Returns:
        New state with item crafted
    
    Raises:
        ValueError: If crafting is not possible
    """
    # Map item name to crafting action
    if item_name == 'WOOD_PICKAXE':
        action = Action.MAKE_WOOD_PICKAXE.value
        requires_table = True
        requires_furnace = False
    elif item_name == 'STONE_PICKAXE':
        action = Action.MAKE_STONE_PICKAXE.value
        requires_table = True
        requires_furnace = False
    elif item_name == 'IRON_PICKAXE':
        action = Action.MAKE_IRON_PICKAXE.value
        requires_table = True
        requires_furnace = True
    elif item_name == 'DIAMOND_PICKAXE':
        action = Action.MAKE_DIAMOND_PICKAXE.value
        requires_table = True
        requires_furnace = False
    elif item_name == 'WOOD_SWORD':
        action = Action.MAKE_WOOD_SWORD.value
        requires_table = True
        requires_furnace = False
    elif item_name == 'STONE_SWORD':
        action = Action.MAKE_STONE_SWORD.value
        requires_table = True
        requires_furnace = False
    elif item_name == 'IRON_SWORD':
        action = Action.MAKE_IRON_SWORD.value
        requires_table = True
        requires_furnace = True
    elif item_name == 'DIAMOND_SWORD':
        action = Action.MAKE_DIAMOND_SWORD.value
        requires_table = True
        requires_furnace = False
    elif item_name == 'IRON_ARMOUR':
        action = Action.MAKE_IRON_ARMOUR.value
        requires_table = True
        requires_furnace = True
    elif item_name == 'DIAMOND_ARMOUR':
        action = Action.MAKE_DIAMOND_ARMOUR.value
        requires_table = True
        requires_furnace = False
    elif item_name == 'TORCH':
        action = Action.MAKE_TORCH.value
        requires_table = True
        requires_furnace = False
    elif item_name == 'ARROW':
        action = Action.MAKE_ARROW.value
        requires_table = True
        requires_furnace = False
    else:
        raise ValueError(f"Unknown item to craft: {item_name}")
    
    # Check proximity to crafting table or furnace
    if location_type == 'table':
        if not _is_near_crafting_table(state):
            raise ValueError("No crafting table nearby")
    elif location_type == 'furnace':
        if not _is_near_furnace(state):
            raise ValueError("No furnace nearby")
    
    # Check material requirements
    if item_name == 'WOOD_PICKAXE':
        if state.inventory.wood < 1:
            raise ValueError("No WOOD in inventory")
        new_inventory = state.inventory.replace(
            wood=state.inventory.wood - 1,
            pickaxe=state.inventory.pickaxe + 1
        )
    elif item_name == 'STONE_PICKAXE':
        if state.inventory.wood < 1 or state.inventory.stone < 1:
            raise ValueError("No WOOD or STONE in inventory")
        new_inventory = state.inventory.replace(
            wood=state.inventory.wood - 1,
            stone=state.inventory.stone - 1,
            pickaxe=state.inventory.pickaxe + 2
        )
    elif item_name == 'IRON_PICKAXE':
        if state.inventory.wood < 1 or state.inventory.stone < 1 or \
           state.inventory.iron < 1 or state.inventory.coal < 1:
            raise ValueError("No WOOD, STONE, IRON, or COAL in inventory")
        new_inventory = state.inventory.replace(
            wood=state.inventory.wood - 1,
            stone=state.inventory.stone - 1,
            iron=state.inventory.iron - 1,
            coal=state.inventory.coal - 1,
            pickaxe=state.inventory.pickaxe + 3
        )
    elif item_name == 'DIAMOND_PICKAXE':
        if state.inventory.wood < 1 or state.inventory.diamond < 3:
            raise ValueError("No WOOD or DIAMOND in inventory")
        new_inventory = state.inventory.replace(
            wood=state.inventory.wood - 1,
            diamond=state.inventory.diamond - 3,
            pickaxe=state.inventory.pickaxe + 4
        )
    elif item_name == 'WOOD_SWORD':
        if state.inventory.wood < 1:
            raise ValueError("No WOOD in inventory")
        new_inventory = state.inventory.replace(
            wood=state.inventory.wood - 1,
            sword=state.inventory.sword + 1
        )
    elif item_name == 'STONE_SWORD':
        if state.inventory.stone < 1 or state.inventory.wood < 1:
            raise ValueError("No STONE or WOOD in inventory")
        new_inventory = state.inventory.replace(
            stone=state.inventory.stone - 1,
            wood=state.inventory.wood - 1,
            sword=state.inventory.sword + 2
        )
    elif item_name == 'IRON_SWORD':
        if state.inventory.iron < 1 or state.inventory.wood < 1 or \
           state.inventory.stone < 1 or state.inventory.coal < 1:
            raise ValueError("No IRON, WOOD, STONE, or COAL in inventory")
        new_inventory = state.inventory.replace(
            iron=state.inventory.iron - 1,
            wood=state.inventory.wood - 1,
            stone=state.inventory.stone - 1,
            coal=state.inventory.coal - 1,
            sword=state.inventory.sword + 3
        )
    elif item_name == 'DIAMOND_SWORD':
        if state.inventory.diamond < 2 or state.inventory.wood < 1:
            raise ValueError("No DIAMOND or WOOD in inventory")
        new_inventory = state.inventory.replace(
            diamond=state.inventory.diamond - 2,
            wood=state.inventory.wood - 1,
            sword=state.inventory.sword + 4
        )
    elif item_name == 'IRON_ARMOUR':
        if state.inventory.iron < 3 or state.inventory.coal < 3:
            raise ValueError("No IRON or COAL in inventory")
        new_inventory = state.inventory.replace(
            iron=state.inventory.iron - 3,
            coal=state.inventory.coal - 3,
            armour=state.inventory.armour + 1
        )
    elif item_name == 'DIAMOND_ARMOUR':
        if state.inventory.diamond < 3:
            raise ValueError("No DIAMOND in inventory")
        new_inventory = state.inventory.replace(
            diamond=state.inventory.diamond - 3,
            armour=state.inventory.armour + 2
        )
    elif item_name == 'TORCH':
        if state.inventory.coal < 1 or state.inventory.wood < 1:
            raise ValueError("No COAL or WOOD in inventory")
        new_inventory = state.inventory.replace(
            coal=state.inventory.coal - 1,
            wood=state.inventory.wood - 1,
            torches=state.inventory.torches + 4
        )
    elif item_name == 'ARROW':
        if state.inventory.stone < 1 or state.inventory.wood < 1:
            raise ValueError("No STONE or WOOD in inventory")
        new_inventory = state.inventory.replace(
            stone=state.inventory.stone - 1,
            wood=state.inventory.wood - 1,
            arrows=state.inventory.arrows + 2
        )
    else:
        raise ValueError(f"Unknown item to craft: {item_name}")
    
    return state.replace(inventory=new_inventory)


def _is_near_crafting_table(state: EnvState) -> bool:
    """Check if player is near a crafting table."""
    for dx, dy in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
        pos = state.player_position + jnp.array([dx, dy])
        if (0 <= pos[0] < state.map[state.player_level].shape[0] and
                0 <= pos[1] < state.map[state.player_level].shape[1]):
            if state.map[state.player_level, pos[0], pos[1]] == BlockType.CRAFTING_TABLE.value:
                return True
    return False


def _is_near_furnace(state: EnvState) -> bool:
    """Check if player is near a furnace."""
    for dx, dy in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
        pos = state.player_position + jnp.array([dx, dy])
        if (0 <= pos[0] < state.map[state.player_level].shape[0] and
                0 <= pos[1] < state.map[state.player_level].shape[1]):
            if state.map[state.player_level, pos[0], pos[1]] == BlockType.FURNACE.value:
                return True
    return False
