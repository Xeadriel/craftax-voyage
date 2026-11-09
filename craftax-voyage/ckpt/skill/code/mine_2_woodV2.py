def mine_2_wood(state, log_fn, step_func):
    from craftax.craftax.constants import BlockType
    # Mine 2 trees to get 2 more wood
    state = mine_block(state, log_fn, step_func, BlockType.TREE, 2, max_steps=20)
    return state