def mine_4_wood(state, log_fn, step_func):
    from craftax.craftax.constants import BlockType
    # Mine 4 trees (each tree gives exactly 1 wood)
    # The tree is already in view (nearest 1 tile), so no exploration needed
    state = mine_block(state, log_fn, step_func, BlockType.TREE, 4, max_steps=40)
    return state