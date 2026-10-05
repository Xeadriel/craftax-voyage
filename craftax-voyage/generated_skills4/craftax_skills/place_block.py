# Description:
# Places a block or plant by moving to the given location and placing the block or plant.

def place_block(state, step_func, block_type, max_steps=15):
    """
    Places a block or plant.
    
    Args:
        state: Current game state
        step_func: Function that takes an action enum and returns the action to take
        block_type: BlockType to place (e.g., STONE, PLANT, etc.)
        max_steps: Maximum steps to place (default 15)
    
    Returns:
        True if no error occurred
    
    Raises:
        ValueError: If placement not possible or moving to spot not possible
        ValueError: If character died
        ValueError: If max steps reached without placing
    """
    from craftax.craftax.constants import BlockType, SOLID_BLOCKS, DIRECTIONS, CLOSE_BLOCKS
    from craftax.craftax.util.game_logic_utils import (
        is_in_solid_block,
        is_position_in_bounds_not_in
