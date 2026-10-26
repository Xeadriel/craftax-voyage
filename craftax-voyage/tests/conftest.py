import sys
from pathlib import Path

import pytest

# The modules import each other as top-level packages (utils, agents, ...)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture(scope="session")
def base_state():
    import jax
    from craftax.craftax_env import make_craftax_env_from_name

    env = make_craftax_env_from_name("Craftax-Symbolic-v1", auto_reset=True)
    _, state = env.reset(jax.random.PRNGKey(0), env.default_params)
    return state


@pytest.fixture(autouse=True)
def fresh_knowledge():
    from control_primitives.knowledge import knowledge

    knowledge.reset()
    yield
    knowledge.reset()
