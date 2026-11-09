def craft_1_torch(state, log_fn, step_func):
    from craftax.craftax.constants import Action
    
    # Check I have enough materials (1 wood + 1 coal for 1 torch)
    if state.inventory.wood < 1:
        raise Exception("Not enough wood to craft torch (need 1, have {})".format(state.inventory.wood))
    if state.inventory.coal < 1:
        raise Exception("Not enough coal to craft torch (need 1, have {})".format(state.inventory.coal))
    
    # Crafting table is in view, so craft directly
    state = craft(state, log_fn, step_func, "torch", 1, max_steps=20)
    
    return state