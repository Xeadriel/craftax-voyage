def mine_2_wood(state, log_fn, step_func):
    from craftax.craftax.constants import BlockType
    # First ensure a tree is in view
    state = explore_until(state, log_fn, step_func, BlockType.TREE, max_steps=30)
    # Mine 2 trees to get 2 wood
    state = mine_block(state, log_fn, step_func, BlockType.TREE, 2, max_steps=30)
    return state