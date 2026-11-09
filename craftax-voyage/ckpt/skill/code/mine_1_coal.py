def mine_1_coal(state, log_fn, step_func):
    from craftax.craftax.constants import Action, BlockType
    
    # Check I have a pickaxe that can mine coal (needs level >= 1)
    if state.inventory.pickaxe < 1:
        # Need to craft a wood pickaxe first
        state = explore_until(state, log_fn, step_func, BlockType.TREE, max_steps=40)
        state = mine_block(state, log_fn, step_func, BlockType.TREE, 1, max_steps=20)
        state = craft(state, log_fn, step_func, Action.MAKE_WOOD_PICKAXE, 1, max_steps=20)
    
    # Explore until coal is in view
    state = explore_until(state, log_fn, step_func, BlockType.COAL, max_steps=60)
    
    # Mine 1 coal block
    state = mine_block(state, log_fn, step_func, BlockType.COAL, 1, max_steps=30)
    
    return state