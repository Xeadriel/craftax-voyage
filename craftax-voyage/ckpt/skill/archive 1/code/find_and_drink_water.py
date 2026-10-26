def find_and_drink_water(state, log_fn, step_func):
    """
    Finds water on the current floor and drinks from it.
    
    Args:
        state: Current EnvState
        log_fn: Logging function taking a single string
        step_func: Function taking an action id (int) and returning the new EnvState
        
    Returns:
        The final EnvState after drinking water
    """
    log_fn("Starting to find and drink water")
    log_fn(f"Current drink level: {state.player_drink}")
    
    # Explore until we find water in sight
    log_fn("Exploring for water source...")
    state = explore_until(state, log_fn, step_func, BlockType.WATER)
    log_fn("Found water source in sight!")
    
    # Drink from the water source
    # We'll drink 6 times to get a safe level (target ~6-7 drinks)
    # This should refill us significantly since we start at 0
    log_fn("Drinking from water source...")
    state = drink(state, log_fn, step_func, number=6)
    
    log_fn(f"Successfully drank water! Final drink count: {state.player_drink}")
    log_fn(f"Health after drinking: {state.player_health}")
    
    return state