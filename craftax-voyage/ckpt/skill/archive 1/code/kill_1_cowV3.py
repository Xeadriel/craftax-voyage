from craftax.craftax.constants import MobType

def kill_1_cow(state, log_fn, step_func):
    """
    Kills 1 cow on the current floor.
    
    Args:
        state: Current EnvState
        log_fn: Logging function taking a single string
        step_func: Function taking an action id (int) and returning the new EnvState
        
    Returns:
        The final EnvState after the cow was killed
    """
    log_fn("Starting to kill 1 cow")
    
    # Explore until we find a cow in sight
    log_fn("Exploring for a cow...")
    state = explore_until(state, log_fn, step_func, (MobType.PASSIVE, 0))
    
    # Kill the cow
    log_fn("Killing cow...")
    state = kill_mob(state, log_fn, step_func, (MobType.PASSIVE, 0))
    
    log_fn(f"Cow killed! Food increased from {state.inventory.food} to {state.inventory.food + 6}")
    
    return state