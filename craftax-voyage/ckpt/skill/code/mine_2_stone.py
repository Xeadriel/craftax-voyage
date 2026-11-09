def mine_2_stone(state, log_fn, step_func):
    from craftax.craftax.constants import BlockType
    
    # I have 0 stone, need 2 more
    # I have a wood pickaxe which can mine stone (requires pickaxe level >= 1)
    # Stone is in view (nearest 2 tiles), so I can mine directly
    
    state = mine_block(state, log_fn, step_func, BlockType.STONE, 2, max_steps=30)
    
    return state