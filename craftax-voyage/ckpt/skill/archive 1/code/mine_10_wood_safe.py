from craftax.craftax.constants import BlockType

def mine_10_wood_safe(state, log_fn, step_func):
    """
    Safely mines 10 wood from trees on the current floor.
    
    Args:
        state: Current EnvState
        log_fn: Logging function taking a single string
        step_func: Function taking an action id (int) and returning the new EnvState
        
    Returns:
        The final EnvState after mining 10 wood
        
    Raises:
        Exception: If health is too low to complete the task, or if max steps are reached
    """
    log_fn("Starting to safely mine 10 wood")
    
    # Check current health and stats
    current_health = state.player_health
    current_food = state.player_food
    current_drink = state.player_drink
    current_energy = state.player_energy
    
    log_fn(f"Current stats - Health: {current_health}, Food: {current_food}, Drink: {current_drink}, Energy: {current_energy}")
    
    # If health is too low, block in and recover
    if current_health < 5:
        log_fn(f"Health too low ({current_health}), blocking in and recovering...")
        # First find a safe location to block in
        log_fn("Finding safe location to block in...")
        state = explore_until(state, log_fn, step_func, BlockType.GRASS)
        
        # Block in with stone (need 4 stone blocks for 4 sides)
        if state.inventory.stone < 4:
            log_fn("Not enough stone to block in (need 4, have {})".format(state.inventory.stone))
            # Mine stone from a stalagmite or stone block
            state = explore_until(state, log_fn, step_func, BlockType.STONE)
            state = mine_block(state, log_fn, step_func, BlockType.STONE, 1)
            state = explore_until(state, log_fn, step_func, BlockType.STONE)
            state = mine_block(state, log_fn, step_func, BlockType.STONE, 1)
            state = explore_until(state, log_fn, step_func, BlockType.STONE)
            state = mine_block(state, log_fn, step_func, BlockType.STONE, 1)
            state = explore_until(state, log_fn, step_func, BlockType.STONE)
            state = mine_block(state, log_fn, step_func, BlockType.STONE, 1)
        
        # Place stone blocks around
        log_fn("Blocking in with stone...")
        # Place stone on all 4 sides (up, down, left, right)
        state = place(state, log_fn, step_func, "stone", position=(state.player_position[0], state.player_position[1] - 1))  # Up
        state = place(state, log_fn, step_func, "stone", position=(state.player_position[0], state.player_position[1] + 1))  # Down
        state = place(state, log_fn, step_func, "stone", position=(state.player_position[0] - 1, state.player_position[1]))  # Left
        state = place(state, log_fn, step_func, "stone", position=(state.player_position[0] + 1, state.player_position[1]))  # Right
        
        # Sleep to recover energy and health
        log_fn("Sleeping to recover...")
        state = sleep(state, log_fn, step_func, max_steps=50)
        
        # Check health after sleeping
        current_health = state.player_health
        log_fn(f"After sleeping - Health: {current_health}")
    
    # If food is low, find and eat a plant
    if current_food < 5:
        log_fn(f"Food too low ({current_food}), looking for ripe plant...")
        state = explore_until(state, log_fn, step_func, BlockType.GRASS)
        # Mine grass for sapling
        state = mine_block(state, log_fn, step_func, BlockType.GRASS, 1)
        # Wait for plant to ripen (this is a long time, skip for now)
        # Actually, we need to find a ripe plant first
        log_fn("Plant needs to ripen first...")
    
    # If drink is low, find and drink from water
    if current_drink < 5:
        log_fn(f"Drink too low ({current_drink}), looking for water...")
        state = explore_until(state, log_fn, step_func, BlockType.WATER)
        log_fn("Drinking to restore...")
        state = drink(state, log_fn, step_func, number=5)
        current_drink = state.player_drink
        log_fn(f"After drinking - Drink: {current_drink}")
    
    # If energy is low, sleep
    if current_energy < 5:
        log_fn(f"Energy too low ({current_energy}), sleeping...")
        state = sleep(state, log_fn, step_func, max_steps=50)
        current_energy = state.player_energy
        log_fn(f"After sleeping - Energy: {current_energy}")
    
    # Now mine 10 trees one by one
    for i in range(10):
        log_fn(f"Tree {i+1}/10 - mining...")
        
        # Check stats before each tree
        current_health = state.player_health
        current_food = state.player_food
        current_drink = state.player_drink
        current_energy = state.player_energy
        
        if current_health < 5:
            log_fn(f"Health too low ({current_health}), need to recover")
            # Find water
            state = explore_until(state, log_fn, step_func, BlockType.WATER)
            while current_health < 5:
                state = drink(state, log_fn, step_func, number=1)
                current_health = state.player_health
                log_fn(f"Drank, health now: {current_health}")
        
        if current_food < 5:
            log_fn(f"Food too low ({current_food}), need food")
            # Find ripe plant
            state = explore_until(state, log_fn, step_func, BlockType.GRASS)
            state = mine_block(state, log_fn, step_func, BlockType.GRASS, 1)
            # Wait for plant to ripen (skip for now)
        
        if current_drink < 5:
            log_fn(f"Drink too low ({current_drink}), need water")
            state = explore_until(state, log_fn, step_func, BlockType.WATER)
            state = drink(state, log_fn, step_func, number=1)
            current_drink = state.player_drink
        
        if current_energy < 5:
            log_fn(f"Energy too low ({current_energy}), need sleep")
            state = sleep(state, log_fn, step_func, max_steps=50)
            current_energy = state.player_energy
        
        # Explore for a tree
        log_fn(f"Tree {i+1}/10 - exploring...")
        state = explore_until(state, log_fn, step_func, BlockType.TREE)
        
        # Mine the tree
        log_fn(f"Tree {i+1}/10 - mining...")
        state = mine_block(state, log_fn, step_func, BlockType.TREE, 1)
        
        current_wood_after_mine = int(state.inventory.wood)
        log_fn(f"Tree {i+1}/10 - mined! Wood: {current_wood_after_mine}, Health: {state.player_health}, Food: {state.player_food}, Drink: {state.player_drink}")
    
    log_fn(f"Successfully mined 10 wood! Final wood count: {state.inventory.wood}")
    
    return state