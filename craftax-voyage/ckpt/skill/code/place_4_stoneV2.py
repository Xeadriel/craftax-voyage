def place_4_stone(state, log_fn, step_func):
    from craftax.craftax.constants import Action, BlockType
    
    # I have 7 stone, need to place 4 more
    # Check I have enough stone
    if state.inventory.stone < 4:
        raise Exception("Not enough stone to place 4 blocks (need 4, have {})".format(state.inventory.stone))
    
    # Place 4 stone blocks
    for i in range(4):
        state = place(state, log_fn, step_func, "stone", max_steps=20)
        log_fn("Placed stone block {}".format(i + 1))
    
    return state