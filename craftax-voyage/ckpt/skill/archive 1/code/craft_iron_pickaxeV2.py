from craftax.craftax.constants import Action, BlockType

def craft_iron_pickaxe(state, log_fn, step_func):
    """
    Crafts 1 iron pickaxe if the player has enough resources and stations.
    
    Args:
        state: Current EnvState
        log_fn: Logging function taking a single string
        step_func: Function taking an action id (int) returning the new EnvState
        
    Returns:
        The final EnvState after crafting the iron pickaxe
    """
    from craftax.craftax.constants import Action, BlockType
    
    log_fn("Starting to craft iron pickaxe")
    
    # Check if we have a stone pickaxe - if not, craft one first
    if state.inventory.pickaxe != "Stone Pickaxe":
        log_fn("Need to craft stone pickaxe first")
        
        # We need a crafting table - check if we have wood for it
        if state.inventory.wood < 2:
            log_fn("Need to find a tree for crafting table (need 2, have {})".format(state.inventory.wood))
            state = explore_until(state, log_fn, step_func, BlockType.TREE)
            state = mine_block(state, log_fn, step_func, BlockType.TREE, 1)
        
        # Place crafting table if needed (or use existing one)
        if state.inventory.wood >= 2:
            log_fn("Placing crafting table (costs 2 wood)")
            state = place(state, log_fn, step_func, "crafting_table")
            log_fn("Crafting table placed. Wood remaining: {}".format(state.inventory.wood))
        
        # Craft stone pickaxe (requires 1 wood, 1 stone)
        log_fn("Crafting stone pickaxe (costs 1 wood, 1 stone)")
        state = craft(state, log_fn, step_func, Action.MAKE_STONE_PICKAXE)
        log_fn("Stone pickaxe crafted successfully!")
    
    # Place the furnace if we don't have one
    if state.inventory.stone < 1:
        log_fn("Need to find stone for furnace (need 1, have {})".format(state.inventory.stone))
        state = explore_until(state, log_fn, step_func, BlockType.STONE)
        state = mine_block(state, log_fn, step_func, BlockType.STONE, 1)
    
    log_fn("Placing furnace (costs 1 stone)")
    state = place(state, log_fn, step_func, "furnace")
    log_fn("Furnace placed. Stone remaining: {}".format(state.inventory.stone))
    
    # Mine iron (requires stone pickaxe, which we now have)
    log_fn("Mining iron (need 1 iron for iron pickaxe)")
    state = explore_until(state, log_fn, step_func, BlockType.IRON)
    state = mine_block(state, log_fn, step_func, BlockType.IRON, 1)
    log_fn("Mined iron. Iron count: {}".format(state.inventory.iron))
    
    # Check if we have enough coal
    if state.inventory.coal < 1:
        log_fn("Need to find coal (need 1, have {})".format(state.inventory.coal))
        state = explore_until(state, log_fn, step_func, BlockType.COAL)
        state = mine_block(state, log_fn, step_func, BlockType.COAL, 1)
        log_fn("Mined coal. Coal count: {}".format(state.inventory.coal))
    
    # Verify we have all required resources
    if state.inventory.wood < 1:
        log_fn("Not enough wood for iron pickaxe")
        raise Exception("Not enough wood to craft iron pickaxe")
    
    if state.inventory.stone < 1:
        log_fn("Not enough stone for iron pickaxe")
        raise Exception("Not enough stone to craft iron pickaxe")
    
    if state.inventory.iron < 1:
        log_fn("Not enough iron for iron pickaxe")
        raise Exception("Not enough iron to craft iron pickaxe")
    
    if state.inventory.coal < 1:
        log_fn("Not enough coal for iron pickaxe")
        raise Exception("Not enough coal to craft iron pickaxe")
    
    # Craft the iron pickaxe
    log_fn("Crafting iron pickaxe")
    state = craft(state, log_fn, step_func, Action.MAKE_IRON_PICKAXE)
    
    log_fn("Iron pickaxe crafted successfully!")
    
    return state