def craft_1_stone_sword(state, log_fn, step_func):
    from craftax.craftax.constants import Action
    
    # Check I have enough materials (1 wood + 1 stone for stone sword)
    if state.inventory.wood < 1:
        raise Exception("Not enough wood to craft stone sword (need 1, have {})".format(state.inventory.wood))
    if state.inventory.stone < 1:
        raise Exception("Not enough stone to craft stone sword (need 1, have {})".format(state.inventory.stone))
    
    # Crafting table is in view (2 tiles away), so craft directly
    state = craft(state, log_fn, step_func, Action.MAKE_STONE_SWORD, 1, max_steps=20)
    
    return state