# Description:
# Levels up a given attribute by checking for available XP points and leveling up.

def level_up_attribute(state, step_func, attribute, max_steps=15):
    """
    Levels up a given attribute.
    
    Args:
        state: Current game state
        step_func: Function that takes an action enum and returns the action to take
        attribute: Attribute to level up (e.g., LEVEL_UP_DEXTERITY, LEVEL_UP_STRENGTH, LEVEL_UP_INTELLIGENCE)
        max_steps: Maximum steps to level up (default 15)
    
    Returns:
        True if no error occurred
    
    Raises:
        ValueError: If no XP points available
        ValueError: If character died
        ValueError: If max steps reached without leveling up
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
        raise ValueError("Character died at start of level up")
    
    if state.player_food <= 3 or state.player_drink <= 3 or state.player_energy <= 3:
        raise ValueError("Player health, hunger, thirst, or energy too low (<=3)")
    
    if state.player_health <= 5:
        raise ValueError("Player HP too low (<=5)")
    
    # Check if we have XP
    if state.player_xp < 1:
        raise ValueError("No XP points available to level up")
    
    # Check if we can level up the specified attribute
    if attribute == Action.LEVEL_UP_DEXTERITY.value and state.player_dexterity >= 5:
        raise ValueError("Dexterity already at maximum level")
    
    if attribute == Action.LEVEL_UP_STRENGTH.value and state.player_strength >= 5:
        raise ValueError("Strength already at maximum level")
    
    if attribute == Action.LEVEL_UP_INTELLIGENCE.value and state.player_intelligence >= 5:
        raise ValueError("Intelligence already at maximum level")
    
    # Level up the attribute
    while current_steps < max_steps:
        current_steps += 1
        
        # Check for death
        if state.player_health <= 0:
            raise ValueError("Character died during level up")
        
        # Check for low resources
        if state.player_food <= 3 or state.player_drink <= 3 or state.player_energy <= 3:
            raise ValueError("Player health, hunger, thirst, or energy too low (<=3)")
        
        # Check for low HP
        if state.player_health <= 5:
            raise ValueError("Player HP too low (<=5)")
        
        # Try to level up
        step_func(attribute)
    
    return True
