def mine_2_iron(state, log_fn, step_func):
    from craftax.craftax.constants import BlockType
    
    # I have a stone pickaxe (level 2) which can mine iron (requires level >= 2)
    # I have 1 iron currently, need 2 more (total of 3)
    target = state.inventory.iron + 2
    
    # First, explore until iron is in view with a larger budget
    state = explore_until(state, log_fn, step_func, BlockType.IRON, max_steps=80)
    
    # Mine 1 iron
    state = mine_block(state, log_fn, step_func, BlockType.IRON, 1, max_steps=30)
    
    # Explore again until another iron is in view
    state = explore_until(state, log_fn, step_func, BlockType.IRON, max_steps=80)
    
    # Mine the second iron
    state = mine_block(state, log_fn, step_func, BlockType.IRON, 1, max_steps=30)
    
    return state