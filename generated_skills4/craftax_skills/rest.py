# Description:
# Puts the player to rest to recover health.
# Returns True if successful, False if already resting or health is maxed.
# Handles rest mechanics and wake-up conditions.


def rest(state, max_steps=100):
    """
    Put the player to rest.

    Args:
        state: Current environment state
        max_steps: Maximum steps to attempt (default 100)

    Returns:
        bool: True if resting, False otherwise
    """

    # Check if already resting
    if state.is_resting:
        raise ValueError("Already resting")

    # Check if health is already maxed
    if state.player_health >= get_max_health(state):
        raise ValueError("Health is already at maximum - cannot rest")

    # Check if we're in a safe position (no mobs nearby)
    for x in range(OBS_DIM[0]):
        for y in range(OBS_DIM[1]):
            block_pos = state.player_position + jnp.array([x, y])
            if in_bounds(state, block_pos):
                if is_in_mob(state, block_pos):
                    raise ValueError(f"Cannot rest - mob at {block_pos}")

    # Put player to rest
    state = state.replace(is_resting=True)

    return True
