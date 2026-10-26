def mine_iron(state, log_fn, step_func):
    """
    Mines 1 iron block when visible or when it can be found and mined.
    
    Args:
        state: Current EnvState
        log_fn: Logging function taking a single string
        step_func: Function taking an action id (int) and returning the new EnvState
    
    Returns:
        The final EnvState after mining 1 iron
    
    Raises:
        Exception: If the player doesn't have a stone pickaxe or higher, or if the iron
            is not visible or reachable
    """
    from craftax.craftax.constants import BlockType
    
    # Check if we have a stone pickaxe or better
    if state.inventory.pickaxe < 2:
        log_fn("Need a stone pickaxe or better to mine iron")
        raise Exception("Need a stone pickaxe or better to mine iron")
    
    log_fn("Looking for iron block...")
    
    # Explore until we find the iron block
    state = explore_until(state, log_fn, step_func, BlockType.IRON)
    log_fn("Found iron block!")
    
    # Mine the iron using the helper function
    state = mine_block(state, log_fn, step_func, BlockType.IRON, 1)
    log_fn("Successfully mined iron!")
    
    return state