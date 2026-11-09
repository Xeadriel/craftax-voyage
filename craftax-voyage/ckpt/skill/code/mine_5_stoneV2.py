def mine_5_stone(state, log_fn, step_func):
    from craftax.craftax.constants import BlockType, Action
    
    # I have 0 stone, need 5 more
    target = state.inventory.stone + 5
    
    # First, craft a wood pickaxe (need 1 wood, have 2)
    state = craft(state, log_fn, step_func, Action.MAKE_WOOD_PICKAXE, 1, max_steps=20)
    
    # Explore until stone is in view
    state = explore_until(state, log_fn, step_func, BlockType.STONE, max_steps=40)
    
    # Mine 5 stone blocks
    state = mine_block(state, log_fn, step_func, BlockType.STONE, 5, max_steps=60)
    
    return state