# Description:
# Collects a specific resource from the environment.
# Returns True if resource collected, False if resource not found.
# Handles mining, gathering, and resource management.


def collect_resource(state, resource_type, max_steps=100):
    """
    Collect a specific resource.

    Args:
        state: Current environment state
        resource_type: Type of resource to collect (wood, stone, coal, iron, diamond, etc.)
        max_steps: Maximum steps to search and collect (default 100)

    Returns:
        bool: True if resource collected, False otherwise
    """
    from craftax.craftax.constants import in_bounds, BlockType

    # Map resource names to block types
    resource_to_block = {
        "wood": BlockType.TREE,
        "stone": BlockType.STONE,
        "coal": BlockType.COAL,
        "iron": BlockType.IRON,
        "diamond": BlockType.DIAMOND,
        "sapphire": BlockType.SAPPHIRE,
        "ruby": BlockType.RUBY,
        "sapling": BlockType.GRASS,  # Saplings spawn on grass
    }

    if resource_type not in resource_to_block:
        raise ValueError(f"Unknown resource type: {resource_type}")

    block_type = resource_to_block[resource_type]

    # Check if we have the required tool
    if (
        block_type == BlockType.COAL
        or block_type == BlockType.IRON
        or block_type == BlockType.DIAMOND
        or block_type == BlockType.SAPPHIRE
        or block_type == BlockType.RUBY
    ):
        if state.inventory.pickaxe < 1:
            raise ValueError(f"Cannot collect {resource_type} without pickaxe")

    # Search for the resource
    found_position = None
    for x in range(OBS_DIM[0]):
        for y in range(OBS_DIM[1]):
            block_pos = state.player_position + jnp.array([x, y])
            if in_bounds(state, block_pos):
                if (
                    state.map[state.player_level, block_pos[0], block_pos[1]]
                    == block_type.value
                ):
                    found_position = block_pos
                    break
        if found_position:
            break

    if not found_position:
        raise ValueError(f"Cannot find {resource_type} in current view")

    # Mine the resource
    state, did_attack_mob, did_kill_mob = attack_mob(
        state, found_position, get_player_damage_vector(state), True
    )

    return True
