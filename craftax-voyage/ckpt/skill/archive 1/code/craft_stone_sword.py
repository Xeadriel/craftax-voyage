from craftax.craftax.constants import Action

def craft_stone_sword(state, log_fn, step_func):
    """
    Crafts 1 stone sword if the player has enough wood and stone and a crafting table nearby.
    
    Args:
        state: Current EnvState
        log_fn: Logging function taking a single string
        step_func: Function taking an action id (int) and returning the new EnvState
        
    Returns:
        The final EnvState after crafting the stone sword
    """
    log_fn("Starting to craft stone sword")
    
    # Check if we have enough resources
    if state.inventory.wood < 1:
        log_fn("Need to find a tree for wood")
        state = explore_until(state, log_fn, step_func, BlockType.TREE)
        state = mine_block(state, log_fn, step_func, BlockType.TREE, 1)
    
    if state.inventory.wood < 1:
        log_fn("Still not enough wood (need 1, have {})".format(state.inventory.wood))
        # Try to find another tree
        state = explore_until(state, log_fn, step_func, BlockType.TREE)
        state = mine_block(state, log_fn, step_func, BlockType.TREE, 1)
    
    if state.inventory.stone < 1:
        log_fn("Need to find stone for crafting")
        state = explore_until(state, log_fn, step_func, BlockType.STONE)
        state = mine_block(state, log_fn, step_func, BlockType.STONE, 1)
    
    # Craft the stone sword
    log_fn("Crafting stone sword (needs 1 wood, 1 stone)")
    state = craft(state, log_fn, step_func, Action.MAKE_STONE_SWORD)
    
    log_fn("Stone sword crafted successfully! Current inventory: wood={}, stone={}".format(
        state.inventory.wood, state.inventory.stone))
    
    return state