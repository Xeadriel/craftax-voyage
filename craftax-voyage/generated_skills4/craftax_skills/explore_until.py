# Description:
# Explores the environment until a specified target block or entity is found,
# or until a maximum number of steps is reached. Clears obstacles in the way
# by mining blocks or placing/removing water/lava blocks.

def explore_until(state, step_func, target_block_type=None, max_steps=100):
    """
    Explores until finding a target block or entity, or reaching max steps.
    
    Args:
        state: Current game state
        step_func: Function that takes an action enum and returns the action to take
        target_block_type: Optional BlockType to search for (e.g., CHEST, FOUNTAIN)
        max_steps: Maximum steps to explore (default 100)
    
    Returns:
        True if target found or no error occurred
    
    Raises:
        ValueError: If hunger, thirst, or energy falls to 3 or below
        ValueError: If HP falls to 5 or below
        ValueError: If enemy gets too close (3 blocks radius)
        ValueError: If max steps reached without finding target
        ValueError: If character died
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
    found_target = False
    
    # Check initial state
    if state.player_health <= 0:
        raise ValueError("Character died at start of exploration")
    
    if state.player_food <= 3 or state.player_drink <= 3 or state.player_energy <= 3:
        raise ValueError("Player health, hunger, thirst, or energy too low (<=3)")
    
    # Check for nearby enemies
    closest_enemy_distance = float('inf')
    for mob_type in [state.melee_mobs, state.ranged_mobs, state.passive_mobs]:
        for mob_index in range(mob_type.mask.shape[1]):
            if mob_type.mask[state.player_level, mob_index]:
                mob_pos = mob_type.position[state.player_level, mob_index]
                dist = jnp.sum(jnp.abs(mob_pos - state.player_position))
                closest_enemy_distance = min(closest_enemy_distance, dist)
    
    if closest_enemy_distance < 3:
        raise ValueError("Enemy too close (within 3 blocks)")
    
    while current_steps < max_steps:
        current_steps += 1
        
        # Check for enemies again
        closest_enemy_distance = float('inf')
        for mob_type in [state.melee_mobs, state.ranged_mobs, state.passive_mobs]:
            for mob_index in range(mob_type.mask.shape[1]):
                if mob_type.mask[state.player_level, mob_index]:
                    mob_pos = mob_type.position[state.player_level, mob_index]
                    dist = jnp.sum(jnp.abs(mob_pos - state.player_position))
                    closest_enemy_distance = min(closest_enemy_distance, dist)
        
        if closest_enemy_distance < 3:
            raise ValueError("Enemy got too close (within 3 blocks)")
        
        # Check for death
        if state.player_health <= 0:
            raise ValueError("Character died during exploration")
        
        # Check for low resources
        if state.player_food <= 3 or state.player_drink <= 3 or state.player_energy <= 3:
            raise ValueError("Player health, hunger, thirst, or energy too low (<=3)")
        
        # Check for low HP
        if state.player_health <= 5:
            raise ValueError("Player HP too low (<=5)")
        
        # Check if target found
        if target_block_type is not None:
            if is_near_block(state, target_block_type.value):
                found_target = True
                break
        
        # Try to move forward
        forward_direction = DIRECTIONS[state.player_direction]
        forward_position = state.player_position + forward_direction
        
        # Check if forward position is valid
        if is_position_in_bounds_not_in_mob_not_colliding(
            state, forward_position, COLLISION_LAND_CREATURE
        ):
            # Try to move forward
            step_func(Action.UP)
        else:
            # Try to move sideways
            left_direction = DIRECTIONS[(state.player_direction + 3) % 4]
            right_direction = DIRECTIONS[(state.player_direction + 1) % 4]
            
            left_position = state.player_position + left_direction
            right_position = state.player_position + right_direction
            
            if is_position_in_bounds_not_in_mob_not_colliding(
                state, left_position, COLLISION_LAND_CREATURE
            ):
                step_func(Action.LEFT)
            elif is_position_in_bounds_not_in_mob_not_colliding(
                state, right_position, COLLISION_LAND_CREATURE
            ):
                step_func(Action.RIGHT)
            else:
                # Try to move backward
                backward_direction = DIRECTIONS[(state.player_direction + 2) % 4]
                backward_position = state.player_position + backward_direction
                
                if is_position_in_bounds_not_in_mob_not_colliding(
                    state, backward_position, COLLISION_LAND_CREATURE
                ):
                    step_func(Action.DOWN)
                else:
                    # Try to place and mine water/lava if in the way
                    if is_in_solid_block(state, forward_position):
                        # Try to place stone on water/lava
                        step_func(Action.PLACE_STONE)
                    else:
                        step_func(Action.NOOP)
        
        # Check if target found after movement
        if target_block_type is not None:
            if is_near_block(state, target_block_type.value):
                found_target = True
                break
        
        # Check for death
        if state.player_health <= 0:
            raise ValueError("Character died during exploration")
        
        # Check for low resources
        if state.player_food <= 3 or state.player_drink <= 3 or state.player_energy <= 3:
            raise ValueError("Player health, hunger, thirst, or energy too low (<=3)")
        
        # Check for low HP
        if state.player_health <= 5:
            raise ValueError("Player HP too low (<=5)")
        
        # Check for enemies
        closest_enemy_distance = float('inf')
        for mob_type in [state.melee_mobs, state.ranged_mobs, state.passive_mobs]:
            for mob_index in range(mob_type.mask.shape[1]):
                if mob_type.mask[state.player_level, mob_index]:
                    mob_pos = mob_type.position[state.player_level, mob_index]
                    dist = jnp.sum(jnp.abs(mob_pos - state.player_position))
                    closest_enemy_distance = min(closest_enemy_distance, dist)
        
        if closest_enemy_distance < 3:
            raise ValueError("Enemy got too close (within 3 blocks)")
    
    if not found_target:
        raise ValueError(f"Max steps ({max_steps}) reached without finding target")
    
    return True
