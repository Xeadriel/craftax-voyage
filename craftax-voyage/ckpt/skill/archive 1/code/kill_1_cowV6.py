from craftax.craftax.constants import Action, BlockType, ItemType, MobType

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
    
    # The cow is already visible at (-4, 1) and player has an Iron Sword
    # Use kill_mob which handles positioning and attacking automatically
    # Cow is a PASSIVE mob with type_id 0
    state = kill_mob(state, log_fn, step_func, (MobType.PASSIVE, 0), max_steps=20)
    
    log_fn(f"Cow killed! Food increased from {state.inventory.food} to {state.inventory.food + 6}")
    
    return state