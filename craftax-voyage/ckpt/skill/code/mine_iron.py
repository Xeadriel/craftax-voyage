def mine_iron(state, log_fn, step_func):
    from craftax.craftax.constants import Action, BlockType
    
    log_fn("Starting to mine 1 iron")
    
    # Need 4 wood total: 2 for table + 1 for wood pickaxe + 1 for stone pickaxe
    wood_needed = 4
    trees_to_mine = wood_needed - state.inventory.wood
    
    # Step 1: Mine enough wood
    if trees_to_mine > 0:
        log_fn(f"Need {trees_to_mine} more wood")
        for i in range(trees_to_mine):
            log_fn(f"Mining tree {i+1}/{trees_to_mine}")
            state = explore_until(state, log_fn, step_func, BlockType.TREE)
            state = mine_block(state, log_fn, step_func, BlockType.TREE, 1)
    
    log_fn(f"Have {state.inventory.wood} wood")
    
    # Step 2: Place a crafting table (needs 2 wood)
    if state.inventory.wood < 2:
        log_fn(f"Need 2 wood for table, have {state.inventory.wood}")
        trees_to_mine = 2 - state.inventory.wood
        for i in range(trees_to_mine):
            log_fn(f"Mining tree {i+1}/{trees_to_mine}")
            state = explore_until(state, log_fn, step_func, BlockType.TREE)
            state = mine_block(state, log_fn, step_func, BlockType.TREE, 1)
    
    log_fn("Placing crafting table")
    state = place(state, log_fn, step_func, "crafting_table")
    
    # Step 3: Craft a wood pickaxe (needs 1 wood)
    log_fn("Crafting wood pickaxe")
    state = craft(state, log_fn, step_func, Action.MAKE_WOOD_PICKAXE)
    log_fn(f"Have {state.inventory.wood} wood, {state.inventory.pickaxe} wood pickaxe")
    
    # Step 4: Mine stone (needs wood pickaxe)
    log_fn("Looking for stone to mine")
    state = explore_until(state, log_fn, step_func, BlockType.STONE)
    state = mine_block(state, log_fn, step_func, BlockType.STONE, 1)
    log_fn(f"Have {state.inventory.stone} stone")
    
    # Step 5: Craft a stone pickaxe (needs 1 wood, 1 stone)
    if state.inventory.wood < 1:
        log_fn(f"Need 1 wood for stone pickaxe, have {state.inventory.wood}")
        # Mine more wood
        state = explore_until(state, log_fn, step_func, BlockType.TREE)
        state = mine_block(state, log_fn, step_func, BlockType.TREE, 1)
    
    if state.inventory.stone < 1:
        log_fn(f"Need 1 stone for stone pickaxe, have {state.inventory.stone}")
        # Mine more stone
        state = explore_until(state, log_fn, step_func, BlockType.STONE)
        state = mine_block(state, log_fn, step_func, BlockType.STONE, 1)
    
    log_fn("Crafting stone pickaxe")
    state = craft(state, log_fn, step_func, Action.MAKE_STONE_PICKAXE)
    log_fn(f"Have {state.inventory.pickaxe} stone pickaxe")
    
    # Step 6: Mine iron (needs stone pickaxe)
    log_fn("Looking for iron to mine")
    state = explore_until(state, log_fn, step_func, BlockType.IRON)
    state = mine_block(state, log_fn, step_func, BlockType.IRON, 1)
    log_fn(f"Have {state.inventory.iron} iron")
    
    log_fn("Successfully mined 1 iron")
    return state