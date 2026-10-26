from craftax.craftax.constants import Action

def craft_iron_sword(state, log_fn, step_func):
    """
    Crafts 1 iron sword using available resources and stations.
    
    Args:
        state: Current EnvState
        log_fn: Logging function taking a single string
        step_func: Function taking an action id (int) and returning the new EnvState
        
    Returns:
        The final EnvState after crafting the iron sword
    """
    log_fn("Crafting iron sword")
    
    # Check if we have all required resources
    if state.inventory.wood < 1:
        log_fn("Need to find a tree for wood")
        state = explore_until(state, log_fn, step_func, BlockType.TREE)
        state = mine_block(state, log_fn, step_func, BlockType.TREE, 1)
    
    if state.inventory.stone < 1:
        log_fn("Need to find stone for crafting")
        state = explore_until(state, log_fn, step_func, BlockType.STONE)
        state = mine_block(state, log_fn, step_func, BlockType.STONE, 1)
    
    if state.inventory.iron < 1:
        log_fn("Need to find iron for crafting")
        state = explore_until(state, log_fn, step_func, BlockType.IRON)
        state = mine_block(state, log_fn, step_func, BlockType.IRON, 1)
    
    if state.inventory.coal < 1:
        log_fn("Need to find coal for crafting")
        state = explore_until(state, log_fn, step_func, BlockType.COAL)
        state = mine_block(state, log_fn, step_func, BlockType.COAL, 1)
    
    # Craft the iron sword
    state = craft(state, log_fn, step_func, Action.MAKE_IRON_SWORD)
    
    log_fn("Iron sword crafted successfully!")
    
    return state