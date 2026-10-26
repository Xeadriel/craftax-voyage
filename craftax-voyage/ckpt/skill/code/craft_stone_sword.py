def craft_stone_sword(state, log_fn, step_func):
    from craftax.craftax.constants import Action, BlockType
    
    # Stone sword needs 1 wood + 1 stone and a crafting table nearby
    # Crafting table needs 2 wood
    # Total needed: 3 wood, 1 stone
    # I have: 1 wood, 4 stone
    
    total_wood_needed = 3  # 2 for table + 1 for sword
    
    # Step 1: Mine enough wood
    log_fn(f"Need {total_wood_needed} wood, have {state.inventory.wood}")
    trees_to_mine = total_wood_needed - state.inventory.wood
    
    if trees_to_mine > 0:
        log_fn(f"Mining {trees_to_mine} more trees")
        for i in range(trees_to_mine):
            log_fn(f"Mining tree {i+1}/{trees_to_mine}")
            state = explore_until(state, log_fn, step_func, BlockType.TREE)
            state = mine_block(state, log_fn, step_func, BlockType.TREE, 1)
    
    log_fn(f"Have {state.inventory.wood} wood")
    
    # Step 2: Place a crafting table (needs 2 wood)
    log_fn("Placing crafting table")
    state = place(state, log_fn, step_func, "crafting_table")
    log_fn(f"Have {state.inventory.wood} wood after placing table")
    
    # Step 3: Craft the stone sword (needs 1 wood, 1 stone)
    log_fn("Crafting stone sword")
    state = craft(state, log_fn, step_func, Action.MAKE_STONE_SWORD)
    
    log_fn("Stone sword crafted successfully")
    return state