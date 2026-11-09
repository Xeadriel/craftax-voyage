def craft_1_wood_pickaxe(state, log_fn, step_func):
    from craftax.craftax.constants import Action, BlockType
    
    # Check I have enough wood (need 1 for a wood pickaxe)
    if state.inventory.wood < 1:
        raise Exception("Not enough wood to craft wood pickaxe (need 1, have {})".format(state.inventory.wood))
    
    # Crafting table has been seen at 10 tiles, need to bring it into view first
    state = explore_until(state, log_fn, step_func, BlockType.CRAFTING_TABLE, max_steps=40)
    
    # Craft the wood pickaxe
    state = craft(state, log_fn, step_func, Action.MAKE_WOOD_PICKAXE, 1, max_steps=20)
    
    return state