def mine_5_stone(state, log_fn, step_func):
    from craftax.craftax.constants import BlockType
    
    # I have 0 stone, need 5 more
    # I have a wood pickaxe (level 1) which can mine stone
    
    # Explore until stone is in view
    state = explore_until(state, log_fn, step_func, BlockType.STONE, max_steps=40)
    
    # Mine 5 stone blocks
    state = mine_block(state, log_fn, step_func, BlockType.STONE, 5, max_steps=60)
    
    return state