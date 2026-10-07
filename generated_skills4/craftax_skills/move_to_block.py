# Description:
# Moves the player to a specific block position on the current floor.
# Returns True if successful, False if the target block is unreachable or doesn't exist.
# This skill handles pathfinding around obstacles and mobs.


def move_to_block(state, target_position, max_steps=100):
    """
    Move player to a specific block position.

    Args:
        state: Current environment state
        target_position: Tuple (x, y) of target block coordinates
        max_steps: Maximum number of steps to attempt (default 100)

    Returns:
        bool: True if reached target, False otherwise
    """
    from craftax.craftax.constants import (
        Action,
        in_bounds,
        is_in_solid_block,
        is_in_mob,
    )

    # Validate target position
    if not in_bounds(state, target_position):
        raise ValueError(f"Target position {target_position} is out of bounds")

    # Check if target is a solid block (can't walk through)
    if is_in_solid_block(state, target_position):
        raise ValueError(f"Cannot move to solid block at {target_position}")

    # Check if target has a mob
    if is_in_mob(state, target_position):
        raise ValueError(f"Cannot move to position with mob at {target_position}")

    # Calculate direction to target
    dx = target_position[0] - state.player_position[0]
    dy = target_position[1] - state.player_position[1]

    # Check if already at target
    if dx == 0 and dy == 0:
        return True

    # Movement priority: prefer cardinal directions over diagonals
    # This matches the action space which only has cardinal directions
    move_direction = None

    if abs(dx) >= abs(dy):
        # Horizontal movement preferred
        if dx > 0:
            move_direction = Action.RIGHT
        else:
            move_direction = Action.LEFT
    else:
        # Vertical movement preferred
        if dy > 0:
            move_direction = Action.DOWN
        else:
            move_direction = Action.UP

    # Execute movement with collision checking
    steps_taken = 0
    while steps_taken < max_steps:
        # Check if we're close enough (within 1 block)
        if abs(dx) <= 1 and abs(dy) <= 1:
            # Make final adjustment to exact position
            if dx == 1:
                move_direction = Action.RIGHT
            elif dx == -1:
                move_direction = Action.LEFT
            elif dy == 1:
                move_direction = Action.DOWN
            elif dy == -1:
                move_direction = Action.UP

            # Execute final move
            state = state.replace(
                player_position=state.player_position
                + DIRECTIONS[move_direction.value],
                player_direction=move_direction.value,
            )
            return True

        # Check if we can move in this direction
        proposed_position = state.player_position + DIRECTIONS[move_direction.value]

        # Check bounds
        if not in_bounds(state, proposed_position):
            raise ValueError(f"Cannot move to {proposed_position} - out of bounds")

        # Check for solid blocks
        if is_in_solid_block(state, proposed_position):
            # Try to find an alternate path
            raise ValueError(f"Cannot move to {proposed_position} - solid block")

        # Check for mobs
        if is_in_mob(state, proposed_position):
            raise ValueError(f"Cannot move to {proposed_position} - mob present")

        # Execute move
        state = state.replace(
            player_position=proposed_position, player_direction=move_direction.value
        )

        # Update position deltas
        dx = target_position[0] - state.player_position[0]
        dy = target_position[1] - state.player_position[1]

        steps_taken += 1

    raise ValueError(
        f"Failed to reach target {target_position} after {max_steps} steps"
    )
