def mine_1_wood(state, log_fn, step_func):
    from craftax.craftax.constants import BlockType
    # Mine 1 tree to get 1 more wood
    state = mine_block(state, log_fn, step_func, BlockType.TREE, 1, max_steps=20)
    return state