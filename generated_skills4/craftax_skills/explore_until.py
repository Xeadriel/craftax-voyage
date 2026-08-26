# Description:
# Explores the environment in a random direction until a condition is met or max steps reached.
# Returns True if condition met, False if max steps reached.
# Useful for finding resources, chests, or specific blocks.


def explore_until(state, condition_fn, max_steps=100):
    """
    Explore until a condition is met.

    Args:
        state: Current environment state
        condition_fn: Function that takes state and returns True when condition is met
        max_steps: Maximum steps to explore (default 100)

    Returns:
        bool: True if condition met, False if max steps reached
    """
    from craftax.craftax.constants import (
        Action,
        DIRECTIONS,
        in_bounds,
        is_in_solid_block,
        is_in_mob,
    )

    steps_taken = 0
    directions = [Action.UP, Action.RIGHT, Action.DOWN, Action.LEFT]

    while steps_taken < max_steps:
        # Check condition
        if condition_fn(state):
            return True

        # Choose random direction
        rng_key = state.state_rng
        move_dir = directions[steps_taken % 4]

        # Calculate proposed position
        proposed_position = state.player_position + DIRECTIONS[move_dir.value]

        # Check bounds
        if not in_bounds(state, proposed_position):
            raise ValueError(f"Cannot explore - out of bounds at {proposed_position}")

        # Check for solid blocks
        if is_in_solid_block(state, proposed_position):
            # Try alternate direction
            alt_dir = directions[(steps_taken + 1) % 4]
            alt_position = state.player_position + DIRECTIONS[alt_dir.value]

            if in_bounds(state, alt_position) and not is_in_solid_block(
                state, alt_position
            ):
                state = state.replace(
                    player_position=alt_position, player_direction=alt_dir.value
                )
            else:
                raise ValueError(f"Cannot explore - solid block at {proposed_position}")
            continue

        # Check for mobs
        if is_in_mob(state, proposed_position):
            raise ValueError(f"Cannot explore - mob at {proposed_position}")

        # Move
        state = state.replace(
            player_position=proposed_position, player_direction=move_dir.value
        )

        steps_taken += 1

    return False
