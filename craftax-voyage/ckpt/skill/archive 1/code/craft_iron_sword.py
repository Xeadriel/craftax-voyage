from craftax.craftax.constants import BlockType

def craft_iron_sword(state, log_fn, step_func):
    """
    Crafts 1 iron sword if possible.
    
    Args:
        state: Current EnvState
        log_fn: Logging function taking a single string
        step_func: Function taking an action id (int) and returning the new EnvState
    
    Returns:
        The final EnvState after crafting the iron sword
    
    Raises:
        Exception: If we don't have enough resources
    """
    # Check if we have enough resources
    if state.inventory.wood < 1:
        log_fn("Not enough wood to craft iron sword")
        raise Exception("Not enough wood to craft iron sword")
    if state.inventory.stone < 1:
        log_fn("Not enough stone to craft iron sword")
        raise Exception("Not enough stone to craft iron sword")
    if state.inventory.iron < 1:
        log_fn("Looking for iron ore to mine...")
    if state.inventory.coal < 1:
        log_fn("Not enough coal to craft iron sword")
        raise Exception("Not enough coal to craft iron sword")
    
    # Mine iron if we don't have enough
    if state.inventory.iron < 1:
        log_fn("Exploring for iron ore...")
        state = explore_until(state, log_fn, step_func, BlockType.IRON)
        log_fn("Found iron ore!")
        state = mine_block(state, log_fn, step_func, BlockType.IRON, 1)
        log_fn(f"Successfully mined iron! Current iron: {state.inventory.iron}")
    
    # Craft the iron sword (craft function handles placing stations if needed)
    log_fn("Crafting iron sword...")
    state = craft(state, log_fn, step_func, "iron_sword", number=1)
    log_fn("Successfully crafted iron sword!")
    
    return state