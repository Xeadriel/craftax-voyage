def craft_1_iron_sword(state, log_fn, step_func):
    from craftax.craftax.constants import Action
    
    # Check I have enough materials (1 wood + 1 stone + 1 iron + 1 coal for iron sword)
    if state.inventory.wood < 1:
        raise Exception("Not enough wood to craft iron sword (need 1, have {})".format(state.inventory.wood))
    if state.inventory.stone < 1:
        raise Exception("Not enough stone to craft iron sword (need 1, have {})".format(state.inventory.stone))
    if state.inventory.iron < 1:
        raise Exception("Not enough iron to craft iron sword (need 1, have {})".format(state.inventory.iron))
    if state.inventory.coal < 1:
        raise Exception("Not enough coal to craft iron sword (need 1, have {})".format(state.inventory.coal))
    
    # Crafting table and furnace are both in view, so craft directly
    state = craft(state, log_fn, step_func, Action.MAKE_IRON_SWORD, 1, max_steps=30)
    
    return state