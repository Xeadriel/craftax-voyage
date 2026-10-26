from craftax.craftax.constants import Action, BlockType, MobType

def kill_1_skeleton(state, log_fn, step_func):
    """
    Kills 1 skeleton on the current floor.
    
    Args:
        state: Current EnvState
        log_fn: Logging function taking a single string
        step_func: Function taking an action id (int) and returning the new EnvState
        
    Returns:
        The final EnvState after the skeleton was killed
    """
    log_fn("Starting to kill 1 skeleton")
    
    # Check if we have arrows - if not, craft some first
    if state.inventory.arrows == 0:
        log_fn("No arrows in inventory, crafting 2 arrows (need 1 wood, 1 stone)")
        
        # Check if we have enough resources
        if state.inventory.wood < 1 or state.inventory.stone < 1:
            log_fn("Need to find resources for arrows")
            # Explore until we find a tree for wood
            state = explore_until(state, log_fn, step_func, BlockType.TREE)
            state = mine_block(state, log_fn, step_func, BlockType.TREE, 1)
            log_fn("Mined wood, have {} wood now".format(state.inventory.wood))
        
        # Craft arrows (1 wood + 1 stone = 2 arrows)
        log_fn("Crafting 2 arrows (costs 1 wood, 1 stone)")
        state = craft(state, log_fn, step_func, Action.MAKE_ARROW)
        log_fn("Crafted 2 arrows. Arrows in inventory: {}".format(state.inventory.arrows))
    
    # Explore until we find a skeleton in sight
    log_fn("Exploring for skeleton...")
    state = explore_until(state, log_fn, step_func, (MobType.RANGED, 0))
    log_fn("Found skeleton in sight!")
    
    # Use kill_mob which handles positioning and attacking automatically
    log_fn("Killing skeleton with ranged attack...")
    state = kill_mob(state, log_fn, step_func, (MobType.RANGED, 0), max_steps=20)
    
    log_fn("Skeleton killed successfully!")
    
    return state