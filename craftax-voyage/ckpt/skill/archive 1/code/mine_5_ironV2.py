from craftax.craftax.constants import Action, BlockType

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
    log_fn("Starting to mine 5 iron")
    
    # Check current iron count
    current_iron = state.inventory.iron
    log_fn(f"Current iron: {current_iron}")
    
    # Calculate how many more iron we need
    iron_needed = 5 - current_iron
    log_fn(f"Need to mine {iron_needed} more iron to reach 5")
    
    # Mine iron blocks one at a time until we reach our goal
    for i in range(iron_needed):
        log_fn(f"Iron {i+1}/{iron_needed} - exploring for iron...")
        
        # Explore until we find an iron block in sight
        state = explore_until(state, log_fn, step_func, BlockType.IRON)
        
        log_fn(f"Iron {i+1}/{iron_needed} - found in sight!")
        
        log_fn(f"Iron {i+1}/{iron_needed} - mining iron...")
        
        # Mine the iron block (one at a time)
        state = mine_block(state, log_fn, step_func, BlockType.IRON, 1)
        
        current_iron = state.inventory.iron
        log_fn(f"Iron {i+1}/{iron_needed} - mined! Current iron: {current_iron}")
        
        # Check if we reached our goal
        if current_iron >= 5:
            log_fn(f"Successfully mined enough iron! Total iron: {current_iron}")
            break
    
    log_fn(f"Task complete! Final iron count: {state.inventory.iron}")
    
    return state