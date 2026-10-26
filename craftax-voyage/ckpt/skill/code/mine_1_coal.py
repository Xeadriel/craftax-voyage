def mine_1_coal(state, log_fn, step_func):
    from craftax.craftax.constants import BlockType
    
    log_fn("Looking for coal to mine")
    
    # Check if we already have coal
    if state.inventory.coal >= 1:
        log_fn(f"Already have {state.inventory.coal} coal, task complete")
        return state
    
    # Check if we have a pickaxe
    if state.inventory.pickaxe < 1:
        log_fn("Need a pickaxe to mine coal")
        raise Exception("Need a pickaxe to mine coal")
    
    # Explore until we can see coal
    log_fn("Exploring to find coal...")
    state = explore_until(state, log_fn, step_func, BlockType.COAL)
    
    # Mine the coal
    log_fn("Mining coal")
    state = mine_block(state, log_fn, step_func, BlockType.COAL, 1)
    
    log_fn(f"Successfully mined coal. Current inventory: {state.inventory.coal} coal")
    
    return state