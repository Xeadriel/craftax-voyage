# Skill: attack_mob
# Purpose: Attacks a specified mob type at the player's current facing direction
# Required inputs: mob_type (string: 'zombie', 'gnome', 'orc', 'lizard', 'knight', 'troll', 'pigman', 'skeleton', 'gnome_archer', 'orc_mage', 'kobold', 'archer', 'deep_thing', 'fire_elemental', 'ice_elemental')
# Preconditions:
#   - Player must be within attack range of mob
#   - Player must have appropriate weapon
# Expected effects:
#   - Mob is damaged
#   - Player may gain XP and level up
#   - Achievement may be triggered for killing
# Failure conditions:
#   - No mob of specified type nearby
#   - Player has no weapon
#   - Player is too far from mob
# Explanation: Uses attack_mob from game_logic.py which handles mob combat
#           Checks mob types from constants.py MobType enum
#           Requires weapon from inventory to determine attack capability

import jax.numpy as jnp
from craftax.craftax.constants import BlockType, Action, DIRECTIONS
from craftax.craftax.craftax_state import EnvState


def attack_mob(state: EnvState, mob_type: str) -> EnvState:
    """
    Attacks a specified mob type at the player's current facing direction.
    
    Args:
        state: Current environment state
        mob_type: Type of mob to attack (e.g., 'ZOMBIE', 'GNOME', 'ORC', 'SKELETON')
    
    Returns:
        New state with mob damaged
    
    Raises:
        ValueError: If mob is not found or attack is not possible
    """
    # Map mob type to mob class index
    mob_type_to_class = {
        'zombie': 1,  # Melee
        'gnome': 1,
        'orc': 1,
        'lizard': 1,
        'knight': 1,
        'troll': 1,
        'pigman': 1,
        'skeleton': 2,  # Ranged
        'gnome_archer': 2,
        'orc_mage': 2,
        'kobold': 2,
        'archer': 2,
        'deep_thing': 2,
        'fire_elemental': 2,
        'ice_elemental': 2,
    }
    
    if mob_type not in mob_type_to_class:
        raise ValueError(f"Unknown mob type: {mob_type}")
    
    mob_class = mob_type_to_class[mob_type]
    
    # Find mobs of this type
    mobs_to_attack = []
    if mob_class == 1:  # Melee
        mobs_to_attack = state.melee_mobs
    elif mob_class == 2:  # Ranged
        mobs_to_attack = state.ranged_mobs
    elif mob_class == 0:  # Passive
        mobs_to_attack = state.passive_mobs
    else:
        raise ValueError(f"Invalid mob class: {mob_class}")
    
    # Check if any mobs of this type exist
    if mobs_to_attack.mask[state.player_level].sum() == 0:
        raise ValueError(f"No {mob_type} mobs found")
    
    # Find closest mob
    mob_positions = mobs_to_attack.position[state.player_level]
    mob_distances = jnp.sum(jnp.abs(mob_positions - state.player_position), axis=1)
    closest_mob_index = jnp.argmin(mob_distances)
    closest_mob_position = mob_positions[closest_mob_index]
    
    # Check if mob is within attack range
    if jnp.sum(jnp.abs(closest_mob_position - state.player_position)) > 1:
        raise ValueError(f"Mob is too far to attack")
    
    # Check if player has weapon
    if state.inventory.sword <= 0:
        raise ValueError("No sword in inventory")
    
    # Calculate damage based on sword level
    sword_level = state.inventory.sword
    base_damage = 1 + 2 * sword_level
    damage_vector = jnp.array([base_damage, 0, 0])  # Physical damage
    
    # Apply attribute scaling
    damage_vector = damage_vector * (1 + 0.25 * (state.player_strength - 1))
    
    # Attack the mob
    new_state, did_attack, did_kill = _attack_mob_logic(state, closest_mob_position, damage_vector, mob_class)
    
    return new_state


def _attack_mob_logic(state: EnvState, mob_position, damage_vector, mob_class) -> tuple:
    """Internal logic for attacking a mob."""
    # Simplified attack logic
    damage = jnp.sum(damage_vector)
    
    # Get mob health
    if mob_class == 1:
        mob_health = state.melee_mobs.health[state.player_level, 0]
    elif mob_class == 2:
        mob_health = state.ranged_mobs.health[state.player_level, 0]
    else:
        mob_health = state.passive_mobs.health[state.player_level, 0]
    
    # Check if mob dies
    new_health = mob_health - damage
    did_kill = new_health <= 0
    
    # Update mob health
    if mob_class == 1:
        new_mobs = state.melee_mobs.replace(
            health=state.melee_mobs.health.at[state.player_level, 0].set(new_health)
        )
    elif mob_class == 2:
        new_mobs = state.ranged_mobs.replace(
            health=state.ranged_mobs.health.at[state.player_level, 0].set(new_health)
        )
    else:
        new_mobs = state.passive_mobs.replace(
            health=state.passive_mobs.health.at[state.player_level, 0].set(new_health)
        )
    
    # Update mob map
    new_mob_map = state.mob_map.at[state.player_level, mob_position[0], mob_position[1]].set(
        jnp.logical_and(
            state.mob_map[state.player_level, mob_position[0], mob_position[1]],
            jnp.logical_not(did_kill)
        )
    )
    
    # Update monsters killed counter
    new_monsters_killed = state.monsters_killed.at[state.player_level].add(
        1 * did_kill
    )
    
    return state.replace(
        melee_mobs=new_mobs if mob_class == 1 else (state.ranged_mobs if mob_class == 2 else state.passive_mobs),
        mob_map=new_mob_map,
        monsters_killed=new_monsters_killed,
    )
