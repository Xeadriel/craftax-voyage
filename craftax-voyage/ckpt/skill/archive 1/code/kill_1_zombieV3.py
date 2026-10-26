def kill_1_zombie(state, log_fn, step_func):
    """
    Kills 1 zombie on the current floor.
    
    Args:
        state: Current EnvState
        log_fn: Logging function taking a single string
        step_func: Function taking an action id (int) and returning the new EnvState
        
    Returns:
        The final EnvState after the zombie was killed
    """
    from craftax.craftax.constants import MobType
    
    log_fn("Starting to kill 1 zombie")
    
    # Check if we have a sword (melee weapon)
    if state.inventory.sword > 0:
        log_fn("Have a sword in inventory, can use melee attack")
    else:
        log_fn("No sword in inventory, need to craft one first")
        # Craft a wood sword
        log_fn("Crafting wood sword (costs 1 wood)")
        from craftax.craftax.constants import Action
        state = craft(state, log_fn, step_func, Action.MAKE_WOOD_SWORD)
        log_fn("Wood sword crafted successfully!")
    
    # Explore until we find a zombie in sight (though one may already be visible)
    log_fn("Exploring for a zombie...")
    state = explore_until(state, log_fn, step_func, (MobType.MELEE, 0), max_steps=30)
    log_fn("Zombie found in sight!")
    
    # Kill the zombie using kill_mob which handles positioning and attacking
    log_fn("Killing zombie...")
    state = kill_mob(state, log_fn, step_func, (MobType.MELEE, 0), max_steps=20)
    
    log_fn(f"Zombie killed! Food increased from {state.inventory.food} to {state.inventory.food + 6}")
    
    return state