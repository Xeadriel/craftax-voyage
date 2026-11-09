def open_1_chest(state, log_fn, step_func):
    from craftax.craftax.constants import BlockType
    
    # First, descend to floor 1 where chests are available
    # The ladder down is open and 7 tiles away
    state = descend_ladder(state, log_fn, step_func, max_steps=20)
    
    # Then explore until a chest is visible on floor 1
    state = explore_until(state, log_fn, step_func, BlockType.CHEST, max_steps=60)
    
    # Finally, open 1 chest
    state = open_chest(state, log_fn, step_func, number=1, max_steps=30)
    
    return state