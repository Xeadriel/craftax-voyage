def mine_5_stone(state, log_fn, step_func):
    from craftax.craftax.constants import BlockType
    
    # Check I have a pickaxe that can mine stone (wood pickaxe level 1 is sufficient)
    if state.inventory.pickaxe < 1:
        raise Exception("No pickaxe to mine stone")
    
    # Mine 5 stone blocks (each gives 1 stone)
    # Stone is already in view (nearest 5 tiles), so no exploration needed
    state = mine_block(state, log_fn, step_func, BlockType.STONE, 5, max_steps=60)
    
    return state