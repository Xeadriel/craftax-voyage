# Skill: place_block
# Purpose: Places a specified block type at the player's current facing direction
# Required inputs: block_name (string) - name of block to place
# Preconditions:
#   - Player must have required materials in inventory
#   - Target position must be valid (not solid, not in mob)
#   - Must be adjacent to crafting table or furnace for certain items
# Expected effects:
#   - Block is placed at target position
#   - Required materials are consumed from inventory
#   - Achievement may be triggered for placing
# Failure conditions:
#   - Insufficient materials in inventory
#   - Target position is solid or in a mob
#   - Cannot place on water (except stone)
#   - Cannot place on solid block
# Explanation: Uses place_block from game_logic.py which handles placement logic
#           Checks CAN_PLACE_ITEM_MAPPING from constants.py for valid placement blocks
#           Requires materials from inventory to determine placement capability

import jax.numpy as jnp
from craftax.craftax.constants import BlockType, ItemType, Action, DIRECTIONS
from craftax.craftax.craftax_state import EnvState


def place_block(state: EnvState, block_name: str) -> EnvState:
    """
    Places a specified block type at the player's current facing direction.
    
    Args:
        state: Current environment state
        block_name: Name of block to place (e.g., 'STONE', 'TABLE', 'FURNACE', 'TORCH', 'PLANT')
    
    Returns:
        New state with block placed and materials consumed
    
    Raises:
        ValueError: If placement is not possible
    """
    # Map block name to appropriate action
    if block_name == 'STONE':
        action = Action.PLACE_STONE.value
    elif block_name == 'TABLE':
        action = Action.PLACE_TABLE.value
    elif block_name == 'FURNACE':
        action = Action.PLACE_FURNACE.value
    elif block_name == 'TORCH':
        action = Action.PLACE_TORCH.value
    elif block_name == 'PLANT':
        action = Action.PLACE_PLANT.value
    else:
        raise ValueError(f"Unknown block type: {block_name}")
    
    # Calculate target position based on player direction
    target_position = state.player_position + DIRECTIONS[state.player_direction]
    
    # Check if position is in bounds
    if not (0 <= target_position[0] < state.map[state.player_level].shape[0] and
            0 <= target_position[1] < state.map[state.player_level].shape[1]):
        raise ValueError(f"Target position {target_position} is out of bounds")
    
    # Check if position is occupied by a mob
    if state.mob_map[state.player_level, target_position[0], target_position[1]]:
        raise ValueError(f"Position {target_position} is occupied by a mob")
    
    # Check if position is solid
    if BlockType(state.map[state.player_level, target_position[0], target_position[1]]).value in [
        BlockType.STONE.value, BlockType.TREE.value, BlockType.COAL.value, BlockType.IRON.value,
        BlockType.DIAMOND.value, BlockType.CRAFTING_TABLE.value, BlockType.FURNACE.value,
        BlockType.PLANT.value, BlockType.RIPE_PLANT.value, BlockType.WALL.value,
        BlockType.WALL_MOSS.value, BlockType.STALAGMITE.value, BlockType.RUBY.value,
        BlockType.SAPPHIRE.value, BlockType.CHEST.value, BlockType.FOUNTAIN.value,
        BlockType.FIRE_TREE.value, BlockType.ENCHANTMENT_TABLE_FIRE.value,
        BlockType.ENCHANTMENT_TABLE_ICE.value, BlockType.GRAVE.value, BlockType.GRAVE2.value,
        BlockType.GRAVE3.value, BlockType.NECROMANCER.value
    ]:
        raise ValueError(f"Cannot place block on solid block at {target_position}")
    
    # Check if position is water (only stone can be placed on water)
    if state.map[state.player_level, target_position[0], target_position[1]] == BlockType.WATER.value:
        if block_name != 'STONE':
            raise ValueError(f"Cannot place {block_name} on water")
    
    # Check if position has an item (cannot place on existing item)
    if state.item_map[state.player_level, target_position[0], target_position[1]] != ItemType.NONE.value:
        raise ValueError(f"Position {target_position} already has an item")
    
    # Check material requirements
    if block_name == 'STONE':
        if state.inventory.stone <= 0:
            raise ValueError("No STONE in inventory")
        new_inventory = state.inventory.replace(
            stone=state.inventory.stone - 1
        )
    elif block_name == 'TABLE':
        if state.inventory.wood <= 0:
            raise ValueError("No WOOD in inventory")
        new_inventory = state.inventory.replace(
            wood=state.inventory.wood - 2
        )
    elif block_name == 'FURNACE':
        if state.inventory.stone <= 0:
            raise ValueError("No STONE in inventory")
        new_inventory = state.inventory.replace(
            stone=state.inventory.stone - 1
        )
    elif block_name == 'TORCH':
        if state.inventory.torches <= 0:
            raise ValueError("No TORCH in inventory")
        new_inventory = state.inventory.replace(
            torches=state.inventory.torches - 1
        )
    elif block_name == 'PLANT':
        if state.inventory.sapling <= 0:
            raise ValueError("No SAPLING in inventory")
        new_inventory = state.inventory.replace(
            sapling=state.inventory.sapling - 1
        )
    else:
        raise ValueError(f"Unknown block type: {block_name}")
    
    # Place the block
    new_map = state.map[state.player_level].at[target_position[0], target_position[1]].set(
        BlockType(block_name)
    )
    
    return state.replace(
        map=state.map.at[state.player_level].set(new_map),
        inventory=new_inventory,
    )
