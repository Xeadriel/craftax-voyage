def mine_10_stone(state, log_fn, step_func):
    """
    Mines 10 stone blocks.
    
    Args:
        state: Current EnvState
        log_fn: Logging function taking a single string
        step_func: Function taking an action id (int) and returning the new EnvState
        
    Returns:
        The final EnvState after mining 10 stone
    """
    log_fn("Starting to mine 10 stone")
    
    # Check if we have a Stone Pickaxe
    if state.inventory.stone > 0:
        log_fn("Already have stone, crafting Stone Pickaxe")
        from craftax.craftax.constants import Action
        state = craft(state, log_fn, step_func, Action.MAKE_STONE_PICKAXE)
    
    # Mine stone blocks until we have 10
    stone_needed = 10 - state.inventory.stone
    log_fn(f"Need to mine {stone_needed} more stone")
    
    for i in range(stone_needed):
        log_fn(f"Step {i+1}/{stone_needed} - Exploring for stone...")
        
        # Explore until we find a stone block
        state = explore_until(state, log_fn, step_func, BlockType.STONE)
        
        # Mine the stone
        state = mine_block(state, log_fn, step_func, BlockType.STONE, 1)
        
        log_fn(f"Step {i+1}/{stone_needed} - Mined stone, now have {state.inventory.stone} stone")
    
    log_fn(f"Successfully mined 10 stone! Final inventory: {state.inventory.stone} stone")
    
    return state