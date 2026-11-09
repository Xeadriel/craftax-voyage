def mine_4_wood(state, log_fn, step_func):
    from craftax.craftax.constants import BlockType
    
    # Tree is already in view (nearest 4 tiles), so we can mine directly
    # Mine 4 trees to get 4 wood
    state = mine_block(state, log_fn, step_func, BlockType.TREE, 4, max_steps=40)
    
    return state