def craft_iron_sword(state, log_fn, step_func):
    from craftax.craftax.constants import Action, BlockType
    
    log_fn("Crafting 1 iron sword")
    
    # Check if we already have an iron sword or better
    if state.inventory.sword >= 3:
        log_fn(f"Already have a {['none', 'wood', 'stone', 'iron', 'diamond'][min(state.inventory.sword, 4)]} sword")
        return state
    
    # Check if we have enough resources
    wood_needed = 1
    stone_needed = 1
    iron_needed = 1
    coal_needed = 1
    
    if state.inventory.wood < wood_needed:
        log_fn(f"Need {wood_needed} wood, have {state.inventory.wood}")
        raise Exception(f"Not enough wood to craft iron sword. Need {wood_needed}, have {state.inventory.wood}")
    
    if state.inventory.stone < stone_needed:
        log_fn(f"Need {stone_needed} stone, have {state.inventory.stone}")
        raise Exception(f"Not enough stone to craft iron sword. Need {stone_needed}, have {state.inventory.stone}")
    
    if state.inventory.iron < iron_needed:
        log_fn(f"Need {iron_needed} iron, have {state.inventory.iron}")
        raise Exception(f"Not enough iron to craft iron sword. Need {iron_needed}, have {state.inventory.iron}")
    
    if state.inventory.coal < coal_needed:
        log_fn(f"Need {coal_needed} coal, have {state.inventory.coal}")
        raise Exception(f"Not enough coal to craft iron sword. Need {coal_needed}, have {state.inventory.coal}")
    
    # Explore to find a crafting station (crafting table and furnace needed for iron items)
    log_fn("Exploring to find crafting stations")
    state = explore_until(state, log_fn, step_func, BlockType.CRAFTING_TABLE, max_steps=30)
    
    # Craft the iron sword
    log_fn("Crafting iron sword")
    state = craft(state, log_fn, step_func, Action.MAKE_IRON_SWORD, number=1, max_steps=30)
    
    log_fn(f"Iron sword crafted. Current sword: {state.inventory.sword}")
    
    return state