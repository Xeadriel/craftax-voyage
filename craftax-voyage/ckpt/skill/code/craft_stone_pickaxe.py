def craft_stone_pickaxe(state, log_fn, step_func):
    from craftax.craftax.constants import Action, BlockType
    
    log_fn("Crafting a stone pickaxe")
    
    # Check if we already have a stone pickaxe or better
    if state.inventory.pickaxe >= 2:
        log_fn(f"Already have a {['none', 'wood', 'stone', 'iron', 'diamond'][min(state.inventory.pickaxe, 4)]} pickaxe")
        return state
    
    # Need at least 1 wood and 1 stone for crafting
    wood_needed = 1
    stone_needed = 1
    
    # We need 2 wood for the crafting table + 1 wood for the pickaxe = 3 total
    total_wood_needed = 2 + 1
    
    # Check if we have enough wood
    if state.inventory.wood < total_wood_needed:
        log_fn(f"Need {total_wood_needed} wood, have {state.inventory.wood}")
        
        # Need to collect more wood first
        trees_to_mine = total_wood_needed - state.inventory.wood
        
        for i in range(trees_to_mine):
            log_fn(f"Mining tree {i+1}/{trees_to_mine}")
            
            # Explore until we can see a tree
            state = explore_until(state, log_fn, step_func, BlockType.TREE)
            
            # Mine the tree to get 1 wood
            state = mine_block(state, log_fn, step_func, BlockType.TREE, 1)
            
            # Check if we have enough wood now
            if state.inventory.wood >= total_wood_needed:
                log_fn(f"Reached target: {state.inventory.wood} wood")
                break
    
    # Now we have at least 3 wood, let's place a crafting table
    log_fn("Placing crafting table")
    state = place(state, log_fn, step_func, "crafting_table")
    
    # Now craft the stone pickaxe
    log_fn("Crafting stone pickaxe")
    state = craft(state, log_fn, step_func, Action.MAKE_STONE_PICKAXE)
    
    return state