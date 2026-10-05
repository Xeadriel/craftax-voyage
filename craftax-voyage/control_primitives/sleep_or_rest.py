# Description:
# Moves to a safe location, places a block to close the entrance, and enters sleep or rest state.
# Returns True if successful, throws error if health decreased or character died.

def sleep_or_rest(state, step_fn, log_fn):
    """
    Control primitive that moves the character to a safe location, places a block
    to close the entrance, and enters sleep or rest state until completion.
    
    Args:
        state: Current game state
        step_fn: Step function that takes an Action enum and returns the next state
        log_fn: Logging function for debugging purposes
    
    Returns:
        True if the sleep/rest operation completed successfully without errors
    
    Raises:
        ValueError: If character health decreased during the operation
        RuntimeError: If character died during the operation
    """
    # Check prerequisites
    if state.player_health <= 0:
        raise RuntimeError("Character is already dead and cannot sleep or rest")
    
    # Store initial health for comparison
    initial_health = state.player_health
    
    # Check if already sleeping or resting
    if state.is_sleeping or state.is_resting:
        log_fn("Character is already sleeping or resting, skipping sleep/rest primitive")
        return True
    
    # Determine if we should sleep or rest based on intrinsics
    should_sleep = state.player_energy < 7  # Energy threshold for sleeping
    should_rest = state.player_health < 8 and state.player_energy >= 7  # Health threshold for resting
    
    if not should_sleep and not should_rest:
        log_fn("Character does not need to sleep or rest (energy: {}, health: {})".format(
            state.player_energy, state.player_health
        ))
        return True
    
    # Determine action to use
    if should_sleep:
        action = Action.SLEEP
        log_fn("Entering sleep state")
    else:
        action = Action.REST
        log_fn("Entering rest state")
    
    # Step 1: Move to a safe location
    # Find a safe position (not in lava, not in mobs, not in walls)
    safe_position = find_safe_position(state, log_fn)
    
    if safe_position is None:
        raise RuntimeError("No safe location found to sleep or rest")
    
    # Move to the safe position
    log_fn("Moving to safe position: {}".format(safe_position))
    move_to_safe_position(state, safe_position, log_fn)
    
    # Step 2: Place a block to close the entrance
    # Find the direction we came from and place a block
    log_fn("Attempting to place block to close entrance")
    place_block_to_close_entrance(state, safe_position, log_fn)
    
    # Step 3: Execute sleep or rest state
    # Sleep and rest cannot be interrupted, so we need to run steps until complete
    log_fn("Executing sleep/rest state")
    execute_sleep_or_rest_state(state, action, log_fn)
    
    # Verify the operation completed successfully
    final_health = state.player_health
    
    if final_health < initial_health:
        raise ValueError("Character health decreased from {} to {} during sleep/rest".format(
            initial_health, final_health
        ))
    
    if final_health <= 0:
        raise RuntimeError("Character died during sleep/rest operation")
    
    return True


def find_safe_position(state, log_fn):
    """
    Find a safe position for sleeping/resting.
    
    A safe position must:
    - Be within map bounds
    - Not be in lava
    - Not be in a solid block
    - Not be occupied by a mob
    - Not be the player's current position
    """
    # Get map dimensions
    map_level = state.player_level
    map_size = state.map[map_level].shape
    
    # Search for safe positions
    for x in range(map_size[0]):
        for y in range(map_size[1]):
            position = jnp.array([x, y])
            
            # Check bounds
            if not (0 <= position[0] < map_size[0] and 0 <= position[1] < map_size[1]):
                continue
            
            # Check if in lava
            block_type = state.map[map_level, position[0], position[1]]
            if block_type == BlockType.LAVA.value:
                continue
            
            # Check if in solid block
            if is_in_solid_block(state, position):
                continue
            
            # Check if occupied by mob
            if is_in_mob(state, position):
                continue
            
            # Check if player is already there
            if jnp.all(state.player_position == position):
                continue
            
            # Found a safe position
            log_fn("Found safe position at: {}".format(position))
            return position
    
    log_fn("No safe position found")
    return None


def move_to_safe_position(state, target_position, log_fn):
    """
    Move the player to the target safe position.
    """
    # Get current position and direction
    current_position = state.player_position
    current_direction = state.player_direction
    
    # Calculate direction to target
    dx = target_position[0] - current_position[0]
    dy = target_position[1] - current_position[1]
    
    # Find the direction that moves us closer to target
    if dx != 0 and dy != 0:
        # Diagonal movement - choose the direction with larger component
        if abs(dx) > abs(dy):
            direction = Action.LEFT if dx < 0 else Action.RIGHT
        else:
            direction = Action.UP if dy < 0 else Action.DOWN
    elif dx != 0:
        direction = Action.LEFT if dx < 0 else Action.RIGHT
    else:
        direction = Action.UP if dy < 0 else Action.DOWN
    
    # Move towards target
    while not jnp.all(target_position == current_position):
        # Check if we can move in the current direction
        proposed_position = current_position + DIRECTIONS[current_direction]
        
        if is_position_in_bounds_not_in_mob_not_colliding(
            state, proposed_position, COLLISION_LAND_CREATURE
        ):
            # Move in current direction
            step_fn(DIRECTIONS[current_direction])
            current_position = state.player_position
            current_direction = state.player_direction
        else:
            # Try to find a valid direction
            valid_direction = find_valid_direction(state, target_position, current_direction)
            
            if valid_direction is not None:
                step_fn(valid_direction)
                current_position = state.player_position
                current_direction = state.player_direction
            else:
                # Cannot move further, break
                log_fn("Cannot move to target position, stopping at: {}".format(current_position))
                break
    
    log_fn("Reached target position: {}".format(target_position))


def find_valid_direction(state, target_position, current_direction):
    """
    Find a valid direction to move towards target.
    """
    # Try all 4 cardinal directions
    directions = [Action.LEFT, Action.RIGHT, Action.UP, Action.DOWN]
    
    for direction in directions:
        proposed_position = state.player_position + DIRECTIONS[direction]
        
        if is_position_in_bounds_not_in_mob_not_colliding(
            state, proposed_position, COLLISION_LAND_CREATURE
        ):
            # Check if this direction moves us closer to target
            dx = target_position[0] - state.player_position[0]
            dy = target_position[1] - state.player_position[1]
            
            if direction == Action.LEFT and dx < 0:
                continue
            if direction == Action.RIGHT and dx > 0:
                continue
            if direction == Action.UP and dy < 0:
                continue
            if direction == Action.DOWN and dy > 0:
                continue
            
            return direction
    
    return None


def place_block_to_close_entrance(state, safe_position, log_fn):
    """
    Place a block to close the entrance to the safe position.
    This is done by placing a block in the direction the player came from.
    """
    # Get current position and direction
    current_position = state.player_position
    current_direction = state.player_direction
    
    # Calculate the direction we came from (opposite of current direction)
    opposite_direction = (current_direction + 2) % 4
    
    # Calculate the entrance position
    entrance_position = safe_position + DIRECTIONS[opposite_direction]
    
    # Check if we can place a block there
    if is_position_in_bounds_not_in_mob_not_colliding(
        state, entrance_position, COLLISION_LAND_CREATURE
    ):
        # Place a stone block
        log_fn("Placing stone block at entrance position: {}".format(entrance_position))
        step_fn(Action.PLACE_STONE)
    else:
        log_fn("Cannot place block at entrance position: {}".format(entrance_position))


def execute_sleep_or_rest_state(state, action, log_fn):
    """
    Execute the sleep or rest state until completion.
    Sleep and rest cannot be interrupted, so we run steps until the state concludes.
    """
    # Sleep and rest are non-interruptible states
    # We need to run steps until the state naturally concludes
    
    # Check if already in sleep/rest state
    if state.is_sleeping or state.is_resting:
        log_fn("Already in sleep/rest state, skipping execution")
        return
    
    # Enter sleep/rest state
    step_fn(action)
    
    # Continue running steps until sleep/rest concludes
    # This is done by waiting for intrinsic decay or external interruption
    max_steps = 100  # Safety limit to prevent infinite loops
    
    for step in range(max_steps):
        # Check if we're still in sleep/rest state
        if state.is_sleeping or state.is_resting:
            # Continue waiting for the state to conclude
            # In Craftax, sleep/rest concludes when:
            # - Energy/health reaches max (for sleep)
            # - Health reaches max or food/drink reaches 0 (for rest)
            # - Player is attacked
            # - Player is interrupted by another action
            
            # Check if we should continue
            if state.player_energy < 7 and state.is_sleeping:
                # Still need to sleep
                continue
            elif state.player_health < 8 and state.is_resting:
                # Still need to rest
                continue
            elif state.player_energy >= 7 and state.is_sleeping:
                # Energy is sufficient, can wake up
                log_fn("Sleep state concluded, waking up")
                break
            elif state.player_health >= 8 or state.player_food <= 0 or state.player_drink <= 0:
                # Health sufficient or needs to wake up
                log_fn("Rest state concluded, waking up")
                break
            else:
                # Continue waiting
                continue
        else:
            # Not in sleep/rest state, we're done
            log_fn("Sleep/rest state concluded")
            break
        
        # Take a step to allow game logic to progress
        step_fn(Action.NOOP)
    
    log_fn("Sleep/rest execution completed after {} steps".format(step + 1))
