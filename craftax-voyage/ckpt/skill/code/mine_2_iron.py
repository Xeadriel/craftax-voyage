def mine_2_iron(state, log_fn, step_func):
    from craftax.craftax.constants import BlockType
    
    # I have a stone pickaxe (level 2) which can mine iron (requires level >= 2)
    # I have 0 iron currently, need 2 more
    target = state.inventory.iron + 2
    
    # First, explore until iron is in view
    state = explore_until(state, log_fn, step_func, BlockType.IRON, max_steps=60)
    
    # Then mine iron until I have 2
    for _ in range(2):
        if state.inventory.iron >= target:
            break
        state = mine_block(state, log_fn, step_func, BlockType.IRON, 1, max_steps=30)
    
    return state