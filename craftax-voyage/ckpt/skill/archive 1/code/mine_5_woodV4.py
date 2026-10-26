from craftax.craftax.constants import BlockType

def mine_5_wood(state, log_fn, step_func):
    """
    Mines 5 wood from trees on the current floor.
    
    Args:
        state: Current EnvState
        log_fn: Logging function taking a single string
        step_func: Function taking an action id (int) and returning the new EnvState
        
    Returns:
        The final EnvState after mining 5 wood
    """
    log_fn("Starting to mine 5 wood")
    
    # Check current wood count
    current_wood = state.inventory.wood
    log_fn(f"Current wood: {current_wood}")
    
    # Calculate how many more trees we need (convert to int)
    wood_needed = int(5 - current_wood)
    log_fn(f"Need to mine {wood_needed} more trees to reach 5 wood")
    
    # If we already have 5 wood, return early
    if wood_needed <= 0:
        log_fn(f"Already have enough wood: {current_wood}")
        return state
    
    # Mine trees one at a time to stay within step budget
    for i in range(wood_needed):
        log_fn(f"Tree {i+1}/{wood_needed} - exploring for a tree...")
        
        # Explore until we find a tree in sight
        state = explore_until(state, log_fn, step_func, BlockType.TREE)
        
        log_fn(f"Tree {i+1}/{wood_needed} - found in sight!")
        
        log_fn(f"Tree {i+1}/{wood_needed} - mining...")
        
        # Mine the single tree (one at a time)
        state = mine_block(state, log_fn, step_func, BlockType.TREE, 1)
        
        current_wood = state.inventory.wood
        log_fn(f"Tree {i+1}/{wood_needed} - mined! Wood: {current_wood}")
        
        # Check if we reached our goal
        if current_wood >= 5:
            log_fn(f"Successfully mined enough wood! Total wood: {current_wood}")
            break
    
    log_fn(f"Task complete! Final wood: {state.inventory.wood}")
    
    return state