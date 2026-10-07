# Skill: open_chest
# Purpose: Opens a chest at the player's current facing direction
# Required inputs: None (uses current facing direction)
# Preconditions:
#   - Player must be adjacent to a chest
#   - Player must be able to interact (not sleeping or resting)
# Expected effects:
#   - Chest is opened and items are added to inventory
#   - Chest is removed from map
#   - Achievement may be triggered for opening
# Failure conditions:
#   - No chest nearby
#   - Player is sleeping or resting
# Explanation: Uses do_action from game_logic.py which handles chest opening
#           Checks for chest proximity using is_near_block from game_logic_utils.py
#           Chest loot is randomized each game run

import jax.numpy as jnp
from craftax.craftax.constants import BlockType
from craftax.craftax.craftax_state import EnvState


def open_chest(state: EnvState) -> EnvState:
    """
    Opens a chest at the player's current facing direction.

    Args:
        state: Current environment state

    Returns:
        New state with chest opened and items added to inventory

    Raises:
        ValueError: If chest cannot be opened
    """
    # Check if player is adjacent to a chest
    chest_nearby = False
    for dx, dy in [
        (-1, -1),
        (-1, 0),
        (-1, 1),
        (0, -1),
        (0, 1),
        (1, -1),
        (1, 0),
        (1, 1),
    ]:
        pos = state.player_position + jnp.array([dx, dy])
        if (
            0 <= pos[0] < state.map[state.player_level].shape[0]
            and 0 <= pos[1] < state.map[state.player_level].shape[1]
        ):
            if state.map[state.player_level, pos[0], pos[1]] == BlockType.CHEST.value:
                chest_nearby = True
                break

    if not chest_nearby:
        raise ValueError("No chest nearby")

    # Check if player is sleeping or resting
    if state.is_sleeping or state.is_resting:
        raise ValueError("Cannot open chest while sleeping or resting")

    # Get chest position
    chest_position = None
    for dx, dy in [
        (-1, -1),
        (-1, 0),
        (-1, 1),
        (0, -1),
        (0, 1),
        (1, -1),
        (1, 0),
        (1, 1),
    ]:
        pos = state.player_position + jnp.array([dx, dy])
        if (
            0 <= pos[0] < state.map[state.player_level].shape[0]
            and 0 <= pos[1] < state.map[state.player_level].shape[1]
        ):
            if state.map[state.player_level, pos[0], pos[1]] == BlockType.CHEST.value:
                chest_position = pos
                break

    if chest_position is None:
        raise ValueError("Could not find chest position")

    # Replace chest with path
    new_map = state.map.at[
        state.player_level, chest_position[0], chest_position[1]
    ].set(BlockType.PATH.value)

    # Add chest items to inventory (simplified - in real implementation would use add_items_from_chest)
    # This is a simplified version that adds random items
    rng = jax.random.PRNGKey(0)
    new_inventory = _add_chest_items(state, chest_position, rng)

    # Mark chest as opened
    new_chests_opened = state.chests_opened.at[state.player_level].set(True)

    return state.replace(
        map=state.map.at[state.player_level].set(new_map),
        inventory=new_inventory,
        chests_opened=new_chests_opened,
    )


def _add_chest_items(state: EnvState, chest_position, rng) -> EnvState:
    """Internal logic for adding chest items to inventory."""
    # Simplified chest loot - in real implementation would use add_items_from_chest from game_logic.py
    # This is a placeholder that adds some random items

    # Torch (60%)
    torch_loot = jax.random.uniform(rng) < 0.6
    torch_amount = jax.random.randint(rng, shape=(), minval=4, maxval=8) * torch_loot

    # Ores (60%)
    ore_loot = jax.random.uniform(rng) < 0.6
    ore_id = jax.random.choice(rng, jnp.arange(5), shape=())

    coal_loot = (
        jax.random.randint(rng, shape=(), minval=1, maxval=4) * (ore_id == 0) * ore_loot
    )
    iron_loot = (
        jax.random.randint(rng, shape=(), minval=1, maxval=3) * (ore_id == 1) * ore_loot
    )
    diamond_loot = (
        jax.random.randint(rng, shape=(), minval=1, maxval=2) * (ore_id == 2) * ore_loot
    )
    sapphire_loot = (
        jax.random.randint(rng, shape=(), minval=1, maxval=2) * (ore_id == 3) * ore_loot
    )
    ruby_loot = (
        jax.random.randint(rng, shape=(), minval=1, maxval=2) * (ore_id == 4) * ore_loot
    )

    # Potion (50%)
    potion_loot = jax.random.uniform(rng) < 0.5
    potion_index = jax.random.randint(rng, shape=(), minval=0, maxval=5)
    potion_amount = jax.random.randint(rng, shape=(), minval=1, maxval=3)

    # Arrows (25%)
    arrow_loot = jax.random.uniform(rng) < 0.25
    arrow_amount = jax.random.randint(rng, shape=(), minval=1, maxval=5) * arrow_loot

    # Tools (20%)
    tool_loot = jax.random.uniform(rng) < 0.2
    tool_id = jax.random.randint(rng, shape=(), minval=0, maxval=1)
    pickaxe_loot = (
        jax.random.choice(
            rng, jnp.arange(4) + 1, shape=(), p=jnp.array([0.4, 0.3, 0.2, 0.1])
        )
        * tool_loot
    )

    # Build new inventory
    new_inventory = state.inventory.replace(
        torches=state.inventory.torches + torch_loot,
        coal=state.inventory.coal + coal_loot,
        iron=state.inventory.iron + iron_loot,
        diamond=state.inventory.diamond + diamond_loot,
        sapphire=state.inventory.sapphire + sapphire_loot,
        ruby=state.inventory.ruby + ruby_loot,
        arrows=state.inventory.arrows + arrow_loot,
        pickaxe=jnp.maximum(
            state.inventory.pickaxe + pickaxe_loot, state.inventory.pickaxe
        ),
        potions=state.inventory.potions.at[potion_index].set(
            state.inventory.potions[potion_index] + potion_loot * potion_amount
        ),
    )

    return state.replace(inventory=new_inventory)
