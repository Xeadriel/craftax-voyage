def craft_wood_pickaxe(state, log_fn, step_func):
    """
    Crafts 1 wood pickaxe if possible.
    
    Args:
        state: Current EnvState
        log_fn: Logging function taking a single string
        step_func: Function taking an action id (int) and returning the new EnvState
    
    Returns:
        The final EnvState after crafting the wood pickaxe
    
    Raises:
        Exception: If we don't have enough wood or the crafting table is not nearby
    """
    # Check if we have enough wood (need 1 for wood pickaxe)
    if state.inventory.wood < 1:
        log_fn("Not enough wood to craft wood pickaxe")
        raise Exception("Not enough wood to craft wood pickaxe")
    
    log_fn("Crafting wood pickaxe...")
    
    # Craft the wood pickaxe using the correct parameter name
    state = craft(state, log_fn, step_func, "wood_pickaxe", number=1)
    
    log_fn(f"Successfully crafted wood pickaxe! Current wood: {state.inventory.wood}")
    
    return state