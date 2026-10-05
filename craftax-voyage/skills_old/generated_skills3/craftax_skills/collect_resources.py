# Description:
# Collects specified resources from the environment.
# Returns True if successfully collected, False otherwise.
# Assumes resources are within 10 blocks of the player.

from craftax.craftax.constants import (
    Action,
    BlockType,
    SOLID_BLOCKS,
    DIRECTIONS,
)
from craftax.craftax.util.game_logic_utils import (
    is_position_in_bounds_not_in_mob_not_colliding,
    is_in_solid_block,
)


def collect_resources(env_step, state, resources, max_steps=50):
    """
    Collects specified resources from the environment.
    
    Args:
        env_step: The environment step function
        state: Current environment state
        resources: List of resource names to collect (e.g., ["coal", "iron", "diamond"])
        max_steps: Maximum number of steps to attempt collection
    
    Returns:
        True if successfully collected, False otherwise
    """
    # Check if player has the required tool level
    pickaxe_level = state.inventory.pickaxe
    
    for resource in resources:
        # Find the resource
        found = False
        for _ in range(max_steps):
            # Check all adjacent blocks
            for direction in DIRECTIONS[1:5]:
                proposed = state.player_position + direction
                if is_position_in_bounds_not_in_mob_not_colliding(state, proposed, 1):
                    block = state.map[state.player_level][proposed[0], proposed[1]]
                    if block == BlockType.COAL.value:
                        if pickaxe_level >= 1:
                            # Mine the block
                            state = env_step(None, state, Action.DO.value, None)
                            found = True
                            break
                    elif block == BlockType.IRON.value:
                        if pickaxe_level >= 2:
                            state = env_step(None, state, Action.DO.value, None)
                            found = True
                            break
                    elif block == BlockType.DIAMOND.value:
                        if pickaxe_level >= 3:
                            state = env_step(None, state, Action.DO.value, None)
                            found = True
                            break
                    elif block == BlockType.SAPPHIRE.value or block == BlockType.RUBY.value:
                        if pickaxe_level >= 4:
                            state = env_step(None, state, Action.DO.value, None)
                            found = True
                            break
            
            if found:
                break
            
            # Move towards resource
            best_direction = None
            best_distance = float('inf')
            
            for direction in DIRECTIONS[1:5]:
                proposed = state.player_position + direction
                if is_position_in_bounds_not_in_mob_not_colliding(state, proposed, 1):
                    distance = (proposed[0] - state.player_position[0])**2 + (proposed[1] - state.player_position[1])**2
                    if distance < best_distance:
                        best_distance = distance
                        best_direction = direction
            
            if best_direction is None:
                raise ValueError(f"Cannot reach {resource}")
            
            state = env_step(None, state, best_direction.value, None)
        
        if not found:
            raise ValueError(f"Could not find {resource} within {max_steps} steps")
    
    return True
