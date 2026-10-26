from craftax.craftax.constants import Action, BlockType, ItemType, MobType

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
    
    # Check if we have a sword (melee weapon)
    if state.inventory.sword > 0:
        log_fn("Have a sword in inventory, can use melee attack")
    else:
        log_fn("No sword in inventory, need to craft one first")
        # Craft a wood sword
        log_fn("Crafting wood sword (costs 1 wood)")
        state = craft(state, log_fn, step_func, Action.MAKE_WOOD_SWORD)
        log_fn("Wood sword crafted successfully!")
    
    # Explore until we find a cow in sight
    # Cows are PASSIVE mobs with type_id 0
    log_fn("Exploring for a cow...")
    state = explore_until(state, log_fn, step_func, (MobType.PASSIVE, 0))
    log_fn("Cow found in sight!")
    
    # Kill the cow using kill_mob which handles positioning and attacking
    log_fn("Killing cow...")
    state = kill_mob(state, log_fn, step_func, (MobType.PASSIVE, 0), max_steps=20)
    
    log_fn(f"Cow killed! Food increased from {state.inventory.food} to {state.inventory.food + 6}")
    
    return state