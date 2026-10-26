def mine_10_wood(state, log_fn, step_func):
    """
    Mines 10 wood from trees on the current floor.
    
    Args:
        state: Current EnvState
        log_fn: Logging function taking a single string
        step_func: Function taking an action id (int) and returning the new EnvState
        
    Returns:
        The final EnvState after mining 10 wood
    """
    from craftax.craftax.constants import BlockType
    
    log_fn("Starting to mine 10 wood")
    
    # Check current wood count
    current_wood = state.inventory.wood
    log_fn(f"Current wood: {current_wood}")
    
    # Calculate how many more trees we need
    wood_needed = 10 - current_wood
    log_fn(f"Need to mine {wood_needed} more trees to reach 10 wood")
    
    # Mine trees one at a time to stay within step budget
    for i in range(wood_needed):
        log_fn(f"Tree {i+1}/{wood_needed} - exploring for a tree...")
        
        # Explore until we find a tree in sight
        state = explore_until(state, log_fn, step_func, BlockType.TREE)
        
        log_fn(f"Tree {i+1}/{wood_needed} - mining...")
        
        # Mine the single tree (one at a time to stay within step budget)
        state = mine_block(state, log_fn, step_func, BlockType.TREE, 1)
        
        current_wood = state.inventory.wood
        log_fn(f"Tree {i+1}/{wood_needed} - mined! Wood: {current_wood}")
        
        # Check if we reached our goal
        if current_wood >= 10:
            log_fn(f"Successfully mined enough wood! Total wood: {current_wood}")
            break
    
    log_fn(f"Task complete! Final wood: {state.inventory.wood}")
    
    return state