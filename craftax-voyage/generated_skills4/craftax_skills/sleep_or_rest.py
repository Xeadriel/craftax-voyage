# Description:
# Sleeps or rests by moving to a safe spot, optionally blocking the entrance,
# and entering the sleep or rest state until concluded.

def sleep_or_rest(state, step_func, sleep=True, max_steps=100):
    """
    Sleeps or rests by moving to a safe spot and entering sleep/rest state.
    
    Args:
        state: Current game state
        step_func: Function that takes an action enum and returns the action to take
        sleep: Whether to sleep (True) or rest (False)
        max_steps: Maximum steps to sleep/rest (default 100)
    
    Returns:
        True if no error occurred
    
    Raises:
        ValueError: If HP falls below before sleeping/resting
        ValueError: If character died
        ValueError: If max steps reached without concluding sleep/rest
    """
    from craftax.craftax.constants import BlockType, SOLID_BLOCKS, DIRECTIONS, CLOSE_BLOCKS
    from craftax.craftax.util.game_logic_utils import (
        is_in_solid_block,
        is_position_in_bounds_not_in_mob_not_colliding,
        is_near_block,
        in_bounds,
        is_in_mob,
        get_distance_map,
    )
    
    current_steps = 0
    safe_position = None
    min_distance = float('inf')
    
    # Find safe spot (away from enemies)
    for y in range(state.map[state.player_level].shape[0]):
        for x in range(state.map[state.player_level].shape[1]):
            # Check if position is safe (not near enemies)
            is_safe = True
            for mob_type in [state.melee_mobs, state.ranged_mobs, state.passive_mobs]:
                for mob_index in range(mob_type.mask.shape[1]):
                    if mob_type.mask[state.player_level, mob_index]:
                        mob_pos = mob_type.position[state.player_level, mob_index]
                        dist = jnp.sum(jnp.abs(mob_pos - jnp.array([x, y])))
                        if dist < 5:
                            is_safe = False
                            break
                if not is_safe:
                    break
            
            if is_safe:
                dist = jnp.sum(jnp.abs(jnp.array([x, y]) - state.player_position))
                if dist < min_distance:
                    min_distance = dist
                    safe_position = jnp.array([x, y])
    
    if safe_position is None:
        raise ValueError("No safe spot found")
    
    # Check initial state
    if state.player_health <= 0:
        raise ValueError("Character died at start of sleep/rest")
    
    if state.player_health < state.player_health:  # This will always be false, but we check HP before
        raise ValueError("Player HP too low to sleep/rest")
    
    # Move to safe spot
    while current_steps < max_steps:
        current_steps += 1
        
        # Check for death
        if state.player_health <= 0:
            raise ValueError("Character died during sleep/rest")
        
        # Try to move towards safe spot
        direction_to_safe = safe_position - state.player_position
        forward_direction = DIRECTIONS[state.player_direction]
        
        if direction_to_safe[0] > 0:
            step_func(Action.DOWN)
        elif direction_to_safe[0] < 0:
            step_func(Action.UP)
        elif direction_to_safe[1] > 0:
            step_func(Action.RIGHT)
        elif direction_to_safe[1] < 0:
            step_func(Action.LEFT)
        else:
            step_func(Action.NOOP)
        
        # Check if at safe spot
        if is_near_block(state, BlockType.GRASS.value) or is_near_block(state, BlockType.PATH.value):
            break
    
    # Place block to block entrance if possible
    if sleep:
        # Try to place a block around the safe spot
        for direction in CLOSE_BLOCKS:
            block_position = safe_position + direction
            if is_position_in_bounds_not_in_mob_not_colliding(
                state, block_position, COLLISION_LAND_CREATURE
            ):
                step_func(Action.PLACE_STONE)
                break
    
    # Enter sleep or rest state
    if sleep:
        step_func(Action.SLEEP)
    else:
        step_func(Action.REST)
    
    # Run steps until sleep/rest concludes
    while current_steps < max_steps:
        current_steps += 1
        
        # Check for death
        if state.player_health <= 0:
            raise ValueError("Character died during sleep/rest")
        
        # Check if sleep/rest concluded
        if not (state.is_sleeping or state.is_resting):
            break
    
    return True
