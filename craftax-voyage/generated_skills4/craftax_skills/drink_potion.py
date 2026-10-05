# Description:
# Drinks a potion by checking for potions in inventory and drinking the potion.

def drink_potion(state, step_func, potion_type, max_steps=15):
    """
    Drinks a potion.
    
    Args:
        state: Current game state
        step_func: Function that takes an action enum and returns the action to take
        potion_type: Potion type to drink (e.g., DRINK_POTION_RED, DRINK_POTION_GREEN, etc.)
        max_steps: Maximum steps to drink (default 15)
    
    Returns:
        True if no error occurred
    
    Raises:
        ValueError: If no potions of given type in inventory
        ValueError: If character died
        ValueError: If max steps reached without drinking
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
        raise ValueError("Character died at start of drink")
    
    if state.player_food <= 3 or state.player_drink <= 3 or state.player_energy <= 3:
        raise ValueError("Player health, hunger, thirst, or energy too low (<=3)")
    
    if state.player_health <= 5:
        raise ValueError("Player HP too low (<=5)")
    
    # Check if we have the potion
    if potion_type == Action.DRINK_POTION_RED.value and state.inventory.potions[0] <= 0:
        raise ValueError("No red potions in inventory")
    
    if potion_type == Action.DRINK_POTION_GREEN.value and state.inventory.potions[1] <= 0:
        raise ValueError("No green potions in inventory")
    
    if potion_type == Action.DRINK_POTION_BLUE.value and state.inventory.potions[2] <= 0:
        raise ValueError("No blue potions in inventory")
    
    if potion_type == Action.DRINK_POTION_PINK.value and state.inventory.potions[3] <= 0:
        raise ValueError("No pink potions in inventory")
    
    if potion_type == Action.DRINK_POTION_CYAN.value and state.inventory.potions[4] <= 0:
        raise ValueError("No cyan potions in inventory")
    
    if potion_type == Action.DRINK_POTION_YELLOW.value and state.inventory.potions[5] <= 0:
        raise ValueError("No yellow potions in inventory")
    
    # Try to drink potion
    while current_steps < max_steps:
        current_steps += 1
        
        # Check for death
        if state.player_health <= 0:
            raise ValueError("Character died during drink")
        
        # Check for low resources
        if state.player_food <= 3 or state.player_drink <= 3 or state.player_energy <= 3:
            raise ValueError("Player health, hunger, thirst, or energy too low (<=3)")
        
        # Check for low HP
        if state.player_health <= 5:
            raise ValueError("Player HP too low (<=5)")
        
        # Try to drink potion
        step_func(potion_type)
    
    return True
