def place_1_crafting_table(state, log_fn, step_func):
    from craftax.craftax.constants import Action, BlockType
    
    # Check I have enough wood (need 2 for a crafting table)
    if state.inventory.wood < 2:
        raise Exception("Not enough wood to place a crafting table (need 2, have {})".format(state.inventory.wood))
    
    # Place the crafting table on a tile in front of the player
    # The function will automatically choose a valid known position
    state = place(state, log_fn, step_func, "crafting_table", max_steps=20)
    
    return state