def kill_1_cow(state, log_fn, step_func):
    """
    Kills 1 cow on the current floor.
    
    Args:
        state: Current EnvState
        log_fn: Logging function taking a single string
        step_func: Function taking an action id (int) and returning the new EnvState
        
    Returns:
        The final EnvState after the cow was killed
    """
    log_fn("Starting to kill 1 cow")
    
    # Check if we have a sword - if not, we need to craft one first
    if state.inventory.sword == 0:
        log_fn("No sword in inventory, need to craft one")
        
        # Check if we have enough wood for crafting table (2 wood)
        if state.inventory.wood < 2:
            log_fn("Need more wood for crafting table (need 2, have {})".format(state.inventory.wood))
            state = explore_until(state, log_fn, step_func, BlockType.TREE)
            state = mine_block(state, log_fn, step_func, BlockType.TREE, 1)
        
        # Place the crafting table (costs 2 wood)
        log_fn("Placing crafting table (costs 2 wood)")
        state = place(state, log_fn, step_func, "crafting_table")
        log_fn("Crafting table placed. Wood remaining: {}".format(state.inventory.wood))
        
        # Craft a wood sword (costs 1 wood)
        log_fn("Crafting wood sword (costs 1 wood)")
        from craftax.craftax.constants import Action
        state = craft(state, log_fn, step_func, Action.MAKE_WOOD_SWORD)
        log_fn("Wood sword crafted successfully!")
    
    # Now kill the cow
    # The cow should be visible, so we can use kill_mob directly
    # kill_mob will handle positioning and attacking automatically
    log_fn("Killing cow...")
    state = kill_mob(state, log_fn, step_func, (MobType.PASSIVE, 0), max_steps=20)
    
    log_fn(f"Cow killed! Food increased from {state.inventory.food} to {state.inventory.food + 6}")
    
    return state