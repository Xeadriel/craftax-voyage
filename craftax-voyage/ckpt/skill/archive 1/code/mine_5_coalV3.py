from craftax.craftax.constants import BlockType

def mine_5_coal(state, log_fn, step_func):
    """
    Mines 5 coal blocks on the current floor.
    
    Args:
        state: Current EnvState
        log_fn: Logging function taking a single string
        step_func: Function taking an action id (int) and returning the new EnvState
        
    Returns:
        The final EnvState after mining 5 coal
    """
    log_fn("Starting to mine 5 coal")
    
    # Check if we have enough coal
    coal_needed = 5 - state.inventory.coal
    log_fn(f"Need to mine {coal_needed} more coal")
    
    if coal_needed <= 0:
        log_fn(f"Already have enough coal: {state.inventory.coal}")
        return state
    
    # Check if we have a pickaxe that can mine coal (Stone Pickaxe level 2 or higher)
    if state.inventory.pickaxe < 2:
        log_fn("Need to craft a pickaxe that can mine coal (Stone Pickaxe level 2+)")
        raise Exception("Need to craft a pickaxe that can mine coal")
    
    # Mine coal blocks one at a time
    for i in range(coal_needed):
        log_fn(f"Coal {i+1}/{coal_needed} - exploring for coal...")
        
        # Explore until we find coal in sight
        # Don't rely on previously seen locations - this ensures we find nearby coal
        state = explore_until(state, log_fn, step_func, BlockType.COAL)
        
        log_fn(f"Coal {i+1}/{coal_needed} - coal found in sight!")
        
        log_fn(f"Coal {i+1}/{coal_needed} - mining coal...")
        
        # Mine the coal block
        state = mine_block(state, log_fn, step_func, BlockType.COAL, 1)
        
        log_fn(f"Coal {i+1}/{coal_needed} - mined! Current coal: {state.inventory.coal}")
        
        # Check if we reached our goal
        if state.inventory.coal >= 5:
            log_fn(f"Successfully mined enough coal! Total coal: {state.inventory.coal}")
            break
    
    log_fn(f"Successfully mined 5 coal! Final coal count: {state.inventory.coal}")
    
    return state