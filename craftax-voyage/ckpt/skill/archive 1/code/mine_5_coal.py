from craftax.craftax.constants import Action, BlockType

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
    
    # Check if we have a Stone Pickaxe or better
    if state.inventory.pickaxe == "Wood Pickaxe":
        log_fn("Need to craft Stone Pickaxe (requires 1 wood, 1 stone)")
        # Craft Stone Pickaxe (requires 1 wood, 1 stone)
        state = craft(state, log_fn, step_func, Action.MAKE_STONE_PICKAXE)
    
    # Explore until we find coal
    log_fn("Exploring for coal...")
    state = explore_until(state, log_fn, step_func, BlockType.COAL)
    
    # Mine coal 5 times
    coal_needed = 5 - state.inventory.coal
    log_fn(f"Need to mine {coal_needed} more coal")
    
    for i in range(coal_needed):
        log_fn(f"Step {i+1}/{coal_needed} - Exploring for coal...")
        
        # Explore until we find a coal block
        state = explore_until(state, log_fn, step_func, BlockType.COAL)
        
        # Mine the coal
        state = mine_block(state, log_fn, step_func, BlockType.COAL, 1)
        
        log_fn(f"Step {i+1}/{coal_needed} - Mined coal, now have {state.inventory.coal} coal")
    
    log_fn(f"Successfully mined {coal_needed} coal! Final coal count: {state.inventory.coal}")
    
    return state