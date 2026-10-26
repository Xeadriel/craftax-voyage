from craftax.craftax.constants import BlockType, MobType

def kill_cow(state, log_fn, step_func):
    """
    Kills 1 cow in sight.
    
    Args:
        state: Current EnvState
        log_fn: Logging function taking a single string
        step_func: Function taking an action id (int) and returning the new EnvState
    
    Returns:
        The final EnvState after the cow was killed
    
    Raises:
        Exception: If we don't have a sword or cannot find the cow
    """
    # Check if we have a sword
    if state.inventory.sword > 0:
        log_fn("Already have a sword!")
        # Face the cow and attack
        state = explore_until(state, log_fn, step_func, (MobType.PASSIVE, 0))
        state = kill_mob(state, log_fn, step_func, (MobType.PASSIVE, 0))
        return state
    else:
        log_fn("Need to craft a sword first")
        # Mine wood first
        log_fn("Mining wood...")
        state = explore_until(state, log_fn, step_func, BlockType.TREE)
        state = mine_block(state, log_fn, step_func, BlockType.TREE, 1)
        
        # Craft a wood sword (needs 1 wood and crafting table)
        log_fn("Crafting wood sword...")
        state = craft(state, log_fn, step_func, "wood_sword", number=1)
        
        # Kill the cow
        log_fn("Killing cow...")
        state = explore_until(state, log_fn, step_func, (MobType.PASSIVE, 0))
        state = kill_mob(state, log_fn, step_func, (MobType.PASSIVE, 0))
        
        log_fn("Successfully killed the cow!")
        return state