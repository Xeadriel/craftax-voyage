def drink_4_water(state, log_fn, step_func):
    """
    Drinks 4 water from the nearest water source in sight.
    
    Args:
        state: Current EnvState
        log_fn: Logging function taking a single string
        step_func: Function taking an action id (int) and returning the new EnvState
    
    Returns:
        The final EnvState after drinking 4 water
    
    Raises:
        Exception: If no water source is in sight or reachable
    """
    log_fn("Starting to drink 4 water...")
    
    # Explore to find water source (water is in the water block type)
    # Water sources include lakes, fountains, and water patches
    from craftax.craftax.constants import BlockType
    
    # Try to find water - it could be a lake or water patch
    # Since I don't see water on the map, I need to explore
    state = explore_until(state, log_fn, step_func, BlockType.WATER)
    log_fn("Found water source!")
    
    # Drink 4 water
    state = drink(state, log_fn, step_func, number=4, max_steps=20)
    log_fn(f"Successfully drank 4 water! Current drink: {state.player_drink}")
    
    return state