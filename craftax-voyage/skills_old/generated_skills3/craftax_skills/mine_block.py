# Description:
# Moves to a specified block and mines it if the player has the required tool level.
# Returns True if successfully mined, False otherwise.
# Assumes the block is within 10 blocks of the player.

from craftax.craftax.constants import (
    Action,
    BlockType,
    SOLID_BLOCKS,
    DIRECTIONS,
)
from craftax.craftax.util.game_logic_utils import (
    is_in_solid_block,
    is_position_in_bounds_not_in_mob_not_colliding,
    get_distance_map,
)


def mine_block(env_step, state, block_position, max_steps=20):
    """
    Moves to a specified block and mines it if the player has the required tool level.
    
    Args:
        env_step: The environment step function
        state: Current environment state
        block_position: [x, y] coordinates of the block to mine
        max_steps: Maximum number of steps to attempt mining
    
    Returns:
        True if successfully mined, False otherwise
    """
    # Check if block is within bounds
    if not (0 <= block_position[0] < state.map[state.player_level].shape[0] and
            0 <= block_position[1] < state.map[state.player_level].shape[1]):
        raise ValueError(f"Block position {block_position} is out of bounds")
    
    # Check if block is solid and can be mined
    block_type = state.map[state.player_level][block_position[0], block_position[1]]
    if block_type in SOLID_BLOCKS:
        # Check if player has the required pickaxe level
        pickaxe_level = state.inventory.pickaxe
        required_level = 1
        if block_type == BlockType.IRON.value:
            required_level = 2
        elif block_type == BlockType.DIAMOND.value:
            required_level = 3
        elif block_type == BlockType.SAPPHIRE.value or block_type == BlockType.RUBY.value:
            required_level = 4
        
        if pickaxe_level < required_level:
            raise ValueError(
                f"Cannot mine {BlockType(block_type).name} - need pickaxe level {required_level}, have {pickaxe_level}"
            )
    else:
        # Grass can be mined with any tool
        pass
    
    # Check if block is in front of player
    player_direction = state.player_direction
    front_block = block_position + DIRECTIONS[player_direction]
    if front_block != block_position:
        raise ValueError(
            f"Block {block_position} is not in front of player (facing direction {player_direction})"
        )
    
    # Move to the block if not already there
    current_position = state.player_position
    if current_position != block_position:
        # Calculate direction to move
        dx = block_position[0] - current_position[0]
        dy = block_position[1] - current_position[1]
        
        # Find the direction that gets us closer
        best_direction = None
        best_distance = float('inf')
        
        for direction in DIRECTIONS[1:5]:  # Skip NOOP
            proposed = current_position + direction
            if is_position_in_bounds_not_in_mob_not_colliding(state, proposed, 1):
                distance = (proposed[0] - block_position[0])**2 + (proposed[1] - block_position[1])**2
                if distance < best_distance:
                    best_distance = distance
                    best_direction = direction
        
        if best_direction is not None:
            for _ in range(max_steps):
                state = env_step(None, state, best_direction.value, None)
                if state.player_position == block_position:
                    break
                if state.player_position == block_position:
                    break
                if state.player_health <= 0:
                    raise ValueError("Player died while trying to mine block")
        
        if state.player_position != block_position:
            raise ValueError(
                f"Could not reach block {block_position} within {max_steps} steps"
            )
    
    # Mine the block
    for _ in range(max_steps):
        state = env_step(None, state, Action.DO.value, None)
        if state.player_position != block_position:
            raise ValueError("Player moved away while mining")
        if state.inventory.wood > 0:
            return True
        if state.player_health <= 0:
            raise ValueError("Player died while mining block")
    
    raise TimeoutError(f"Failed to mine block {block_position} within {max_steps} steps")
