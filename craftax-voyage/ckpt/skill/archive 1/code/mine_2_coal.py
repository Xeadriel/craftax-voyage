def mine_2_coal(state, log_fn, step_func):
    """
    Mines 2 coal blocks on the current floor.
    
    Args:
        state: Current EnvState
        log_fn: Logging function taking a single string
        step_func: Function taking an action id (int) and returning the new EnvState
        
    Returns:
        The final EnvState after mining 2 coal
    """
    log_fn("Starting to mine 2 coal")
    
    # Check if we have a pickaxe that can mine coal (Stone Pickaxe level 2+)
    if state.inventory.pickaxe < 2:
        log_fn(f"No suitable pickaxe for mining coal (level: {state.inventory.pickaxe})")
        raise Exception("Need a pickaxe level 2+ to mine coal")
    
    log_fn(f"Have pickaxe level {state.inventory.pickaxe}, can mine coal")
    
    # Mine 2 coal blocks one at a time
    for i in range(2):
        log_fn(f"Coal {i+1}/2 - exploring for coal...")
        
        # Explore until we find coal in sight (even though one may already be visible)
        state = explore_until(state, log_fn, step_func, BlockType.COAL)
        
        log_fn(f"Coal {i+1}/2 - found in sight!")
        
        log_fn(f"Coal {i+1}/2 - mining coal...")
        
        # Mine the coal block (one at a time)
        state = mine_block(state, log_fn, step_func, BlockType.COAL, 1)
        
        log_fn(f"Coal {i+1}/2 - mined! Current coal: {state.inventory.coal}")
    
    log_fn(f"Successfully mined 2 coal! Final coal count: {state.inventory.coal}")
    
    return state