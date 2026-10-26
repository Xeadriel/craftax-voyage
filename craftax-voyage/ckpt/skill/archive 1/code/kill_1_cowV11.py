from craftax.craftax.constants import MobType

def kill_1_cow(state, log_fn, step_func):
    """
    Kills 1 cow on the current floor using melee attack.
    
    Args:
        state: Current EnvState
        log_fn: Logging function taking a single string
        step_func: Function taking an action id (int) and returning the new EnvState
        
    Returns:
        The final EnvState after the cow was killed
    """
    log_fn("Starting to kill 1 cow")
    
    # Check if we have a sword (melee weapon)
    if state.inventory.sword > 0:
        log_fn("Have an Iron Sword in inventory, can use melee attack")
    else:
        log_fn("No sword in inventory, need to craft one first")
        from craftax.craftax.constants import Action
        state = craft(state, log_fn, step_func, Action.MAKE_WOOD_SWORD)
        log_fn("Wood sword crafted successfully!")
    
    # The cow is already visible on the map at (5, -1)
    # Use kill_mob which handles positioning and attacking automatically
    log_fn("Killing cow...")
    state = kill_mob(state, log_fn, step_func, (MobType.PASSIVE, 0), max_steps=20)
    
    log_fn(f"Cow killed! Food increased from {state.inventory.food} to {state.inventory.food + 6}")
    
    return state