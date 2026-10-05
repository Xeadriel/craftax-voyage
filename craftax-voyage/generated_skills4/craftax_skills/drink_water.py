# Description:
# Drinks water by moving to the closest water source and drinking until
# maximum capacity. Clears blocks and lava that are in the way.

def drink_water(state, step_func, max_steps=20):
    """
    Drinks water by moving to the closest water source.
    
    Args:
        state: Current game state
        step_func: Function that takes an action enum and returns the action to take
        max_steps: Maximum steps to drink (default 20)
    
    Returns:
        True if no error occurred
    
    Raises:
        ValueError: If no water source nearby
        ValueError: If hunger, thirst, hp, or energy falls to 3 or below
        ValueError: If enemy gets too close (1 blocks radius)
        ValueError: If max steps reached without drinking
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
    water_position = None
    min_distance = float('inf')
    
    # Find closest water source
    for y in range(state.map[state.player_level].shape[0]):
        for x in range(state.map[state.player_level].shape[1]):
            if state.map[state.player_level, x, y] in [BlockType.WATER.value, BlockType.FOUNTAIN.value]:
                dist = jnp.sum(jnp.abs(jnp.array([x, y]) - state.player_position))
                if dist < min_distance:
                    min_distance = dist
                    water_position = jnp.array([x, y])
    
    if water_position is None:
        raise ValueError("No water source found nearby")
    
    # Check initial state
    if state.player_health <= 0:
        raise ValueError("Character died at start of drink")
    
    if state.player_food <= 3 or state.player_drink <= 3 or state.player_energy <= 3:
        raise ValueError("Player health, hunger, thirst, or energy too low (<=3)")
    
    if state.player_health <= 5:
        raise ValueError("Player HP too low (<=5)")
    
    # Check for nearby enemies
    closest_enemy_distance = float('inf')
    for mob_type in [state.melee_mobs, state.ranged_mobs, state.passive_mobs]:
        for mob_index in range(mob_type.mask.shape[1]):
            if mob_type.mask[state.player_level, mob_index]:
                mob_pos = mob_type.position[state.player_level, mob_index]
                dist = jnp.sum(jnp.abs(mob_pos - state.player_position))
                closest_enemy_distance = min(closest_enemy_distance, dist)
    
    if closest_enemy_distance < 1:
        raise ValueError("Enemy too close (within 1 block)")
    
    # Move to water and drink
    while current_steps < max_steps:
        current_steps += 1
        
        # Check for enemies
        closest_enemy_distance = float('inf')
        for mob_type in [state.melee_mobs, state.ranged_mobs, state.passive_mobs]:
            for mob_index in range(mob_type.mask.shape[1]):
                if mob_type.mask[state.player_level, mob_index]:
                    mob_pos = mob_type.position[state.player_level, mob_index]
                    dist = jnp.sum(jnp.abs(mob_pos - state.player_position))
                    closest_enemy_distance = min(closest_enemy_distance, dist)
        
        if closest_enemy_distance < 1:
            raise ValueError("Enemy got too close (within 1 block)")
        
        # Check for death
        if state.player_health <= 0:
            raise ValueError("Character died during drink")
        
        # Check for low resources
        if state.player_food <= 3 or state.player_drink <= 3 or state.player_energy <= 3:
            raise ValueError("Player health, hunger, thirst, or energy too low (<=3)")
        
        # Check for low HP
        if state.player_health <= 5:
            raise ValueError("Player HP too low (<=5)")
        
        # Try to move towards water
        direction_to_water = water_position - state.player_position
        forward_direction = DIRECTIONS[state.player_direction]
        
        if direction_to_water[0] > 0:
            step_func(Action.DOWN)
        elif direction_to_water[0] < 0:
            step_func(Action.UP)
        elif direction_to_water[1] > 0:
            step_func(Action.RIGHT)
        elif direction_to_water[1] < 0:
            step_func(Action.LEFT)
        else:
            # Already at water, try to drink
            step_func(Action.DO)
        
        # Check if at water
        if is_near_block(state, BlockType.WATER.value) or is_near_block(state, BlockType.FOUNTAIN.value):
            step_func(Action.DO)
        
        # Check for death
        if state.player_health <= 0:
            raise ValueError("Character died during drink")
        
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
        
        if closest_enemy_distance < 1:
            raise ValueError("Enemy got too close (within 1 block)")
    
    return True
