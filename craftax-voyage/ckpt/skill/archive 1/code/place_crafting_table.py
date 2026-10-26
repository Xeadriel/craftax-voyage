def place_crafting_table(state, log_fn, step_func):
    from craftax.craftax.constants import BlockType
    
    # Check if we have enough wood (need 2 wood for crafting table)
    if state.inventory.wood < 2:
        log_fn("Not enough wood to place crafting table")
        return state
    
    # Check if we're near a crafting table (optional - we can place anywhere)
    # For now, we'll just place it in front of us
    
    # Place the crafting table in front of the player
    # The player is at position (0, 0) facing LEFT, so the tile (-1, 0) is in front
    # We can also use the automatic placement by not specifying a position
    state = place(state, log_fn, step_func, "crafting_table")
    
    return state