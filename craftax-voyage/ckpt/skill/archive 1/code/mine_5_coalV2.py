from craftax.craftax.constants import Action, BlockType

def mine_5_coal(state, log_fn, step_func):
    """
    Mines 5 coal blocks on the current floor.
    
    Args:
        state: Current EnvState
        log_fn: Logging function taking a single string
        step_func: Function taking an action id (int) and returning the new EnvState
        
    Returns:
        The final EnvState after mining 5 coal
    """
    log_fn("Starting to mine 5 coal")
    
    # Check if we have enough wood for crafting table (2 wood)
    if state.inventory.wood < 2:
        log_fn(f"Not enough wood for crafting table (need 2, have {state.inventory.wood})")
        # Explore until we find a tree
        state = explore_until(state, log_fn, step_func, BlockType.TREE)
        state = mine_block(state, log_fn, step_func, BlockType.TREE, 1)
    
    # Craft a crafting table
    log_fn("Placing crafting table (costs 2 wood)")
    state = place(state, log_fn, step_func, "crafting_table")
    log_fn("Crafting table placed. Wood remaining: {}".format(state.inventory.wood))
    
    # Craft a wood pickaxe (costs 1 wood)
    if state.inventory.wood < 1:
        log_fn("Need more wood for wood pickaxe (need 1, have {})".format(state.inventory.wood))
        state = explore_until(state, log_fn, step_func, BlockType.TREE)
        state = mine_block(state, log_fn, step_func, BlockType.TREE, 1)
    
    log_fn("Crafting wood pickaxe (costs 1 wood)")
    state = craft(state, log_fn, step_func, Action.MAKE_WOOD_PICKAXE)
    log_fn("Wood pickaxe crafted successfully!")
    
    # Mine stone (need stone for stone pickaxe)
    log_fn("Mining stone for stone pickaxe...")
    state = explore_until(state, log_fn, step_func, BlockType.STONE)
    state = mine_block(state, log_fn, step_func, BlockType.STONE, 1)
    log_fn("Mined stone. Stone count: {}".format(state.inventory.stone))
    
    # Craft a stone pickaxe (costs 1 wood, 1 stone)
    log_fn("Crafting stone pickaxe (costs 1 wood, 1 stone)")
    state = craft(state, log_fn, step_func, Action.MAKE_STONE_PICKAXE)
    log_fn("Stone pickaxe crafted successfully!")
    
    # Mine 5 coal blocks
    log_fn("Mining 5 coal blocks...")
    coal_needed = 5 - state.inventory.coal
    log_fn(f"Need to mine {coal_needed} more coal")
    
    for i in range(coal_needed):
        log_fn(f"Coal {i+1}/{coal_needed} - exploring for coal...")
        state = explore_until(state, log_fn, step_func, BlockType.COAL)
        
        log_fn(f"Coal {i+1}/{coal_needed} - mining coal...")
        state = mine_block(state, log_fn, step_func, BlockType.COAL, 1)
        
        log_fn(f"Coal {i+1}/{coal_needed} - mined coal, now have {state.inventory.coal} coal")
    
    log_fn(f"Successfully mined 5 coal! Final coal count: {state.inventory.coal}")
    
    return state