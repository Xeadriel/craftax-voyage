# Description:
# Moves to and mines a specified block type if available.
# Checks for required tool level before attempting to mine.
# Returns True on success, raises ValueError on failure.

from craftax.craftax.constants import (
    Action,
    BlockType,
    SOLID_BLOCKS,
)
from craftax.craftax.util.game_logic_utils import (
    is_in_solid_block,
    is_position_in_bounds_not_in_mob_not_colliding,
    in_bounds,
)


def mine_block(env_step_fn, state, block_type: BlockType, max_steps: int = 50):
    """
    Moves to and mines a specified block type if available.
    
    Args:
        env_step_fn: Function to call for environment step
        state: Current environment state
        block_type: The block type to mine (e.g., STONE, IRON, DIAMOND)
        max_steps: Maximum number of steps to attempt mining
    
    Returns:
        True if mining was successful
    
    Raises:
        ValueError: If block not found, no tool available, or action failed
    """
    # Check if block type is in solid blocks list
    if block_type.value not in SOLID_BLOCKS:
        raise ValueError(f"Block type {block_type.name} is not a solid block that can be mined")
    
    # Get current position and direction
    current_pos = state.player_position
    current_dir = state.player_direction
    
    # Search for the block in the visible map area
    # Map is 9x11 visible area centered on player
    search_range = 3  # Search within 3 tiles of visible area
    
    found_block = None
    found_pos = None
    
    # Search for the block in the visible map
    for dy in range(-search_range, search_range + 1):
        for dx in range(-search_range, search_range + 1):
            candidate_pos = current_pos + jnp.array([dx, dy])
            if in_bounds(state, candidate_pos):
                block_at_pos = state.map[state.player_level][candidate_pos[0], candidate_pos[1]]
                if block_at_pos == block_type.value:
                    found_block = block_at_pos
                    found_pos = candidate_pos
                    break
        if found_block is not None:
            break
    
    if found_block is None:
        raise ValueError(f"Block type {block_type.name} not found in visible area")
    
    # Check if we have the required tool level
    # Pickaxe levels: 1=wood, 2=stone, 3=iron, 4=diamond
    required_pickaxe_level = get_required_pickaxe_level(block_type)
    current_pickaxe = state.inventory.pickaxe
    
    if current_pickaxe < required_pickaxe_level:
        raise ValueError(
            f"Need pickaxe level {required_pickaxe_level} to mine {block_type.name}, "
            f"have level {current_pickaxe}"
        )
    
    # Move towards the block
    move_to_block(env_step_fn, state, found_pos, max_steps)
    
    # Mine the block
    success = mine_at_position(env_step_fn, state, found_pos, max_steps)
    
    return success


def get_required_pickaxe_level(block_type: BlockType) -> int:
    """
    Returns the minimum pickaxe level required to mine the block.
    
    Args:
        block_type: The block type to mine
    
    Returns:
        Required pickaxe level (1=wood, 2=stone, 3=iron, 4=diamond)
    """
    # Map block types to required pickaxe levels
    pickaxe_requirements = {
        BlockType.STONE.value: 1,
        BlockType.COAL.value: 1,
        BlockType.IRON.value: 2,
        BlockType.DIAMOND.value: 3,
        BlockType.SAPPHIRE.value: 4,
        BlockType.RUBY.value: 4,
        BlockType.TREE.value: 1,
        BlockType.FURNACE.value: 1,
        BlockType.CRAFTING_TABLE.value: 1,
        BlockType.STALAGMITE.value: 1,
    }
    
    return pickaxe_requirements.get(block_type.value, 1)


def move_to_block(env_step_fn, state, target_pos, max_steps: int = 50):
    """
    Moves the player towards the target position.
    
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


def mine_at_position(env_step_fn, state, target_pos, max_steps: int = 50):
    """
    Mines a block at the specified position.
    
    Args:
        env_step_fn: Function to call for environment step
        state: Current environment state
        target_pos: Position to mine [x, y]
        max_steps: Maximum number of steps to mine
    
    Returns:
        True if mining was successful
    
    Raises:
        ValueError: If mining failed
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
    
    # Execute mining action
    for step in range(max_steps):
        # Check if we're at the target position
        if state.player_position != target_pos:
            # Move to target
            move_to_block(env_step_fn, state, target_pos, max_steps - step)
            break
        
        # Try to mine using DO action
        env_step_fn(state, Action.DO.value)
        state = state.replace(timestep=state.timestep + 1)
        
        # Check if block was mined
        block_at_pos = state.map[state.player_level][target_pos[0], target_pos[1]]
        if block_at_pos == BlockType.PATH.value:
            return True
        
        # Check if we're stuck
        if step >= max_steps - 5:
            raise ValueError("Mining action failed after multiple attempts")
    
    raise ValueError("Mining action failed")
