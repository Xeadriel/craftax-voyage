# Description:
# Crafts an item by checking ingredient requirements, moving to the necessary
# crafting station, and crafting the item.

def craft_item(state, step_func, item_type, max_steps=15):
    """
    Crafts an item by checking ingredients and moving to crafting station.
    
    Args:
        state: Current game state
        step_func: Function that takes an action enum and returns the action to take
        item_type: Item to craft (e.g., MAKE_WOOD_PICKAXE, MAKE_STONE_PICKAXE, etc.)
        max_steps: Maximum steps to craft (default 15)
    
    Returns:
        True if no error occurred
    
    Raises:
        ValueError: If not enough items in inventory
        ValueError: If crafting station not available and cannot be built
        ValueError: If character died
        ValueError: If max steps reached without crafting
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
    
    # Check initial state
    if state.player_health <= 0:
        raise ValueError("Character died at start of craft")
    
    if state.player_food <= 3 or state.player_drink <= 3 or state.player_energy <= 3:
        raise ValueError("Player health, hunger, thirst, or energy too low (<=3)")
    
    if state.player_health <= 5:
        raise ValueError("Player HP too low (<=5)")
    
    # Check if at crafting table or furnace
    is_at_crafting_table = is_near_block(state, BlockType.CRAFTING_TABLE.value)
    is_at_furnace = is_near_block(state, BlockType.FURNACE.value)
    
    # Check if at enchantment table
    is_at_enchantment_table = is_near_block(state, BlockType.ENCHANTMENT_TABLE_FIRE.value) or is_near_block(state, BlockType.ENCHANTMENT_TABLE_ICE.value)
    
    # Check if at crafting table or furnace
    is_at_crafting_station = is_at_crafting_table or is_at_furnace
    
    # Check if at enchantment table
    is_at_enchantment_station = is_at_enchantment_table
    
    # Check if we need to move to crafting station
    if not is_at_crafting_station:
        # Find nearest crafting table or furnace
        target_position = None
        min_distance = float('inf')
        
        for y in range(state.map[state.player_level].shape[0]):
            for x in range(state.map[state.player_level].shape[1]):
                if state.map[state.player_level, x, y] in [BlockType.CRAFTING_TABLE.value, BlockType.FURNACE.value]:
                    dist = jnp.sum(jnp.abs(jnp.array([x, y]) - state.player_position))
                    if dist < min_distance:
                        min_distance = dist
                        target_position = jnp.array([x, y])
        
        if target_position is None:
            raise ValueError("No crafting station found")
        
        # Move to crafting station
        while current_steps < max_steps:
            current_steps += 1
            
            # Check for death
            if state.player_health <= 0:
                raise ValueError("Character died during craft")
            
            # Check for low resources
            if state.player_food <= 3 or state.player_drink <= 3 or state.player_energy <= 3:
                raise ValueError("Player health, hunger, thirst, or energy too low (<=3)")
            
            # Check for low HP
            if state.player_health <= 5:
                raise ValueError("Player HP too low (<=5)")
            
            # Try to move towards target
            direction_to_target = target_position - state.player_position
            forward_direction = DIRECTIONS[state.player_direction]
            
            if direction_to_target[0] > 0:
                step_func(Action.DOWN)
            elif direction_to_target[0] < 0:
                step_func(Action.UP)
            elif direction_to_target[1] > 0:
                step_func(Action.RIGHT)
            elif direction_to_target[1] < 0:
                step_func(Action.LEFT)
            else:
                step_func(Action.NOOP)
            
            # Check if at target
            if is_near_block(state, BlockType.CRAFTING_TABLE.value) or is_near_block(state, BlockType.FURNACE.value):
                break
        
        # Check if we're at crafting station
        is_at_crafting_table = is_near_block(state, BlockType.CRAFTING_TABLE.value)
        is_at_furnace = is_near_block(state, BlockType.FURNACE.value)
        is_at_crafting_station = is_at_crafting_table or is_at_furnace
    
    # Check if we need to move to enchantment table
    if is_at_enchantment_station:
        is_at_enchantment_table = is_near_block(state, BlockType.ENCHANTMENT_TABLE_FIRE.value) or is_near_block(state, BlockType.ENCHANTMENT_TABLE_ICE.value)
    else:
        # Find nearest enchantment table
        target_position = None
        min_distance = float('inf')
        
        for y in range(state.map[state.player_level].shape[0]):
            for x in range(state.map[state.player_level].shape[1]):
                if state.map[state.player_level, x, y] in [BlockType.ENCHANTMENT_TABLE_FIRE.value, BlockType.ENCHANTMENT_TABLE_ICE.value]:
                    dist = jnp.sum(jnp.abs(jnp.array([x, y]) - state.player_position))
                    if dist < min_distance:
                        min_distance = dist
                        target_position = jnp.array([x, y])
        
        if target_position is None:
            raise ValueError("No enchantment table found")
        
        # Move to enchantment table
        while current_steps < max_steps:
            current_steps += 1
            
            # Check for death
            if state.player_health <= 0:
                raise ValueError("Character died during craft")
            
            # Check for low resources
            if state.player_food <= 3 or state.player_drink <= 3 or state.player_energy <= 3:
                raise ValueError("Player health, hunger, thirst, or energy too low (<=3)")
            
            # Check for low HP
            if state.player_health <= 5:
                raise ValueError("Player HP too low (<=5)")
            
            # Try to move towards target
            direction_to_target = target_position - state.player_position
            forward_direction = DIRECTIONS[state.player_direction]
            
            if direction_to_target[0] > 0:
                step_func(Action.DOWN)
            elif direction_to_target[0] < 0:
                step_func(Action.UP)
            elif direction_to_target[1] > 0:
                step_func(Action.RIGHT)
            elif direction_to_target[1] < 0:
                step_func(Action.LEFT)
            else:
                step_func(Action.NOOP)
            
            # Check if at target
            if is_near_block(state, BlockType.ENCHANTMENT_TABLE_FIRE.value) or is_near_block(state, BlockType.ENCHANTMENT_TABLE_ICE.value):
                break
        
        # Check if we're at enchantment table
        is_at_enchantment_table = is_near_block(state, BlockType.ENCHANTMENT_TABLE_FIRE.value) or is_near_block(state, BlockType.ENCHANTMENT_TABLE_ICE.value)
    
    # Check if we're at crafting station
    is_at_crafting_table = is_near_block(state, BlockType.CRAFTING_TABLE.value)
    is_at_furnace = is_near_block(state, BlockType.FURNACE.value)
    is_at_crafting_station = is_at_crafting_table or is_at_furnace
    
    # Check if we're at enchantment table
    is_at_enchantment_table = is_near_block(state, BlockType.ENCHANTMENT_TABLE_FIRE.value) or is_near_block(state, BlockType.ENCHANTMENT_TABLE_ICE.value)
    
    # Check if we need to build crafting table or furnace
    if not is_at_crafting_station:
        # Check if we can build crafting table
        if state.inventory.wood >= 2:
            # Find valid placement spot
            for direction in CLOSE_BLOCKS:
                block_position = state.player_position + direction
                if is_position_in_bounds_not_in_mob_not_colliding(
                    state, block_position, COLLISION_LAND_CREATURE
                ):
                    step_func(Action.PLACE_TABLE)
                    break
        
        # Check if we can build furnace
        if state.inventory.stone > 0:
            # Find valid placement spot
            for direction in CLOSE_BLOCKS:
                block_position = state.player_position + direction
                if is_position_in_bounds_not_in_mob_not_colliding(
                    state, block_position, COLLISION_LAND_CREATURE
                ):
                    step_func(Action.PLACE_FURNACE)
                    break
    
    # Check if we're at crafting station
    is_at_crafting_table = is_near_block(state, BlockType.CRAFTING_TABLE.value)
    is_at_furnace = is_near_block(state, BlockType.FURNACE.value)
    is_at_crafting_station = is_at_crafting_table or is_at_furnace
    
    # Check if we're at enchantment table
    is_at_enchantment_table = is_near_block(state, BlockType.ENCHANTMENT_TABLE_FIRE.value) or is_near_block(state, BlockType.ENCHANTMENT_TABLE_ICE.value)
    
    # Craft the item
    while current_steps < max_steps:
        current_steps += 1
        
        # Check for death
        if state.player_health <= 0:
            raise ValueError("Character died during craft")
        
        # Check for low resources
        if state.player_food <= 3 or state.player_drink <= 3 or state.player_energy <= 3:
            raise ValueError("Player health, hunger, thirst, or energy too low (<=3)")
        
        # Check for low HP
        if state.player_health <= 5:
            raise ValueError("Player HP too low (<=5)")
        
        # Try to craft
        step_func(item_type)
    
    return True
