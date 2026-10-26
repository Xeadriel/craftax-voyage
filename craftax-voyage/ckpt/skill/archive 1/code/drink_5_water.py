def drink_5_water(state, log_fn, step_func):
    """
    Drinks 5 water from the nearest water source on the current floor.
    
    Args:
        state: Current EnvState
        log_fn: Logging function taking a single string
        step_func: Function taking an action id (int) and returning the new EnvState
        
    Returns:
        The final EnvState after drinking 5 water
    """
    log_fn("Starting to drink 5 water")
    log_fn(f"Current drink level: {state.player_drink}")
    
    # Explore until we find water in sight
    log_fn("Exploring for water source...")
    state = explore_until(state, log_fn, step_func, BlockType.WATER)
    log_fn("Found water source in sight!")
    
    # Drink 5 times from the water source
    log_fn("Drinking 5 times from water source...")
    state = drink(state, log_fn, step_func, number=5, max_steps=20)
    
    log_fn(f"Successfully drank 5 water! Final drink count: {state.player_drink}")
    log_fn(f"Health after drinking: {state.player_health}")
    
    return state