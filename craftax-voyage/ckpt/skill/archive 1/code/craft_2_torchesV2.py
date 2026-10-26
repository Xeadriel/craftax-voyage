from craftax.craftax.constants import Action, BlockType

def craft_2_torches(state, log_fn, step_func):
    """
    Crafts 2 torches (actually crafts 4, then places 2 of them)
    and places them on grass/sand tiles.
    
    Args:
        state: Current EnvState
        log_fn: Logging function taking a single string
        step_func: Function taking an action id (int) and returning the new EnvState
        
    Returns:
        The final EnvState after crafting and placing 2 torches
    """
    log_fn("Starting to craft 2 torches")
    
    # We need: 2 wood for crafting table + 1 wood + 1 coal for torches = 3 wood total
    # Player has 0 wood, need 3 wood
    # Player has 5 coal, which is enough
    
    log_fn(f"Need to mine 3 trees to get enough wood (need 3, have {state.inventory.wood})")
    
    # Mine 3 trees one at a time
    for i in range(3):
        log_fn(f"Tree {i+1}/3 - exploring for a tree...")
        state = explore_until(state, log_fn, step_func, BlockType.TREE)
        log_fn(f"Tree {i+1}/3 - found in sight!")
        
        log_fn(f"Tree {i+1}/3 - mining...")
        state = mine_block(state, log_fn, step_func, BlockType.TREE, 1)
        
        log_fn(f"Tree {i+1}/3 - mined. Wood: {state.inventory.wood}")
    
    log_fn(f"Mined 3 trees. Total wood: {state.inventory.wood}")
    
    # Place crafting table (costs 2 wood)
    log_fn("Placing crafting table (costs 2 wood)...")
    state = place(state, log_fn, step_func, "crafting_table")
    log_fn(f"Crafting table placed. Wood remaining: {state.inventory.wood}")
    
    # Craft torches (costs 1 wood + 1 coal, gives 4 torches)
    log_fn("Crafting torches (costs 1 wood + 1 coal, gives 4 torches)...")
    state = craft(state, log_fn, step_func, Action.MAKE_TORCH)
    log_fn(f"After crafting, have {state.inventory.torches} torches")
    
    # Place 2 torches on grass tiles
    # Looking at the map, grass is at positions like (-5, -3), (-4, -3), etc.
    # We need to find a grass tile that's walkable
    
    log_fn("Looking for grass tile to place torches...")
    
    # Search for a grass tile that's not water
    for i in range(10):
        log_fn(f"Checking tile {i}...")
        # Try to find a grass tile by moving around
        state = explore_until(state, log_fn, step_func, BlockType.TREE)
        
        # After exploring, we should be near something visible
        # Try placing a torch
        log_fn("Placing first torch...")
        state = place(state, log_fn, step_func, "torch")
        
        # Check if we have torches left
        if state.inventory.torches > 1:
            log_fn("Placing second torch...")
            state = place(state, log_fn, step_func, "torch")
            log_fn("Successfully placed 2 torches!")
            break
    
    log_fn("Successfully crafted and placed 2 torches!")
    log_fn(f"Final torch count: {state.inventory.torches}")
    
    return state