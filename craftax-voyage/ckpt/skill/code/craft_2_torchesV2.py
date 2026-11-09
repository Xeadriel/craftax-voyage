def craft_2_torches(state, log_fn, step_func):
    from craftax.craftax.constants import Action, BlockType
    
    # First, explore until the crafting table is in view
    # It's seen at 7 tiles away, so we need to bring it into view
    state = explore_until(state, log_fn, step_func, BlockType.CRAFTING_TABLE, max_steps=40)
    
    # Check I have enough materials (1 wood + 1 coal per torch, so 2 of each for 2 torches)
    if state.inventory.wood < 2:
        raise Exception("Not enough wood to craft 2 torches (need 2, have {})".format(state.inventory.wood))
    if state.inventory.coal < 2:
        raise Exception("Not enough coal to craft 2 torches (need 2, have {})".format(state.inventory.coal))
    
    # Crafting table is now in view, so craft directly
    state = craft(state, log_fn, step_func, "torch", 2, max_steps=30)
    
    return state