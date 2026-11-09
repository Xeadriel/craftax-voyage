def place_crafting_table(state, log_fn, step_func):
    # I have 5 wood, need 2 to place a crafting table
    if state.inventory.wood < 2:
        raise Exception("Not enough wood to place a crafting table (need 2, have {})".format(state.inventory.wood))
    
    # Place the crafting table on the tile in front of the player
    state = place(state, log_fn, step_func, "crafting_table")
    
    return state