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
    
    # Check if we have a pickaxe that can mine coal (Stone Pickaxe level 2+)
    if state.inventory.pickaxe < 2:
        log_fn(f"No suitable pickaxe for mining coal (level: {state.inventory.pickaxe})")
        raise Exception("Need a pickaxe level 2+ to mine coal")
    
    log_fn(f"Have pickaxe level {state.inventory.pickaxe}, can mine coal")
    
    # Check current coal count
    current_coal = state.inventory.coal
    log_fn(f"Current coal: {current_coal}")
    
    # Calculate how many more coal we need
    coal_needed = 5 - current_coal
    log_fn(f"Need to mine {coal_needed} more coal to reach 5")
    
    # Mine coal blocks one at a time until we reach our goal
    for i in range(coal_needed):
        log_fn(f"Coal {i+1}/{coal_needed} - exploring for coal...")
        
        # Explore until we find coal in sight
        state = explore_until(state, log_fn, step_func, BlockType.COAL)
        
        log_fn(f"Coal {i+1}/{coal_needed} - found in sight!")
        
        log_fn(f"Coal {i+1}/{coal_needed} - mining coal...")
        
        # Mine the coal block (one at a time)
        state = mine_block(state, log_fn, step_func, BlockType.COAL, 1)
        
        current_coal = state.inventory.coal
        log_fn(f"Coal {i+1}/{coal_needed} - mined! Current coal: {current_coal}")
        
        # Check if we reached our goal
        if current_coal >= 5:
            log_fn(f"Successfully mined enough coal! Total coal: {current_coal}")
            break
    
    log_fn(f"Task complete! Final coal count: {state.inventory.coal}")
    
    return state