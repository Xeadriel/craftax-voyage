# Description:
# Places a torch at a specified position if the player has torches in inventory.
# Checks for torch availability and valid placement location.
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


def place_torch(env_step_fn, state, position: jnp.ndarray, max_steps: int = 50):
    """
    Places a torch at a specified position if the player has torches in inventory.
    
    Args:
        env_step_fn: Function to call for environment step
        state: Current environment state
        position: Target position [x, y]
        max_steps: Maximum number of steps to place
    
    Returns:
        True if torch was placed
    
    Raises:
        ValueError: If no torch in inventory, position invalid, or placement failed
    """
    import jax.numpy as jnp
    
    # Check if we have torches in inventory
    if state.inventory.torches <= 0:
        raise ValueError("No torches in inventory")
    
    # Check if position is valid
    if not in_bounds(state, position):
        raise ValueError(f"Position {position} is out of bounds")
    
    # Check if position is in a solid block
    if is_in_solid_block(state, position):
        raise ValueError(f"Position {position} is a solid block")
    
    # Check if position is in a mob
    if is_in_mob(state, position):
        raise ValueError(f"Position {position} is occupied by a mob")
    
    # Check if position is on a valid block for placement
    block_at_pos = state.map[state.player_level][position[0], position[1]]
    if block_at_pos.value not in CAN_PLACE_ITEM_BLOCKS:
        raise ValueError(f"Cannot place torch on {block_at_pos.name}")
    
    # Check if position is in an item
    item_at_pos = state.item_map[state.player_level][position[0], position[1]]
    if item_at_pos != ItemType.NONE.value:
        raise ValueError(f"Position {position} is occupied by an item")
    
    # Move to position
    move_to_position(env_step_fn, state, position, max_steps)
    
    # Place the torch
    success = place_torch_at_position(env_step_fn, state, position, max_steps)
    
    return success


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


def place_torch_at_position(env_step_fn, state, target_pos, max_steps: int = 50):
    """
    Places a torch at the specified position.
    
    Args:
        env_step_fn: Function to call for environment step
        state: Current environment state
        target_pos: Position to place torch [x, y]
        max_steps: Maximum number of steps to place
    
    Returns:
        True if torch was placed
    
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
        
        # Try to place using PLACE_TORCH action
        env_step_fn(state, Action.PLACE_TORCH.value)
        state = state.replace(timestep=state.timestep + 1)
        
        # Check if torch was placed
        item_at_pos = state.item_map[state.player_level][target_pos[0], target_pos[1]]
        if item_at_pos == ItemType.TORCH.value:
            return True
        
        # Check if we're stuck
        if step >= max_steps - 5:
            raise ValueError("Placement action failed after multiple attempts")
    
    raise ValueError("Placement action failed")
