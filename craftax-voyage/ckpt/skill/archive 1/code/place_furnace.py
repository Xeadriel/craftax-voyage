def place_furnace(state, log_fn, step_func):
    """
    Places 1 furnace if possible.
    
    Args:
        state: Current EnvState
        log_fn: Logging function taking a single string
        step_func: Function taking an action id (int) and returning the new EnvState
    
    Returns:
        The final EnvState after placing the furnace
    
    Raises:
        Exception: If we don't have enough stone or no valid position to place it
    """
    # Check if we have enough stone (need 1 for furnace)
    if state.inventory.stone < 1:
        log_fn("Not enough stone to place furnace")
        raise Exception("Not enough stone to place furnace")
    
    log_fn("Placing furnace...")
    state = place(state, log_fn, step_func, "furnace")
    log_fn("Furnace placed!")
    
    return state