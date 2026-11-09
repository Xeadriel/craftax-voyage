def craft_2_arrows(state, log_fn, step_func):
    from craftax.craftax.constants import Action, BlockType
    
    # Check I have enough materials (1 wood + 1 stone = 2 arrows per craft)
    if state.inventory.wood < 1:
        raise Exception("Not enough wood to craft arrows (need 1, have {})".format(state.inventory.wood))
    if state.inventory.stone < 1:
        raise Exception("Not enough stone to craft arrows (need 1, have {})".format(state.inventory.stone))
    
    # Explore until the crafting table is in view
    state = explore_until(state, log_fn, step_func, BlockType.CRAFTING_TABLE, max_steps=40)
    
    # Craft 1 batch of arrows (gives 2 arrows total)
    state = craft(state, log_fn, step_func, "arrow", 1, max_steps=20)
    
    return state