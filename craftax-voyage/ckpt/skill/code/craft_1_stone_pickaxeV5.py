def craft_1_stone_pickaxe(state, log_fn, step_func):
    from craftax.craftax.constants import Action, BlockType
    
    # Check I have enough materials (1 wood + 1 stone for stone pickaxe)
    if state.inventory.wood < 1:
        raise Exception("Not enough wood to craft stone pickaxe (need 1, have {})".format(state.inventory.wood))
    if state.inventory.stone < 1:
        raise Exception("Not enough stone to craft stone pickaxe (need 1, have {})".format(state.inventory.stone))
    
    # Explore until the crafting table is in view (use BlockType enum, not string)
    state = explore_until(state, log_fn, step_func, BlockType.CRAFTING_TABLE, max_steps=40)
    
    # Craft the stone pickaxe
    state = craft(state, log_fn, step_func, Action.MAKE_STONE_PICKAXE, 1, max_steps=20)
    
    return state