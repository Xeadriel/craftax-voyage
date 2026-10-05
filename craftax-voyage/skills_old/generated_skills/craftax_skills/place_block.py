# Description:
# Places a block at a specified position if the player has the required materials.
# Checks for valid placement location and required inventory.
# Returns True on success, raises ValueError on failure.

from craftax.craftax.constants import (
    Action,
    BlockType,
    ItemType,
    CAN_PLACE_ITEM_BLOCKS,
)
from craftax.craftax.util.game_logic_utils import (
    is_in_solid_block,
    is_position_in_bounds_not_in_mob_not_colliding,
    in_bounds,
)


def place_block(env_step_fn, state, block_type: BlockType, position: jnp.ndarray, max_steps: int = 50):
    """
    Places a block at a specified position if the player has the required materials.
    
    Args:
        env_step_fn: Function to call for environment step
        state: Current environment state
        block_type: The block type to place (e.g., STONE, PATH)
        position: Target position [x, y]
        max_steps: Maximum number of steps to place
    
    Returns:
        True if placement was successful
    
    Raises:
        ValueError: If block not found in inventory, position invalid, or placement failed
    """
    import jax.numpy as jnp
    
    # Check if block type can be placed
    if block_type.value not in CAN_PLACE_ITEM_BLOCKS:
        raise ValueError(f"Block type {block_type.name} cannot be placed by player")
    
    # Check if position is valid
    if not in_bounds(state, position):
        raise ValueError(f"Position {position} is out of bounds")
    
    # Check if position is in a solid block
    if is_in_solid_block(state, position):
        raise ValueError(f"Position {position} is a solid block")
    
    # Check if position is in a mob
    if is_in_mob(state, position):
        raise ValueError(f"Position {position} is occupied by a mob")
    
    # Check if we have the required item
    item_to_place = get_item_for_block(block_type)
    
    if item_to_place is None:
        raise ValueError(f"No item found for block type {block_type.name}")
    
    # Check inventory
    current_item = state.inventory
    if current_item[item_to_place] <= 0:
        raise ValueError(f"No {item_to_place.name} in inventory to place {block_type.name}")
    
    # Move to position
    move_to_position(env_step_fn, state, position, max_steps)
    
    # Place the block
    success = place_at_position(env_step_fn, state, position, item_to_place, max_steps)
    
    return success


def get_item_for_block(block_type: BlockType) -> ItemType:
    """
    Returns the item type needed to place the block.
    
    Args:
        block_type: The block type to place
    
    Returns:
        Item type needed (e.g., STONE, PATH)
    """
    # Map block types to item types
    block_to_item = {
        BlockType.STONE.value: ItemType.STONE.value,
        BlockType.PATH.value: ItemType.STONE.value,
        BlockType.WATER.value: ItemType.WATER.value,
        BlockType.FOUNTAIN.value: ItemType.WATER.value,
    }
    
    return block_to_item.get(block_type.value, ItemType.NONE.value)


def move_to_position(env_step_fn, state, target_pos, max_steps: int = 50):
    """
    Moves the player to the target position.
    
    Args:
        env_step_fn: Function to call for environment step
        state: Current environment state
        target_pos: Target position [x, y]
        max_steps: Maximum number of steps to move
    
    Raises:
        ValueError: If target position is invalid or unreachable
    """
    import jax.numpy as jnp
    
    # Calculate direction to target
    current_pos = state.player_position
    direction = target_pos - current_pos
    
    # Check if target is in bounds
    if not in_bounds(state, target_pos):
        raise ValueError(f"Target position {target_pos} is out of bounds")
    
    # Check if target is in a solid block
    if is_in_solid_block(state, target_pos):
        raise ValueError(f"Target position {target_pos} is a solid block")
    
    # Check if target is in a mob
    if is_in_mob(state, target_pos):
        raise ValueError(f"Target position {target_pos} is occupied by a mob")
    
    # Move towards target
    for step in range(max_steps):
        # Find closest valid direction
        best_dir = None
        best_distance = float('inf')
        
        for action in [Action.UP.value, Action.DOWN.value, Action.LEFT.value, Action.RIGHT.value]:
            proposed_pos = current_pos + DIRECTIONS[action]
            
            if in_bounds(state, proposed_pos) and not is_in_solid_block(state, proposed_pos) and not is_in_mob(state, proposed_pos):
                distance = jnp.sum(jnp.abs(proposed_pos - target_pos))
                if distance < best_distance:
                    best_distance = distance
                    best_dir = action
        
        if best_dir is None:
            raise ValueError("Cannot move towards target - no valid path")
        
        # Execute move
        env_step_fn(state, best_dir)
        state = state.replace(
            player_position=current_pos + DIRECTIONS[best_dir],
            player_direction=best_dir
        )
        current_pos = state.player_position
    
    # Verify we reached the target
    if not in_bounds(state, target_pos):
        raise ValueError("Failed to reach target position")
    
    return True


def place_at_position(env_step_fn, state, target_pos, item_type: ItemType, max_steps: int = 50):
    """
    Places an item at the specified position.
    
    Args:
        env_step_fn: Function to call for environment step
        state: Current environment state
        target_pos: Position to place [x, y]
        item_type: Item type to place
        max_steps: Maximum number of steps to place
    
    Returns:
        True if placement was successful
    
    Raises:
        ValueError: If placement failed
    """
    import jax.numpy as jnp
    
    # Check if position is valid
    if not in_bounds(state, target_pos):
        raise ValueError(f"Position {target_pos} is out of bounds")
    
    # Check if position is in a solid block
    if is_in_solid_block(state, target_pos):
        raise ValueError(f"Position {target_pos} is a solid block")
    
    # Check if position is in a mob
    if is_in_mob(state, target_pos):
        raise ValueError(f"Position {target_pos} is occupied by a mob")
    
    # Execute placement action
    for step in range(max_steps):
        # Check if we're at the target position
        if state.player_position != target_pos:
            # Move to target
            move_to_position(env_step_fn, state, target_pos, max_steps - step)
            break
        
        # Try to place using appropriate action
        action = get_placement_action(item_type)
        env_step_fn(state, action)
        state = state.replace(timestep=state.timestep + 1)
        
        # Check if item was placed
        item_at_pos = state.item_map[state.player_level][target_pos[0], target_pos[1]]
        if item_at_pos == item_type.value:
            return True
        
        # Check if we're stuck
        if step >= max_steps - 5:
            raise ValueError("Placement action failed after multiple attempts")
    
    raise ValueError("Placement action failed")


def get_placement_action(item_type: ItemType) -> Action:
    """
    Returns the action to place the item.
    
    Args:
        item_type: Item type to place
    
    Returns:
        Action to place the item
    """
    placement_actions = {
        ItemType.STONE.value: Action.PLACE_STONE.value,
        ItemType.TORCH.value: Action.PLACE_TORCH.value,
        ItemType.PLANT.value: Action.PLACE_PLANT.value,
        ItemType.TABLE.value: Action.PLACE_TABLE.value,
        ItemType.FURNACE.value: Action.PLACE_FURNACE.value,
    }
    
    return placement_actions.get(item_type.value, Action.NOOP.value)
