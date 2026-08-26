# Description:
# Mines a specific block type that is visible in the current view.
# Returns True if successfully mined, False if block not found or unreachable.
# Handles obstacles like water, mobs, and other blocks in the way.


def mine_block(state, block_type, max_steps=100):
    """
    Mine a block of the specified type.

    Args:
        state: Current environment state
        block_type: BlockType enum value to mine
        max_steps: Maximum steps to search and mine (default 100)

    Returns:
        bool: True if block mined, False otherwise
    """
    from craftax.craftax.constants import (
        Action,
        DIRECTIONS,
        in_bounds,
        is_in_solid_block,
        is_in_mob,
    )
    from craftax.craftax.game_logic import get_player_damage_vector

    # Check if we have the required tool
    if block_type == 4:  # COAL
        if state.inventory.pickaxe < 1:
            raise ValueError("Cannot mine coal without pickaxe level >= 1")
    elif block_type == 9:  # IRON
        if state.inventory.pickaxe < 2:
            raise ValueError("Cannot mine iron without pickaxe level >= 2")
    elif block_type == 10:  # DIAMOND
        if state.inventory.pickaxe < 3:
            raise ValueError("Cannot mine diamond without pickaxe level >= 3")
    elif block_type == 21:  # SAPPHIRE
        if state.inventory.pickaxe < 4:
            raise ValueError("Cannot mine sapphire without pickaxe level >= 4")
    elif block_type == 22:  # RUBY
        if state.inventory.pickaxe < 4:
            raise ValueError("Cannot mine ruby without pickaxe level >= 4")

    # Search for the block in the current view
    found_position = None
    for x in range(OBS_DIM[0]):
        for y in range(OBS_DIM[1]):
            block_pos = state.player_position + jnp.array([x, y])
            if in_bounds(state, block_pos):
                if (
                    state.map[state.player_level, block_pos[0], block_pos[1]]
                    == block_type
                ):
                    found_position = block_pos
                    break
        if found_position:
            break

    if not found_position:
        raise ValueError(f"Cannot find {BlockType(block_type).name} in current view")

    # Check if we can reach the block
    if is_in_solid_block(state, found_position):
        raise ValueError(
            f"Cannot mine {BlockType(block_type).name} at {found_position} - solid block"
        )

    if is_in_mob(state, found_position):
        raise ValueError(
            f"Cannot mine {BlockType(block_type).name} at {found_position} - mob present"
        )

    # Move to the block
    dx = found_position[0] - state.player_position[0]
    dy = found_position[1] - state.player_position[1]

    steps_taken = 0
    while steps_taken < max_steps:
        if abs(dx) <= 1 and abs(dy) <= 1:
            # Make final move to adjacent position
            if dx == 1:
                move_dir = Action.RIGHT
            elif dx == -1:
                move_dir = Action.LEFT
            elif dy == 1:
                move_dir = Action.DOWN
            elif dy == -1:
                move_dir = Action.UP

            state = state.replace(
                player_position=state.player_position + DIRECTIONS[move_dir.value],
                player_direction=move_dir.value,
            )
            break

        # Determine next move direction
        if abs(dx) >= abs(dy):
            if dx > 0:
                move_dir = Action.RIGHT
            else:
                move_dir = Action.LEFT
        else:
            if dy > 0:
                move_dir = Action.DOWN
            else:
                move_dir = Action.UP

        proposed_position = state.player_position + DIRECTIONS[move_dir.value]

        if not in_bounds(state, proposed_position):
            raise ValueError(f"Cannot reach {found_position} - out of bounds")

        if is_in_solid_block(state, proposed_position):
            raise ValueError(
                f"Cannot reach {found_position} - solid block at {proposed_position}"
            )

        if is_in_mob(state, proposed_position):
            raise ValueError(
                f"Cannot reach {found_position} - mob at {proposed_position}"
            )

        state = state.replace(
            player_position=proposed_position, player_direction=move_dir.value
        )

        dx = found_position[0] - state.player_position[0]
        dy = found_position[1] - state.player_position[1]
        steps_taken += 1

    # Mine the block
    state, did_attack_mob, did_kill_mob = attack_mob(
        state, found_position, get_player_damage_vector(state), True
    )

    return True
