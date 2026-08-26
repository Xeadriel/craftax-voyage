# Skill: shoot_arrow
# Purpose: Shoots an arrow at the mob in front of the player
# Required inputs: None (uses current direction)
# Preconditions:
#   - Player must have a bow in inventory
#   - Player must have arrows in inventory
#   - Player must have projectiles slot available
# Expected effects:
#   - Arrow is shot in player's facing direction
#   - Arrow is consumed from inventory
#   - Projectile is added to player's projectile slots
# Failure conditions:
#   - No bow in inventory
#   - No arrows in inventory
#   - No projectile slots available
# Explanation: Uses shoot_projectile from game_logic.py which handles arrow shooting
#           Requires bow and arrows from inventory to determine shooting capability
#           Arrow direction is based on player's current direction

import jax.numpy as jnp
from craftax.craftax.constants import ProjectileType
from craftax.craftax.craftax_state import EnvState


def shoot_arrow(state: EnvState) -> EnvState:
    """
    Shoots an arrow in the player's current facing direction.

    Args:
        state: Current environment state

    Returns:
        New state with arrow shot

    Raises:
        ValueError: If shooting is not possible
    """
    # Check if player has bow
    if state.inventory.bow <= 0:
        raise ValueError("No bow in inventory")

    # Check if player has arrows
    if state.inventory.arrows <= 0:
        raise ValueError("No arrows in inventory")

    # Check if player has projectile slots available
    if state.player_projectiles.mask[state.player_level].sum() >= 3:
        raise ValueError("No projectile slots available")

    # Get arrow direction
    arrow_direction = DIRECTIONS[state.player_direction]

    # Spawn projectile
    new_projectiles, new_directions = _spawn_projectile_logic(
        state, state.player_position, arrow_direction, ProjectileType.ARROW2.value
    )

    # Consume arrow
    new_inventory = state.inventory.replace(arrows=state.inventory.arrows - 1)

    return state.replace(
        player_projectiles=new_projectiles,
        player_projectile_directions=new_directions,
        inventory=new_inventory,
    )


def _spawn_projectile_logic(
    state: EnvState, position, direction, projectile_type
) -> tuple:
    """Internal logic for spawning a projectile."""
    # Find empty projectile slot
    empty_slot_index = jnp.argmax(
        jnp.logical_not(state.player_projectiles.mask[state.player_level])
    )

    # Create new projectile
    new_projectiles = state.player_projectiles.replace(
        position=state.player_projectiles.position.at[
            state.player_level, empty_slot_index
        ].set(position),
        mask=state.player_projectiles.mask.at[state.player_level, empty_slot_index].set(
            True
        ),
        type_id=state.player_projectiles.type_id.at[
            state.player_level, empty_slot_index
        ].set(projectile_type),
    )

    new_directions = state.player_projectile_directions.at[
        state.player_level, empty_slot_index
    ].set(direction)

    return new_projectiles, new_directions
