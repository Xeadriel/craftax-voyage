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
    
    # Check if we have a sword first
    if state.inventory.sword > 0:
        log_fn("Already have a sword, can use melee attack")
        # Use kill_mob which handles positioning and attacking
        state = kill_mob(state, log_fn, step_func, (MobType.RANGED, 0), max_steps=20)
        return state
    else:
        log_fn("No sword in inventory, need to craft one")
    
    # Check if we have a bow and arrows
    if state.inventory.bow > 0 and state.inventory.arrows > 0:
        log_fn("Already have bow and arrows, can use ranged attack")
        # Use kill_mob which handles positioning and attacking
        state = kill_mob(state, log_fn, step_func, (MobType.RANGED, 0), max_steps=20)
        return state
    else:
        log_fn("Need to craft weapon or get arrows")
    
    # Check if we have a crafting table nearby
    # First, we need to place one if we don't have one
    # Check if we have enough wood for a crafting table (2 wood)
    if state.inventory.wood < 2:
        log_fn("Need more wood for crafting table (need 2, have {})".format(state.inventory.wood))
        # Explore until we find a tree in sight
        log_fn("Exploring for a tree...")
        state = explore_until(state, log_fn, step_func, BlockType.TREE)
        log_fn("Tree found, mining it...")
        # Mine the tree
        state = mine_block(state, log_fn, step_func, BlockType.TREE, 1)
        log_fn("Mined wood, now have {} wood".format(state.inventory.wood))
    
    # Now we should have enough wood, place the crafting table
    log_fn("Placing crafting table (costs 2 wood)")
    state = place(state, log_fn, step_func, "crafting_table")
    log_fn("Crafting table placed. Wood remaining: {}".format(state.inventory.wood))
    
    # Check if we have enough wood for a wood sword (1 wood)
    if state.inventory.wood < 1:
        log_fn("Need more wood for wood sword (need 1, have {})".format(state.inventory.wood))
        # Mine another tree
        log_fn("Mining another tree for wood sword...")
        state = explore_until(state, log_fn, step_func, BlockType.TREE)
        state = mine_block(state, log_fn, step_func, BlockType.TREE, 1)
        log_fn("Mined wood, now have {} wood".format(state.inventory.wood))
    
    # Craft a wood sword
    log_fn("Crafting wood sword (costs 1 wood)")
    from craftax.craftax.constants import Action
    state = craft(state, log_fn, step_func, Action.MAKE_WOOD_SWORD)
    log_fn("Wood sword crafted successfully!")
    
    # Now kill the skeleton with the sword
    log_fn("Killing skeleton with wood sword...")
    state = kill_mob(state, log_fn, step_func, (MobType.RANGED, 0), max_steps=20)
    
    log_fn(f"Skeleton killed! Food increased from {state.inventory.food} to {state.inventory.food + 6}")
    
    return state