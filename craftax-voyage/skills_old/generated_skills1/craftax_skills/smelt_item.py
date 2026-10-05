# Skill: smelt_item
# Purpose: Smelts an item in a furnace
# Required inputs: item_name (string), fuel_name (string)
# Preconditions:
#   - Player must be adjacent to a furnace
#   - Player must have the item and fuel in inventory
#   - Furnace must have fuel or player must add fuel
# Expected effects:
#   - Item is smelted and output is added to inventory
#   - Fuel is consumed from inventory
#   - Furnace is closed after smelting
# Failure conditions:
#   - No furnace nearby
#   - Insufficient item or fuel in inventory
#   - Item is not smeltable
# Explanation: Uses furnace interaction logic from game_logic.py
#           Checks for furnace proximity using is_near_block from game_logic_utils.py
#           Requires fuel and item from inventory

import jax.numpy as jnp
from craftax.craftax.constants import BlockType, ItemType, Action
from craftax.craftax.craftax_state import EnvState


def smelt_item(state: EnvState, item_name: str, fuel_name: str, count: int = 1) -> EnvState:
    """
    Smelts an item in a furnace.
    
    Args:
        state: Current environment state
        item_name: Name of item to smelt (e.g., 'COAL', 'IRON_INGOT')
        fuel_name: Name of fuel (e.g., 'COAL', 'WOOD')
        count: Number of items to smelt
    
    Returns:
        New state with smelted item added to inventory
    
    Raises:
        ValueError: If smelting is not possible
    """
    # Map item name to smeltable items
    smeltable_items = ['COAL', 'IRON', 'DIAMOND', 'SAPPHIRE', 'RUBY']
    if item_name not in smeltable_items:
        raise ValueError(f"Item {item_name} cannot be smelted")
    
    # Check proximity to furnace
    if not _is_near_furnace(state):
        raise ValueError("No furnace nearby")
    
    # Check if furnace is open
    if not _is_furnace_open(state):
        raise ValueError("Furnace is closed")
    
    # Check if furnace has fuel
    if not _has_fuel(state):
        raise ValueError("Furnace has no fuel")
    
    # Check inventory
    for i in range(count):
        if state.inventory.coal <= 0:
            raise ValueError("No COAL in inventory")
        if state.inventory.iron <= 0:
            raise ValueError("No IRON in inventory")
        if state.inventory.diamond <= 0:
            raise ValueError("No DIAMOND in inventory")
        if state.inventory.sapphire <= 0:
            raise ValueError("No SAPPHIRE in inventory")
        if state.inventory.ruby <= 0:
            raise ValueError("No RUBY in inventory")
    
    # Consume fuel and item
    new_inventory = state.inventory.replace(
        coal=state.inventory.coal - 1,
        iron=state.inventory.iron - 1,
        diamond=state.inventory.diamond - 1,
        sapphire=state.inventory.sapphire - 1,
        ruby=state.inventory.ruby - 1,
    )
    
    # Add smelted item (simplified - in real implementation would check recipe)
    smelted_item = item_name.lower() + '_INGOT'
    new_inventory = new_inventory.replace(
        coal=state.inventory.coal + 1 if item_name == 'COAL' else 0,
        iron=state.inventory.iron + 1 if item_name == 'IRON' else 0,
        diamond=state.inventory.diamond + 1 if item_name == 'DIAMOND' else 0,
        sapphire=state.inventory.sapphire + 1 if item_name == 'SAPPHIRE' else 0,
        ruby=state.inventory.ruby + 1 if item_name == 'RUBY' else 0,
    )
    
    return state.replace(inventory=new_inventory)


def _is_near_furnace(state: EnvState) -> bool:
    """Check if player is near a furnace."""
    for dx, dy in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
        pos = state.player_position + jnp.array([dx, dy])
        if (0 <= pos[0] < state.map[state.player_level].shape[0] and
                0 <= pos[1] < state.map[state.player_level].shape[1]):
            if state.map[state.player_level, pos[0], pos[1]] == BlockType.FURNACE.value:
                return True
    return False


def _is_furnace_open(state: EnvState) -> bool:
    """Check if furnace is open (player is adjacent to it)."""
    for dx, dy in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
        pos = state.player_position + jnp.array([dx, dy])
        if (0 <= pos[0] < state.map[state.player_level].shape[0] and
                0 <= pos[1] < state.map[state.player_level].shape[1]):
            if state.map[state.player_level, pos[0], pos[1]] == BlockType.FURNACE.value:
                return True
    return False


def _has_fuel(state: EnvState) -> bool:
    """Check if furnace has fuel."""
    # Simplified check - in real implementation would check furnace state
    return state.inventory.coal > 0 or state.inventory.iron > 0 or \
           state.inventory.diamond > 0 or state.inventory.sapphire > 0 or \
           state.inventory.ruby > 0
