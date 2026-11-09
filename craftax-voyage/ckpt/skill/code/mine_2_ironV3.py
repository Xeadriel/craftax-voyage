def mine_2_iron(state, log_fn, step_func):
    from craftax.craftax.constants import BlockType
    
    # Check I have a stone pickaxe (level >= 2) to mine iron
    if state.inventory.pickaxe < 2:
        # Craft a stone pickaxe first (1 wood + 1 stone)
        if state.inventory.wood < 1:
            raise Exception("Not enough wood to craft stone pickaxe (need 1, have {})".format(state.inventory.wood))
        if state.inventory.stone < 1:
            raise Exception("Not enough stone to craft stone pickaxe (need 1, have {})".format(state.inventory.stone))
        
        # Explore until crafting table is in view
        state = explore_until(state, log_fn, step_func, BlockType.CRAFTING_TABLE, max_steps=40)
        
        # Craft stone pickaxe
        state = craft(state, log_fn, step_func, "stone_pickaxe", 1, max_steps=20)
    
    # Target: 2 more iron on top of what we have now
    target = state.inventory.iron + 2
    
    # Mine iron blocks one at a time, exploring for more between each
    for _ in range(2):
        if state.inventory.iron >= target:
            break
        
        # Explore until iron is in view
        state = explore_until(state, log_fn, step_func, BlockType.IRON, max_steps=80)
        
        # Mine 1 iron block
        state = mine_block(state, log_fn, step_func, BlockType.IRON, 1, max_steps=30)
    
    return state