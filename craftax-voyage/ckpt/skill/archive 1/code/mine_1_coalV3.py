def mine_1_coal(state, log_fn, step_func):
    from craftax.craftax.constants import BlockType
    
    # Check if we have a stone pickaxe or better
    if state.inventory.pickaxe < 2:
        log_fn("Need a stone pickaxe or better to mine coal")
        # Craft a stone pickaxe first
        log_fn("Crafting stone pickaxe...")
        state = craft(state, log_fn, step_func, "stone_pickaxe", number=1)
        log_fn("Stone pickaxe crafted!")
    
    # Explore until we find the coal block
    state = explore_until(state, log_fn, step_func, BlockType.COAL)
    log_fn("Found coal!")
    
    # Mine 1 coal block
    state = mine_block(state, log_fn, step_func, BlockType.COAL, 1)
    log_fn(f"Successfully mined 1 coal! Current coal: {state.inventory.coal}")
    
    return state