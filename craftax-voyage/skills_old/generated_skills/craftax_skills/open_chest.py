# Description:
# Opens a chest if found nearby.
# Checks for chest availability and moves to it.
# Returns True on success, raises ValueError on failure.

from craftax.craftax.constants import (
    Action,
    BlockType,
)
from craftax.craftax.util.game_logic_utils import (
    is_in_mob,
    is_position_in_bounds_not_in_mob_not_colliding,
    in_bounds,
)


def open_chest(env_step_fn, state, max_steps: int = 50):
    """
    Opens a chest if found nearby.
    
    Args:
        env_step_fn: Function to call for environment step
        state: Current environment state
        max_steps: Maximum number of steps to open
    
    Returns:
        True if chest was opened
    
    Raises:
        ValueError: If no chest found or opening failed
    """
    import jax.numpy as jnp
    
    # Find a chest
    chest_pos = find_chest(env_step_fn, state, max_steps)
    
    if chest_pos is None:
        raise ValueError("No chest found in visible area")
    
    # Move to chest
    move_to_chest(env_step_fn, state, chest_pos, max_steps)
    
    # Open the chest
    success = open_at_position(env_step_fn, state, chest_pos, max_steps)
    
    return success


def find_chest(env_step_fn, state, max_steps: int = 50):
    """
    Finds a chest in the visible area.
    
    Args:
        env_step_fn: Function to call for environment step
        state: Current environment state
        max_steps: Maximum number of steps to search
    
    Returns:
        Position of chest or None
    """
    import jax.numpy as jnp
    
    # Check all visible positions for chest
    for dy in range(-3, 4):
        for dx in range(-3, 4):
            candidate_pos = state.player_position + jnp.array([dx, dy])
            if in_bounds(state, candidate_pos):
                block_at_pos = state.map[state.player_level][candidate_pos[0], candidate_pos[1]]
                if block_at_pos == BlockType.CHEST.value:
                    return candidate_pos
    
    return None


def move_to_chest(env_step_fn, state, target_pos, max_steps: int = 50):
    """
    Moves the player to the chest position.
    
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


def open_at_position(env_step_fn, state, target_pos, max_steps: int = 50):
    """
    Opens a chest at the specified position.
    
    Args:
        env_step_fn: Function to call for environment step
        state: Current environment state
        target_pos: Position of chest [x, y]
        max_steps: Maximum number of steps to open
    
    Returns:
        True if chest was opened
    
    Raises:
        ValueError: If opening failed
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
    
    # Execute opening action
    for step in range(max_steps):
        # Check if we're at the target position
        if state.player_position != target_pos:
            # Move to target
            move_to_chest(env_step_fn, state, target_pos, max_steps - step)
            break
        
        # Try to open using DO action
        env_step_fn(state, Action.DO.value)
        state = state.replace(timestep=state.timestep + 1)
        
        # Check if chest was opened
        block_at_pos = state.map[state.player_level][target_pos[0], target_pos[1]]
        if block_at_pos == BlockType.PATH.value:
            return True
        
        # Check if we're stuck
        if step >= max_steps - 5:
            raise ValueError("Opening action failed after multiple attempts")
    
    raise ValueError("Opening action failed")
