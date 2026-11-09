def craft_2_arrows(state, log_fn, step_func):
    from craftax.craftax.constants import Action
    
    # Check I have enough materials (1 wood + 1 stone for 1 craft = 2 arrows)
    if state.inventory.wood < 1:
        raise Exception("Not enough wood to craft arrows (need 1, have {})".format(state.inventory.wood))
    if state.inventory.stone < 1:
        raise Exception("Not enough stone to craft arrows (need 1, have {})".format(state.inventory.stone))
    
    # Crafting table is in view (5 tiles away)
    # Craft 1 batch of arrows (gives 2 arrows total)
    state = craft(state, log_fn, step_func, "arrow", 1, max_steps=20)
    
    return state