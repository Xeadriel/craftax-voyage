from craftax.craftax.constants import Action, BlockType

def mine_10_stone(state, log_fn, step_func):
    """
    Mines 10 stone blocks using a stone pickaxe.
    
    Args:
        state: Current EnvState
        log_fn: Logging function taking a single string
        step_func: Function taking an action id (int) and returning the new EnvState
        
    Returns:
        The final EnvState after mining 10 stone
    """
    log_fn("Starting to mine 10 stone")
    
    # Check current resources
    log_fn(f"Current resources: wood={state.inventory.wood}, stone={state.inventory.stone}")
    
    # Need to mine 7 more trees to get enough wood for crafting
    # Crafting table: 2 wood
    # Wood pickaxe: 1 wood
    # Stone pickaxe: 1 wood + 1 stone
    # Total wood needed: 4, but we'll mine 7 trees to be safe
    trees_to_mine = 7
    
    log_fn(f"Need to mine {trees_to_mine} more trees for crafting")
    
    # Mine trees one at a time
    for i in range(trees_to_mine):
        log_fn(f"Tree {i+1}/{trees_to_mine} - exploring for tree...")
        state = explore_until(state, log_fn, step_func, BlockType.TREE)
        
        log_fn(f"Tree {i+1}/{trees_to_mine} - mining...")
        state = mine_block(state, log_fn, step_func, BlockType.TREE, 1)
        
        log_fn(f"Tree {i+1}/{trees_to_mine} - done. Wood: {state.inventory.wood}")
    
    log_fn(f"Mined {trees_to_mine} trees. Total wood: {state.inventory.wood}")
    
    # Place crafting table (costs 2 wood)
    log_fn("Placing crafting table (costs 2 wood)...")
    state = place(state, log_fn, step_func, "crafting_table")
    log_fn(f"Crafting table placed. Wood remaining: {state.inventory.wood}")
    
    # Craft wood pickaxe (costs 1 wood)
    log_fn("Crafting wood pickaxe...")
    state = craft(state, log_fn, step_func, Action.MAKE_WOOD_PICKAXE)
    log_fn("Wood pickaxe crafted successfully!")
    
    # Mine 1 stone block
    log_fn("Mining stone...")
    state = explore_until(state, log_fn, step_func, BlockType.STONE)
    state = mine_block(state, log_fn, step_func, BlockType.STONE, 1)
    log_fn(f"Mined 1 stone. Stone count: {state.inventory.stone}")
    
    # Craft stone pickaxe (costs 1 wood + 1 stone)
    log_fn("Crafting stone pickaxe...")
    state = craft(state, log_fn, step_func, Action.MAKE_STONE_PICKAXE)
    log_fn("Stone pickaxe crafted successfully!")
    
    # Mine 10 stone blocks
    log_fn("Mining 10 stone blocks...")
    for i in range(10):
        log_fn(f"Stone {i+1}/10 - exploring for stone...")
        state = explore_until(state, log_fn, step_func, BlockType.STONE)
        
        log_fn(f"Stone {i+1}/10 - mining...")
        state = mine_block(state, log_fn, step_func, BlockType.STONE, 1)
        
        log_fn(f"Stone {i+1}/10 - done. Stone: {state.inventory.stone}")
    
    log_fn(f"Successfully mined 10 stone! Final stone count: {state.inventory.stone}")
    
    return state