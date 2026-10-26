def mine_5_iron(state, log_fn, step_func):
    """
    Mines 5 iron blocks on the current floor.
    
    Args:
        state: Current EnvState
        log_fn: Logging function taking a single string
        step_func: Function taking an action id (int) and returning the new EnvState
        
    Returns:
        The final EnvState after mining 5 iron
    """
    from craftax.craftax.constants import BlockType
    
    log_fn("Starting to mine 5 iron")
    
    # Check if we already have enough iron
    if state.inventory.iron >= 5:
        log_fn("Already have {} iron, no need to mine".format(state.inventory.iron))
        return state
    
    # Calculate how many more iron we need
    iron_needed = 5 - state.inventory.iron
    log_fn(f"Need to mine {iron_needed} more iron")
    
    # Keep exploring until we find iron for each needed block
    for i in range(iron_needed):
        log_fn(f"Step {i+1}/{iron_needed} - Exploring for iron...")
        
        # Explore until we find an iron block
        state = explore_until(state, log_fn, step_func, BlockType.IRON)
        
        # Mine the iron block
        log_fn(f"Step {i+1}/{iron_needed} - Mining iron...")
        state = mine_block(state, log_fn, step_func, BlockType.IRON, 1)
        
        log_fn(f"Step {i+1}/{iron_needed} - Mined iron, now have {state.inventory.iron} iron")
    
    log_fn(f"Successfully mined {iron_needed} iron! Final iron count: {state.inventory.iron}")
    
    return state