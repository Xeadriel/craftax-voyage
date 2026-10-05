# Description:
# Reads a book by checking for books in inventory and reading the book.

def read_book(state, step_func, max_steps=15):
    """
    Reads a book.
    
    Args:
        state: Current game state
        step_func: Function that takes an action enum and returns the action to take
        max_steps: Maximum steps to read (default 15)
    
    Returns:
        True if no error occurred
    
    Raises:
        ValueError: If no books in inventory
        ValueError: If character died
        ValueError: If max steps reached without reading
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
        raise ValueError("Character died at start of read")
    
    if state.player_food <= 3 or state.player_drink <= 3 or state.player_energy <= 3:
        raise ValueError("Player health, hunger, thirst, or energy too low (<=3)")
    
    if state.player_health <= 5:
        raise ValueError("Player HP too low (<=5)")
    
    # Check if we have books
    if state.inventory.books <= 0:
        raise ValueError("No books in inventory")
    
    # Try to read book
    while current_steps < max_steps:
        current_steps += 1
        
        # Check for death
        if state.player_health <= 0:
            raise ValueError("Character died during read")
        
        # Check for low resources
        if state.player_food <= 3 or state.player_drink <= 3 or state.player_energy <= 3:
            raise ValueError("Player health, hunger, thirst, or energy too low (<=3)")
        
        # Check for low HP
        if state.player_health <= 5:
            raise ValueError("Player HP too low (<=5)")
        
        # Try to read book
        step_func(Action.READ_BOOK)
    
    return True
