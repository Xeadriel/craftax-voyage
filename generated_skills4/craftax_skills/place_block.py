# Description:
# Places a block at a specific position relative to the player.
# Returns True if successful, False if position invalid or insufficient materials.
# Handles placement on valid surfaces and checks for solid blocks.


def place_block(state, block_type, relative_position, max_steps=100):
    """
    Place a block at a position relative to the player.

    Args:
        state: Current environment state
        block_type: BlockType enum value to place
        relative_position: Tuple (x, y) relative to player position
        max_steps: Maximum steps to attempt (default 100)

    Returns:
        bool: True if block placed, False otherwise
    """
    from craftax.craftax.constants import (
        Action,
        DIRECTIONS,
        in_bounds,
        is_in_solid_block,
        CAN_PLACE_ITEM_BLOCKS,
    )

    # Calculate absolute position
    absolute_position = state.player_position + jnp.array(relative_position)

    # Check bounds
    if not in_bounds(state, absolute_position):
        raise ValueError(f"Cannot place block at {absolute_position} - out of bounds")

    # Check if position is occupied by solid block
    if is_in_solid_block(state, absolute_position):
        raise ValueError(
            f"Cannot place block at {absolute_position} - solid block present"
        )

    # Check if position has an item
    if (
        state.item_map[state.player_level, absolute_position[0], absolute_position[1]]
        != 0
    ):
        raise ValueError(f"Cannot place block at {absolute_position} - item present")

    # Check if position is valid for placement
    if block_type == BlockType.STONE.value:
        # Stone can be placed on water or empty space
        if (
            state.map[state.player_level, absolute_position[0], absolute_position[1]]
            not in CAN_PLACE_ITEM_BLOCKS
        ):
            raise ValueError(
                f"Cannot place stone at {absolute_position} - invalid surface"
            )
    elif block_type == BlockType.CRAFTING_TABLE.value:
        # Crafting table needs 2 wood
        if state.inventory.wood < 2:
            raise ValueError("Cannot place crafting table - need 2 wood")
    elif block_type == BlockType.FURNACE.value:
        # Furnace needs 1 stone
        if state.inventory.stone < 1:
            raise ValueError("Cannot place furnace - need 1 stone")
    elif block_type == BlockType.PLANT.value:
        # Plant needs sapling and grass
        if state.inventory.sapling < 1:
            raise ValueError("Cannot place plant - need sapling")
        if (
            state.map[state.player_level, absolute_position[0], absolute_position[1]]
            != BlockType.GRASS.value
        ):
            raise ValueError("Cannot place plant - needs grass")
    elif block_type == BlockType.TORCH.value:
        # Torch needs valid surface and no item
        if (
            state.map[state.player_level, absolute_position[0], absolute_position[1]]
            not in CAN_PLACE_ITEM_BLOCKS
        ):
            raise ValueError(
                f"Cannot place torch at {absolute_position} - invalid surface"
            )
        if (
            state.item_map[
                state.player_level, absolute_position[0], absolute_position[1]
            ]
            != 0
        ):
            raise ValueError(
                f"Cannot place torch at {absolute_position} - item present"
            )
        if state.inventory.torches < 1:
            raise ValueError("Cannot place torch - need torch")

    # Move to placement position
    dx = absolute_position[0] - state.player_position[0]
    dy = absolute_position[1] - state.player_position[1]

    steps_taken = 0
    while steps_taken < max_steps:
        if abs(dx) <= 1 and abs(dy) <= 1:
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
            raise ValueError("Cannot reach placement position - out of bounds")

        if is_in_solid_block(state, proposed_position):
            raise ValueError(
                f"Cannot reach placement position - solid block at {proposed_position}"
            )

        if is_in_mob(state, proposed_position):
            raise ValueError(
                f"Cannot reach placement position - mob at {proposed_position}"
            )

        state = state.replace(
            player_position=proposed_position, player_direction=move_dir.value
        )

        dx = absolute_position[0] - state.player_position[0]
        dy = absolute_position[1] - state.player_position[1]
        steps_taken += 1

    # Place the block
    state = place_block(state, action, static_params)

    return True
