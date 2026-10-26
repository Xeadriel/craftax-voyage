def craft_iron_pickaxe(state, log_fn, step_func):
    """
    Crafts 1 iron pickaxe if possible.
    
    Args:
        state: Current EnvState
        log_fn: Logging function taking a single string
        step_func: Function taking an action id (int) and returning the new EnvState
    
    Returns:
        The final EnvState after crafting the iron pickaxe
    
    Raises:
        Exception: If we don't have enough resources
    """
    # Check if we have the required resources
    if state.inventory.wood < 1:
        log_fn("Not enough wood to craft iron pickaxe")
        raise Exception("Not enough wood to craft iron pickaxe")
    if state.inventory.stone < 1:
        log_fn("Not enough stone to craft iron pickaxe")
        raise Exception("Not enough stone to craft iron pickaxe")
    if state.inventory.iron < 1:
        log_fn("Not enough iron to craft iron pickaxe")
        raise Exception("Not enough iron to craft iron pickaxe")
    if state.inventory.coal < 1:
        log_fn("Not enough coal to craft iron pickaxe")
        raise Exception("Not enough coal to craft iron pickaxe")
    
    # Check if we're near a crafting table and furnace
    # Player is at (0, 0), crafting table at (-1, 0), furnace at (0, -1)
    # Both are within 1 tile distance, so we're near both
    
    log_fn("Crafting iron pickaxe...")
    state = craft(state, log_fn, step_func, "iron_pickaxe")
    
    log_fn(f"Successfully crafted iron pickaxe! Current iron: {state.inventory.iron}")
    
    return state