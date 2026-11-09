def craft_1_wood_sword(state, log_fn, step_func):
    from craftax.craftax.constants import Action
    
    # Check I have enough wood (need 1 for a wood sword)
    if state.inventory.wood < 1:
        raise Exception("Not enough wood to craft wood sword (need 1, have {})".format(state.inventory.wood))
    
    # Crafting table is in view, so craft directly
    state = craft(state, log_fn, step_func, "wood_sword", 1, max_steps=20)
    
    return state