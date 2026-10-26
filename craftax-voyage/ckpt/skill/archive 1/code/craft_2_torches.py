from craftax.craftax.constants import Action

def craft_2_torches(state, log_fn, step_func):
    """
    Crafts 2 torches (actually crafts 1 which gives 4, then places 2 of them).
    
    Args:
        state: Current EnvState
        log_fn: Logging function taking a single string
        step_func: Function taking an action id (int) and returning the new EnvState
        
    Returns:
        The final EnvState after crafting and placing 2 torches
    """
    log_fn("Starting to craft 2 torches")
    
    # Check if we have enough resources
    log_fn(f"Checking resources: Wood={state.inventory.wood}, Coal={state.inventory.coal}, Torch={state.inventory.torches}")
    
    if state.inventory.wood < 1:
        log_fn("Need to find a tree for wood")
        state = explore_until(state, log_fn, step_func, BlockType.TREE)
        state = mine_block(state, log_fn, step_func, BlockType.TREE, 1)
    
    if state.inventory.coal < 1:
        log_fn("Need to find coal")
        state = explore_until(state, log_fn, step_func, BlockType.COAL)
        state = mine_block(state, log_fn, step_func, BlockType.COAL, 1)
    
    # Craft 1 torch (which gives 4 torches)
    log_fn("Crafting 1 torch (will give 4 torches)")
    state = craft(state, log_fn, step_func, Action.MAKE_TORCH)
    log_fn(f"After crafting, have {state.inventory.torches} torches")
    
    # Place 2 torches (we have 4, so place 2 and leave 2)
    log_fn("Placing first torch")
    state = place(state, log_fn, step_func, "torch")
    log_fn(f"After placing first torch, have {state.inventory.torches} torches")
    
    log_fn("Placing second torch")
    state = place(state, log_fn, step_func, "torch")
    log_fn(f"After placing second torch, have {state.inventory.torches} torches")
    
    log_fn("Successfully crafted and placed 2 torches!")
    
    return state