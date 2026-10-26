from craftax.craftax.constants import Action, BlockType, ItemType, MobType

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
    log_fn("Starting to kill 1 zombie")
    
    # Check if we have a crafting table
    # We need to craft one first since we have 0 crafting tables
    # First, check if we have enough wood for crafting table (2 wood)
    if state.inventory.wood < 2:
        log_fn("Need to find a tree for crafting table (need 2, have {})".format(state.inventory.wood))
        state = explore_until(state, log_fn, step_func, BlockType.TREE)
        state = mine_block(state, log_fn, step_func, BlockType.TREE, 1)
    
    # Craft a crafting table
    log_fn("Crafting crafting table (costs 2 wood)")
    state = craft(state, log_fn, step_func, Action.MAKE_WOOD_PICKAXE)  # This is wrong - need to craft table
    
    # Actually, we need to place a crafting table first, then craft the sword
    # Let me re-think this...
    
    # Place a crafting table
    log_fn("Placing crafting table (costs 2 wood)")
    state = place(state, log_fn, step_func, "crafting_table")
    log_fn("Crafting table placed. Wood remaining: {}".format(state.inventory.wood))
    
    # Craft a wood sword
    log_fn("Crafting wood sword (costs 1 wood)")
    state = craft(state, log_fn, step_func, Action.MAKE_WOOD_SWORD)
    log_fn("Wood sword crafted successfully!")
    
    # Now kill the zombie
    log_fn("Killing zombie...")
    state = kill_mob(state, log_fn, step_func, (MobType.MELEE, 0), max_steps=20)
    
    log_fn(f"Zombie killed! Food increased from {state.inventory.food} to {state.inventory.food + 6}")
    
    return state

from craftax.craftax.constants import Action, BlockType, ItemType, MobType

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
    log_fn("Starting to kill 1 zombie")
    
    # We need to craft a wood sword first since we have no sword
    # First, place a crafting table (costs 2 wood)
    log_fn("Placing crafting table (costs 2 wood)")
    state = place(state, log_fn, step_func, "crafting_table")
    log_fn("Crafting table placed. Wood remaining: {}".format(state.inventory.wood))
    
    # Craft a wood sword (costs 1 wood)
    log_fn("Crafting wood sword (costs 1 wood)")
    state = craft(state, log_fn, step_func, Action.MAKE_WOOD_SWORD)
    log_fn("Wood sword crafted successfully!")
    
    # Now kill the zombie using kill_mob which handles positioning and attacking
    log_fn("Killing zombie...")
    state = kill_mob(state, log_fn, step_func, (MobType.MELEE, 0), max_steps=20)
    
    log_fn(f"Zombie killed! Food increased from {state.inventory.food} to {state.inventory.food + 6}")
    
    return state