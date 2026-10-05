# Description:
# Mines a specified number of blocks of a given type. Moves to the nearest
# block of the given type and mines it repeatedly. Clears obstacles in the way.

def mine_blocks(state, step_func, block_type, count=1, max_steps=50):
    """
    Mines a specified number of blocks of a given type.
    
    Args:
        state: Current game state
        step_func: Function that takes an action enum and returns the action to take
        block_type: BlockType to mine (e.g., STONE, COAL, IRON, DIAMOND)
        count: Number of blocks to mine (default 1)
        max_steps: Maximum steps to mine (default 50)
    
    Returns:
        True if all blocks mined or no error occurred
    
    Raises:
        ValueError: If hunger, thirst, or energy falls to 3 or below
        ValueError: If HP falls to 5 or below
        ValueError: If enemy gets too close (3 blocks radius)
        ValueError: If max steps reached without mining enough blocks
        ValueError: If character died
    """
    from craftax.craftax.constants import BlockType, SOLID_BLOCKS, DIRECTIONS, CLOSE_BLOCKS
    from craftax.craftax.util.game_logic_utils import (
        is_in_solid_block,
        is_position_in_bounds_not_in_mob_not_colliding,
        is_near_block,
        in_bounds,
        is_in_mob,
    )
    
    mined_count = 0
    current_steps = 0
    
    # Check initial state
    if state.player_health <= 0:
        raise ValueError("Character died at start of mining")
    
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
    
    if closest_enemy_distance < 3:
        raise ValueError("Enemy too close (within 3 blocks)")
    
    # Find nearest block of the given type
    target_position = None
    min_distance = float('inf')
    
    for y in range(state.map[state.player_level].shape[0]):
        for x in range(state.map[state.player_level].shape[1]):
            if state.map[state.player_level, x, y] == block_type.value:
                dist = jnp.sum(jnp.abs(jnp.array([x, y]) - state.player_position))
                if dist < min_distance:
                    min_distance = dist
                    target_position = jnp.array([x, y])
    
    if target_position is None:
        raise ValueError(f"No {block_type.name} blocks found in the world")
    
    # Move to the target block
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
            raise ValueError("Character died during mining")
        
        # Check for low resources
        if state.player_food <= 3 or state.player_drink <= 3 or state.player_energy <= 3:
            raise ValueError("Player health, hunger, thirst, or energy too low (<=3)")
        
        # Check for low HP
        if state.player_health <= 5:
            raise ValueError("Player HP too low (<=5)")
        
        # Try to move towards target
        direction_to_target = target_position - state.player_position
        forward_direction = DIRECTIONS[state.player_direction]
        
        # Calculate which direction to move
        if direction_to_target[0] > 0:
            step_func(Action.DOWN)
        elif direction_to_target[0] < 0:
            step_func(Action.UP)
        elif direction_to_target[1] > 0:
            step_func(Action.RIGHT)
        elif direction_to_target[1] < 0:
            step_func(Action.LEFT)
        else:
            # Already at target, try to mine
            step_func(Action.DO)
        
        # Check if target found
        if target_position is not None:
            if is_near_block(state, block_type.value):
                # Try to mine
                step_func(Action.DO)
        
        # Check for death
        if state.player_health <= 0:
            raise ValueError("Character died during mining")
        
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
    
    if mined_count < count:
        raise ValueError(f"Max steps ({max_steps}) reached without mining {count} blocks")
    
    return True
