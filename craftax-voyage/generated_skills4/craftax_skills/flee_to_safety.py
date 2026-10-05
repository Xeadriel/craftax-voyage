# Description:
# Flee to relative safety by avoiding enemies, dodging projectiles, and building
# distance. Can mine blocks and remove water that are in the way.

def flee_to_safety(state, step_func, max_steps=20):
    """
    Flee to relative safety by avoiding enemies and building distance.
    
    Args:
        state: Current game state
        step_func: Function that takes an action enum and returns the action to take
        max_steps: Maximum steps to flee (default 20)
    
    Returns:
        True if no error occurred
    
    Raises:
        ValueError: If hunger, thirst, hp, or energy falls to 3 or below
        ValueError: If max steps reached without establishing safety
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
    safe_distance = 0
    
    # Check initial state
    if state.player_health <= 0:
        raise ValueError("Character died at start of flee")
    
    if state.player_food <= 3 or state.player_drink <= 3 or state.player_energy <= 3:
        raise ValueError("Player health, hunger, thirst, or energy too low (<=3)")
    
    if state.player_health <= 5:
        raise ValueError("Player HP too low (<=5)")
    
    # Find closest enemy
    closest_enemy = None
    closest_enemy_distance = float('inf')
    
    for mob_type in [state.melee_mobs, state.ranged_mobs, state.passive_mobs]:
        for mob_index in range(mob_type.mask.shape[1]):
            if mob_type.mask[state.player_level, mob_index]:
                mob_pos = mob_type.position[state.player_level, mob_index]
                dist = jnp.sum(jnp.abs(mob_pos - state.player_position))
                
                if dist < closest_enemy_distance:
                    closest_enemy_distance = dist
                    closest_enemy = mob_index
    
    if closest_enemy is not None:
        closest_enemy_position = state.melee_mobs.position[state.player_level, closest_enemy]
        closest_enemy_distance = jnp.sum(jnp.abs(closest_enemy_position - state.player_position))
    
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
        
        # Check if safe
        if closest_enemy_distance >= 5 or closest_enemy is None:
            safe_distance = closest_enemy_distance
            break
        
        # Check for death
        if state.player_health <= 0:
            raise ValueError("Character died during flee")
        
        # Check for low resources
        if state.player_food <= 3 or state.player_drink <= 3 or state.player_energy <= 3:
            raise ValueError("Player health, hunger, thirst, or energy too low (<=3)")
        
        # Check for low HP
        if state.player_health <= 5:
            raise ValueError("Player HP too low (<=5)")
        
        # Move away from enemy
        if closest_enemy is not None:
            enemy_position = state.melee_mobs.position[state.player_level, closest_enemy]
            direction_away = enemy_position - state.player_position
            direction_away = -direction_away
            
            if direction_away[0] > 0:
                step_func(Action.UP)
            elif direction_away[0] < 0:
                step_func(Action.DOWN)
            elif direction_away[1] > 0:
                step_func(Action.LEFT)
            elif direction_away[1] < 0:
                step_func(Action.RIGHT)
            else:
                step_func(Action.NOOP)
        else:
            # No enemy, just move randomly
            step_func(Action.NOOP)
        
        # Check if safe
        closest_enemy_distance = float('inf')
        for mob_type in [state.melee_mobs, state.ranged_mobs, state.passive_mobs]:
            for mob_index in range(mob_type.mask.shape[1]):
                if mob_type.mask[state.player_level, mob_index]:
                    mob_pos = mob_type.position[state.player_level, mob_index]
                    dist = jnp.sum(jnp.abs(mob_pos - state.player_position))
                    closest_enemy_distance = min(closest_enemy_distance, dist)
        
        if closest_enemy_distance >= 5 or closest_enemy is None:
            safe_distance = closest_enemy_distance
            break
        
        # Check for death
        if state.player_health <= 0:
            raise ValueError("Character died during flee")
        
        # Check for low resources
        if state.player_food <= 3 or state.player_drink <= 3 or state.player_energy <= 3:
            raise ValueError("Player health, hunger, thirst, or energy too low (<=3)")
        
        # Check for low HP
        if state.player_health <= 5:
            raise ValueError("Player HP too low (<=5)")
    
    if safe_distance < 5:
        raise ValueError(f"Max steps ({max_steps}) reached without establishing safety (distance: {safe_distance})")
    
    return True
