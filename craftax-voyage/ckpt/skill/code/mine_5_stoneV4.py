def mine_5_stone(state, log_fn, step_func):
    from craftax.craftax.constants import BlockType
    
    # Ensure stone is in view
    state = explore_until(state, log_fn, step_func, BlockType.STONE, max_steps=40)
    
    # Mine 5 stone blocks (each gives 1 stone)
    # I have a wood pickaxe (level 1) which can mine stone (requires level >= 1)
    state = mine_block(state, log_fn, step_func, BlockType.STONE, 5, max_steps=60)
    
    return state