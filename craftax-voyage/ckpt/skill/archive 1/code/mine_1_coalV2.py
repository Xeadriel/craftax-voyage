from craftax.craftax.constants import BlockType

def mine_1_coal(state, log_fn, step_func):
    """
    Mines 1 coal block on the current floor.
    
    Args:
        state: Current EnvState
        log_fn: Logging function taking a single string
        step_func: Function taking an action id (int) and returning the new EnvState
        
    Returns:
        The final EnvState after mining 1 coal
    """
    log_fn("Starting to mine 1 coal")
    
    # Check if we have a pickaxe that can mine coal (any level 1+)
    # Pickaxe is stored as an integer: 1 = Wood, 2 = Stone, 3 = Iron, 4 = Diamond
    if state.inventory.pickaxe < 1:
        log_fn(f"No suitable pickaxe for mining coal (level: {state.inventory.pickaxe})")
        raise Exception("Need a pickaxe level 1+ to mine coal")
    
    log_fn(f"Have pickaxe level {state.inventory.pickaxe}, can mine coal")
    
    # Explore until we find coal in sight
    log_fn("Exploring for coal...")
    state = explore_until(state, log_fn, step_func, BlockType.COAL)
    log_fn("Coal found in sight!")
    
    # Mine the coal block
    log_fn("Mining coal...")
    state = mine_block(state, log_fn, step_func, BlockType.COAL, 1)
    
    log_fn(f"Successfully mined coal! Coal count: {state.inventory.coal}")
    
    return state