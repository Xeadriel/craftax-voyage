def mine_5_stone(state, log_fn, step_func):
    from craftax.craftax.constants import BlockType
    
    # Mine 5 stone blocks
    # I have a stone pickaxe (level 2) which can mine stone
    # Stone is visible at 2 tiles, so mine_block will handle it
    state = mine_block(state, log_fn, step_func, BlockType.STONE, 5, max_steps=60)
    
    return state