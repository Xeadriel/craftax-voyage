def craft_1_iron_pickaxe(state, log_fn, step_func):
    from craftax.craftax.constants import Action, BlockType
    
    # Check I have enough materials (1 wood + 1 stone + 1 iron + 1 coal for iron pickaxe)
    if state.inventory.wood < 1:
        raise Exception("Not enough wood to craft iron pickaxe (need 1, have {})".format(state.inventory.wood))
    if state.inventory.stone < 1:
        raise Exception("Not enough stone to craft iron pickaxe (need 1, have {})".format(state.inventory.stone))
    if state.inventory.iron < 1:
        raise Exception("Not enough iron to craft iron pickaxe (need 1, have {})".format(state.inventory.iron))
    if state.inventory.coal < 1:
        raise Exception("Not enough coal to craft iron pickaxe (need 1, have {})".format(state.inventory.coal))
    
    # Explore until the crafting table is in view
    state = explore_until(state, log_fn, step_func, BlockType.CRAFTING_TABLE, max_steps=40)
    
    # Craft the iron pickaxe (costs 1 wood + 1 stone + 1 iron + 1 coal, needs table + furnace nearby)
    state = craft(state, log_fn, step_func, Action.MAKE_IRON_PICKAXE, 1, max_steps=30)
    
    return state