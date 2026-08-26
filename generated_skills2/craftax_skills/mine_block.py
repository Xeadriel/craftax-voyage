# Skill: mine_block
# Purpose: Mines a specified block type at the player's current position
# Required inputs: block_type (BlockType enum value), max_steps (int)
# Preconditions: Player must be at a valid position, have a pickaxe of appropriate level
# Expected effects: Block is removed, corresponding resource is added to inventory
# Failure conditions: Block is not mineable, player has no pickaxe, out of bounds
# Explanation: Uses state.map for block lookup, state.inventory for resource tracking,
#             state.player_position for location, and Action.DO for mining interaction

import jax
from craftax.craftax.constants import BlockType, Action
from craftax.craftax.craftax_state import EnvState
from craftax.craftax.util.game_logic_utils import is_in_solid_block, in_bounds


def mine_block(state: EnvState, block_type: BlockType, max_steps: int = 100) -> bool:
    """
    Mines a specified block type at the player's current position.

    Returns True if mining succeeded, False otherwise.
    """
    # Check if we have the required pickaxe level
    pickaxe_level = state.inventory.pickaxe

    # Determine minimum pickaxe level needed for this block
    pickaxe_requirements = {
        BlockType.STONE: 1,
        BlockType.COAL: 1,
        BlockType.IRON: 2,
        BlockType.DIAMOND: 3,
        BlockType.SAPPHIRE: 4,
        BlockType.RUBY: 4,
        BlockType.TREE: 0,
        BlockType.FURNACE: 0,
        BlockType.CRAFTING_TABLE: 0,
        BlockType.STALAGMITE: 1,
    }

    required_level = pickaxe_requirements.get(block_type, 0)

    if pickaxe_level < required_level:
        return False

    # Check if block is in bounds
    if not in_bounds(state, state.player_position):
        return False

    # Check if block is solid (cannot mine solid blocks)
    if is_in_solid_block(state, state.player_position):
        return False

    # Check if block is at player position
    current_block = state.map[
        state.player_level, state.player_position[0], state.player_position[1]
    ]

    if current_block != block_type.value:
        return False

    # Mine the block by performing the DO action
    # This will remove the block and add resources to inventory
    # We need to check if the action was successful by observing the state change

    # For multi-step mining, we'll try to mine until we get the resource
    # or hit a failure condition
    for step in range(max_steps):
        # Check if we already have the resource (success condition)
        if block_type.value in [
            BlockType.STONE.value,
            BlockType.COAL.value,
            BlockType.IRON.value,
            BlockType.DIAMOND.value,
            BlockType.SAPPHIRE.value,
            BlockType.RUBY.value,
        ]:
            if getattr(state.inventory, f"{block_type.name.lower()}") > 0:
                return True

        # Check if we're stuck (no progress)
        if step > 0:
            # Check if block is still there
            current_block = state.map[
                state.player_level, state.player_position[0], state.player_position[1]
            ]
            if current_block == block_type.value:
                # Block still exists, but we've tried max_steps
                return False

        # Perform mining action
        # Note: In Craftax, mining is done by pressing SPACE (Action.DO)
        # The environment handles the actual mining logic
        action = Action.DO.value
        key = jax.random.PRNGKey(0)
        _, new_state, reward, done, info = state.step(
            key, state, action, state.default_params
        )
        state = new_state

    return False
