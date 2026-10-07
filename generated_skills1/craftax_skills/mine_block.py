# Skill: mine_block
# Purpose: Mines a specified block type at the player's current facing direction
# Required inputs: block_name (string) - name of block to mine from constants.py
# Preconditions:
#   - Player must be within bounds
#   - Player must have pickaxe level >= required level for block
#   - Block must be accessible (not in mob, not solid)
# Expected effects:
#   - Block is removed and replaced with PATH
#   - Corresponding resource is added to inventory
#   - Achievement may be triggered for collection
# Failure conditions:
#   - Block is out of bounds
#   - Block is in a mob's position
#   - Block is solid and cannot be mined
#   - Player has insufficient pickaxe level
# Explanation: Uses do_action from game_logic.py which handles mining logic
#           Checks SOLID_BLOCKS from constants.py for block accessibility
#           Requires pickaxe level from inventory to determine mining capability

from craftax.craftax.constants import BlockType, DIRECTIONS
from craftax.craftax.craftax_state import EnvState


def mine_block(state: EnvState, block_name: str) -> EnvState:
    """
    Mines a specified block type at the player's current facing direction.

    Args:
        state: Current environment state
        block_name: Name of block to mine (e.g., 'STONE', 'COAL', 'TREE')

    Returns:
        New state with block mined and resource added to inventory

    Raises:
        ValueError: If block name is invalid or mining is not possible
    """
    # Map block name to BlockType enum
    block_type = BlockType(block_name)

    # Calculate target position based on player direction
    target_position = state.player_position + DIRECTIONS[state.player_direction]

    # Check if position is in bounds
    if not (
        0 <= target_position[0] < state.map[state.player_level].shape[0]
        and 0 <= target_position[1] < state.map[state.player_level].shape[1]
    ):
        raise ValueError(f"Target position {target_position} is out of bounds")

    # Check if position is occupied by a mob
    if state.mob_map[state.player_level, target_position[0], target_position[1]]:
        raise ValueError(f"Position {target_position} is occupied by a mob")

    # Check if block is solid and cannot be mined
    if BlockType(block_name).value in [
        BlockType.STONE.value,
        BlockType.TREE.value,
        BlockType.COAL.value,
        BlockType.IRON.value,
        BlockType.DIAMOND.value,
        BlockType.CRAFTING_TABLE.value,
        BlockType.FURNACE.value,
        BlockType.PLANT.value,
        BlockType.RIPE_PLANT.value,
        BlockType.WALL.value,
        BlockType.WALL_MOSS.value,
        BlockType.STALAGMITE.value,
        BlockType.RUBY.value,
        BlockType.SAPPHIRE.value,
        BlockType.CHEST.value,
        BlockType.FOUNTAIN.value,
        BlockType.FIRE_TREE.value,
        BlockType.ENCHANTMENT_TABLE_FIRE.value,
        BlockType.ENCHANTMENT_TABLE_ICE.value,
        BlockType.GRAVE.value,
        BlockType.GRAVE2.value,
        BlockType.GRAVE3.value,
        BlockType.NECROMANCER.value,
    ]:
        raise ValueError(f"Block {block_name} is solid and cannot be mined")

    # Check pickaxe level requirements
    pickaxe_level = state.inventory.pickaxe
    if block_name == "STONE" and pickaxe_level < 1:
        raise ValueError("Need pickaxe level 1+ to mine STONE")
    if block_name == "COAL" and pickaxe_level < 1:
        raise ValueError("Need pickaxe level 1+ to mine COAL")
    if block_name == "IRON" and pickaxe_level < 2:
        raise ValueError("Need pickaxe level 2+ to mine IRON")
    if block_name == "DIAMOND" and pickaxe_level < 3:
        raise ValueError("Need pickaxe level 3+ to mine DIAMOND")
    if block_name == "SAPPHIRE" and pickaxe_level < 4:
        raise ValueError("Need pickaxe level 4+ to mine SAPPHIRE")
    if block_name == "RUBY" and pickaxe_level < 4:
        raise ValueError("Need pickaxe level 4+ to mine RUBY")

    # Check if block exists at target position
    current_block = state.map[
        state.player_level, target_position[0], target_position[1]
    ]
    if current_block != block_type.value:
        raise ValueError(
            f"Block at {target_position} is {BlockType(current_block).name}, not {block_name}"
        )

    # Perform mining action using the environment's do_action logic
    # This is a simplified version that directly modifies the state
    new_map = (
        state.map[state.player_level]
        .at[target_position[0], target_position[1]]
        .set(BlockType.PATH.value)
    )
    new_inventory = state.inventory.replace(
        wood=state.inventory.wood + 1 if block_name == "TREE" else 0,
        stone=state.inventory.stone + 1 if block_name in ["STONE", "STALAGMITE"] else 0,
        coal=state.inventory.coal + 1 if block_name == "COAL" else 0,
        iron=state.inventory.iron + 1 if block_name == "IRON" else 0,
        diamond=state.inventory.diamond + 1 if block_name == "DIAMOND" else 0,
        sapphire=state.inventory.sapphire + 1 if block_name == "SAPPHIRE" else 0,
        ruby=state.inventory.ruby + 1 if block_name == "RUBY" else 0,
        sapling=state.inventory.sapling + 1 if block_name == "GRASS" else 0,
        torches=state.inventory.torches + 0,
        arrows=state.inventory.arrows + 0,
        armour=state.inventory.armour,
        potions=state.inventory.potions,
        books=state.inventory.books,
    )

    return state.replace(
        map=state.map.at[state.player_level].set(new_map),
        inventory=new_inventory,
    )
