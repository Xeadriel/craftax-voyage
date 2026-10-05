# Description:
# Fights an enemy type or passive mob via melee attacks. Decides when to use
# melee attacks, move in, retreat, bait, reposition, and dodge enemy projectiles.

def fight_melee(state, step_func, enemy_type=None, max_steps=20):
    """
    Fights an enemy type or passive mob via melee attacks.
    
    Args:
        state: Current game state
        step_func: Function that takes an action enum and returns the action to take
        enemy_type: Optional MobType to target (0=passive, 1=melee, 2=ranged)
        max_steps: Maximum steps to fight (default 20)
    
    Returns:
        True if enemy defeated or no error occurred
    
    Raises:
        ValueError: If hunger, thirst, hp, or energy falls to 3 or below
        ValueError: If max steps reached without defeating enemy
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
    enemy_defeated = False
    
    # Check initial state
    if state.player_health <= 0:
        raise ValueError("Character died at start of fight")
    
    if state.player_food <= 3 or state.player_drink <= 3 or state.player_energy <= 3:
        raise ValueError("Player health, hunger, thirst, or energy too low (<=3)")
    
    if state.player_health <= 5:
        raise ValueError("Player HP too low (<=5)")
    
    # Find closest enemy of the specified type
    closest_enemy = None
    closest_enemy_distance = float('inf')
    
    if enemy_type is not None:
        for mob_type in [state.melee_mobs, state.ranged_mobs, state.passive_mobs]:
            for mob_index in range(mob_type.mask.shape[1]):
                if mob_type.mask[state.player_level, mob_index]:
                    mob_pos = mob_type.position[state.player_level, mob_index]
                    dist = jnp.sum(jnp.abs(mob_pos - state.player_position))
                    
                    if mob_type.type_id[state.player_level, mob_index] == enemy_type:
                        if dist < closest_enemy_distance:
                            closest_enemy_distance = dist
                            closest_enemy = mob_index
    else:
        # Find any enemy
        for mob_type in [state.melee_mobs, state.ranged_mobs, state.passive_mobs]:
            for mob_index in range(mob_type.mask.shape[1]):
                if mob_type.mask[state.player_level, mob_index]:
                    mob_pos = mob_type.position[state.player_level, mob_index]
                    dist = jnp.sum(jnp.abs(mob_pos - state.player_position))
                    
                    if dist < closest_enemy_distance:
                        closest_enemy_distance = dist
                        closest_enemy = mob_index
    
    if closest_enemy is None:
        raise ValueError("No enemy found to fight")
    
    # Get enemy position
    enemy_position = state.melee_mobs.position[state.player_level, closest_enemy]
    
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
        
        if closest_enemy_distance < 3:
            raise ValueError("Enemy got too close (within 3 blocks)")
        
        # Check for death
        if state.player_health <= 0:
            raise ValueError("Character died during fight")
        
        # Check for low resources
        if state.player_food <= 3 or state.player_drink <= 3 or state.player_energy <= 3:
            raise ValueError("Player health, hunger, thirst, or energy too low (<=3)")
        
        # Check for low HP
        if state.player_health <= 5:
            raise ValueError("Player HP too low (<=5)")
        
        # Check if enemy defeated
        if state.melee_mobs.health[state.player_level, closest_enemy] <= 0:
            enemy_defeated = True
            break
        
        # Check if enemy is too far
        if closest_enemy_distance > 10:
            # Move towards enemy
            direction_to_enemy = enemy_position - state.player_position
            if direction_to_enemy[0] > 0:
                step_func(Action.DOWN)
            elif direction_to_enemy[0] < 0:
                step_func(Action.UP)
            elif direction_to_enemy[1] > 0:
                step_func(Action.RIGHT)
            elif direction_to_enemy[1] < 0:
                step_func(Action.LEFT)
            else:
                step_func(Action.NOOP)
        else:
            # Check if enemy is attacking
            is_attacking = state.melee_mobs.attack_cooldown[state.player_level, closest_enemy] <= 0
            is_close = closest_enemy_distance <= 1
            
            if is_attacking and is_close:
                # Dodge by moving away
                step_func(Action.NOOP)
            else:
                # Attack if close enough
                if is_close:
                    step_func(Action.DO)
                else:
                    # Move towards enemy
                    direction_to_enemy = enemy_position - state.player_position
                    if direction_to_enemy[0] > 0:
                        step_func(Action.DOWN)
                    elif direction_to_enemy[0] < 0:
                        step_func(Action.UP)
                    elif direction_to_enemy[1] > 0:
                        step_func(Action.RIGHT)
                    elif direction_to_enemy[1] < 0:
                        step_func(Action.LEFT)
                    else:
                        step_func(Action.NOOP)
        
        # Check for death
        if state.player_health <= 0:
            raise ValueError("Character died during fight")
        
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
    
    if not enemy_defeated:
        raise ValueError(f"Max steps ({max_steps}) reached without defeating enemy")
    
    return True
