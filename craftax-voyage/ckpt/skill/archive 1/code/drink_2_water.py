from craftax.craftax.constants import BlockType

def drink_2_water(state, log_fn, step_func):
    """
    Drinks 2 water from the nearest water source.
    
    Args:
        state: Current EnvState
        log_fn: Logging function taking a single string
        step_func: Function taking an action id (int) and returning the new EnvState
        
    Returns:
        The final EnvState after drinking 2 water
    """
    log_fn("Starting to drink 2 water")
    
    # Explore until we find water in sight
    log_fn("Exploring for water source...")
    state = explore_until(state, log_fn, step_func, BlockType.WATER)
    log_fn("Found water source in sight!")
    
    # Drink 2 times from the water source
    log_fn("Drinking 2 times from water source...")
    state = drink(state, log_fn, step_func, number=2)
    
    log_fn(f"Successfully drank 2 water! Final drink count: {state.player_drink}")
    
    return state