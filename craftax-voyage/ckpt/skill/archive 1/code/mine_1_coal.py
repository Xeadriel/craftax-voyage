def mine_1_coal(state, log_fn, step_func):
    """
    Mines 1 coal block using the stone pickaxe.
    
    Args:
        state: Current EnvState
        log_fn: Logging function taking a single string
        step_func: Function taking an action id (int) and returning the new EnvState
    
    Returns:
        The final EnvState after mining 1 coal
    
    Raises:
        Exception: If coal cannot be found or mined
    """
    log_fn("Looking for coal to mine...")
    state = explore_until(state, log_fn, step_func, BlockType.COAL)
    log_fn("Found coal!")
    
    log_fn("Mining 1 coal...")
    state = mine_block(state, log_fn, step_func, BlockType.COAL, 1)
    
    log_fn(f"Successfully mined 1 coal! Current coal: {state.inventory.coal}")
    return state