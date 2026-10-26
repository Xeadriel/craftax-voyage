def craft_iron_pickaxe(state, log_fn, step_func):
    from craftax.craftax.constants import Action
    
    log_fn("Crafting iron pickaxe")
    
    # Check if we already have an iron pickaxe or better
    if state.inventory.pickaxe >= 3:
        log_fn(f"Already have a {['none', 'wood', 'stone', 'iron', 'diamond'][min(state.inventory.pickaxe, 4)]} pickaxe")
        return state
    
    # Craft the iron pickaxe (requires 1 wood, 1 stone, 1 iron, 1 coal, and both table and furnace nearby)
    state = craft(state, log_fn, step_func, Action.MAKE_IRON_PICKAXE)
    
    log_fn("Iron pickaxe crafted successfully")
    
    return state