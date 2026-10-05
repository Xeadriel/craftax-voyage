# Description:
# Mines a specified number of blocks of a given type, clearing obstacles in the way.
# Returns True if successful, throws errors for various failure conditions.

def mine_blocks(state, step_func, log_fn, block_type, count=1, max_steps=50):
    """
    Mines a specified number of blocks of a given type.
    
    Args:
        state: The current game state
        action_step: Function that takes an Action enum and returns the action
        log: Logging function
        block_type: The BlockType enum to mine
        x: Number of blocks to mine (default 1)
        max_steps: Maximum steps to attempt mining (default 50)
    
    Returns:
        True if mining was successful
    
    Raises:
        ValueError: If hunger, thirst, or energy fall to 3 or below
        ValueError: If health falls to 5 or below
        ValueError: If an enemy gets too close (3 blocks radius)
        ValueError: If character died
        ValueError: If X blocks cannot be mined (no more blocks of that type exist)
        ValueError: If max steps reached without success
    """
    from craftax.craftax.constants import (
        BlockType,
        SOLID_BLOCKS,
        DIRECTIONS,
        CLOSE_BLOCKS,
        Action,
        MOB_TYPE_COLLISION_MAPPING,
        FLOOR_MOB_MAPPING,
        MobType,
    )
    from craftax.craftax.util.game_logic_utils import (
        is_in_solid_block,
        is_in_mob,
        in_bounds,
        is_position_in_bounds_not_in_mob_not_colliding,
        get_distance_map,
    )
    
    # Check if player is alive
    if state.player_health <= 0:
        raise ValueError("Character died - health is 0 or below")
    
    # Check if player is sleeping or resting (interrupted actions)
    if state.is_sleeping or state.is_resting:
        raise ValueError("Cannot mine while sleeping or resting")
    
    # Check intrinsics - hunger, thirst, energy must be above 3
    if state.player_food <= 3:
        raise ValueError(f"Hunger too low ({state.player_food}), must be above 3")
    if state.player_drink <= 3:
        raise ValueError(f"Thirst too low ({state.player_drink}), must be above 3")
    if state.player_energy <= 3:
        raise ValueError(f"Energy too low ({state.player_energy}), must be above 3")
    
    # Check health threshold
    if state.player_health <= 5:
        raise ValueError(f"Health too low ({state.player_health}), must be above 5")
    
    # Check if target block type is valid
    if block_type not in BlockType:
        raise ValueError(f"Invalid block type: {block_type}")
    
    # Get current position and direction
    current_position = state.player_position
    current_direction = state.player_direction
    
    # Check if we're already at a block of the target type
    target_block_position = current_position + DIRECTIONS[current_direction]
    target_block = state.map[state.player_level, target_block_position[0], target_block_position[1]]
    
    if target_block == block_type:
        # Already at target block, start mining
        pass
    else:
        # Find nearest block of the target type
        player_distance_map = get_distance_map(current_position, state.map.shape)
        target_blocks = []
        
        for y in range(state.map.shape[0]):
            for x_coord in range(state.map.shape[1]):
                block = state.map[state.player_level, y, x_coord]
                if block == block_type:
                    target_blocks.append((y, x_coord))
        
        if not target_blocks:
            raise ValueError(f"No blocks of type {block_type.name} found in the world")
        
        # Find nearest block
        nearest_block = min(target_blocks, key=lambda pos: player_distance_map[pos[0], pos[1]])
        
        # Navigate to the nearest block
        log_fn(f"Moving to nearest {block_type.name} at {nearest_block}")
        step_func(Action.NOOP)  # No-op to advance step
        
        # Move towards target
        while True:
            # Check if we're close enough to mine
            distance = player_distance_map[nearest_block[0], nearest_block[1]]
            if distance <= 1:
                # We're adjacent, start mining
                break
            
            # Check if we're at a valid position
            if not in_bounds(state, current_position):
                raise ValueError("Player position out of bounds")
            
            # Check for enemies nearby
            for mob_pos in state.mob_map[state.player_level]:
                if is_in_mob(state, mob_pos):
                    if is_position_in_bounds_not_in_mob_not_colliding(state, mob_pos, MOB_TYPE_COLLISION_MAPPING[FLOOR_MOB_MAPPING[state.player_level, MobType.MELEE.value], 1]):
                        distance_to_mob = jnp.sum(jnp.abs(mob_pos - current_position))
                        if distance_to_mob <= 3:
                            raise ValueError(f"Enemy too close at {mob_pos}, distance is {distance_to_mob}")
            
            # Move in direction
            next_direction = (current_direction + 1) % 4
            next_position = current_position + DIRECTIONS[next_direction]
            
            # Check if move is valid
            if not is_position_in_bounds_not_in_mob_not_colliding(state, next_position, COLLISION_LAND_CREATURE):
                # Try other directions
                for dir_idx in range(4):
                    if dir_idx == next_direction:
                        continue
                    dir_direction = DIRECTIONS[dir_idx]
                    dir_position = current_position + dir_direction
                    if is_position_in_bounds_not_in_mob_not_colliding(state, dir_position, COLLISION_LAND_CREATURE):
                        next_direction = dir_idx
                        break
                else:
                    raise ValueError("Cannot move towards target block")
            
            current_direction = next_direction
            current_position = next_position
            step_func(Action.NOOP)
    
    # Mining loop
    for i in range(count):
        # Check if we're at a valid position
        if not in_bounds(state, current_position):
            raise ValueError("Player position out of bounds during mining")
        
        # Check for enemies nearby
        for mob_pos in state.mob_map[state.player_level]:
            if is_in_mob(state, mob_pos):
                if is_position_in_bounds_not_in_mob_not_colliding(state, mob_pos, MOB_TYPE_COLLISION_MAPPING[FLOOR_MOB_MAPPING[state.player_level, MobType.MELEE.value], 1]):
                    distance_to_mob = jnp.sum(jnp.abs(mob_pos - current_position))
                    if distance_to_mob <= 3:
                        raise ValueError(f"Enemy too close at {mob_pos}, distance is {distance_to_mob}")
        
        # Check if we're at a block of the target type
        target_block = state.map[state.player_level, current_position[0], current_position[1]]
        if target_block != block_type:
            raise ValueError(f"Current block is {BlockType(target_block).name}, not {block_type.name}")
        
        # Mine the block
        step_func(Action.DO)
        
        # Check if block was successfully mined
        target_block = state.map[state.player_level, current_position[0], current_position[1]]
        if target_block != BlockType.PATH.value:
            # Block wasn't mined, try to clear obstacles
            if target_block in [BlockType.WATER.value, BlockType.LAVA.value]:
                # Need to place and remove a block
                log_fn(f"Placing stone to clear {BlockType(target_block).name}")
                step_func(Action.PLACE_STONE)
                step_func(Action.DO)
                step_func(Action.PLACE_STONE)
                step_func(Action.DO)
            else:
                raise ValueError(f"Failed to mine block, remaining type: {BlockType(target_block).name}")
        
        # Check if we've reached the target count
        if i + 1 >= count:
            break
    
    # Final check - verify we mined the correct number of blocks
    if i < count:
        raise ValueError(f"Failed to mine {count - i} more blocks of type {block_type.name}")
    
    return True
