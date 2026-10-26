# Design: clean roles for curriculum, action and critic agents

## Context / why
The test run `craftax-voyage/testrun.txt` (104 iterations, all agents Qwen3.5-4B) never got past floor 1:
- 4 deaths
- ~1/3 of tasks were survival chores, often badly chosen. Example: "Drink 6 water" at drink 6, health 2, energy 1, right before dying.
- The action agent read "Drink 6 water" / "Mine 3 coal" as "until I have N", added its own goals (descending inside "Open 1 chest") and logged verdicts like "Chest opened successfully".
- The critic was swayed by those log lines and by hallucinated QA context ("passive mobs cannot be killed"). It also passed a do-nothing skill ("already had 6 drinks"), which then entered the skill library and taught the wrong pattern further.
- After a death the curriculum still believed the old progress ("you are on floor 1 with an iron pickaxe").

Goal: each agent does one job well.
- **Curriculum:** the only decision maker. At every turn it picks the best next task given what it has and what it can find, keeps intrinsics safe preemptively, and steadily grows resources and equipment. There is no "preparation phase": it upgrades and plans descents as materials become available.
- **Action agent:** pure executor. It interprets the task literally (amounts are always "N more"), does it safely and efficiently, makes no decisions of its own and never claims success.
- **Critic:** impartial judge. It decides only from the before/after state and what the primitives report actually happened, never from the action agent's own words.

## Non-goals (this round)
- **No mid-task interrupt / survival override.** Decided to wait. Run first, then classify deaths: if "sudden collapse mid-task" deaths remain common, add a narrow "about to die" stop later.
- **No critic → curriculum verdict on the curriculum's choices.** The curriculum gets a factual recap instead.
- **No task parsing in code** (tasks like enchant, search and open chest aren't countable). No "next upgrades" agenda for the curriculum. No templated skills (against the point of the project).

## 1. Shared: situation report (new module, e.g. `craftax-voyage/utils/situation_report.py`)
- A function `render_situation_report(state)` produces the curriculum's state view. The critic uses the same function to describe its before/after states.
- It reads only player-visible information, via `control_primitives/knowledge.py`:
  - `visible_mask` / `is_visible` (in view)
  - `known_blocks` / `known_items` (seen on this floor)
  - `visible_mobs`, `ladder_open`
- Sections (no day/night, no "next upgrades"):
  - **Vitals:** `current/max` for health, food, drink, energy and mana. Maxima come from `craftax.craftax.util.game_logic_utils.get_max_health/food/drink/energy/mana`, because they change with strength, dexterity and intelligence. Food, drink and energy also show "can gain up to (max - current)". Also: sleeping/resting state.
  - **Attributes:** XP, dexterity, strength, intelligence.
  - **Threats in view:** melee and ranged mobs, as name + distance in tiles.
  - **Equipment:** pickaxe/sword tier as names, bow, armour per slot, enchantments, learned spells.
  - **Inventory:** all entries, including zeros (materials, saplings, torches, arrows, books, potions).
  - **In view now:** resource blocks and passive mobs currently visible, with the nearest distance of each kind.
  - **Seen on this floor:** remembered resource blocks (from `known_blocks`) with the nearest distance, plus explicit "not seen" for key ores. Also chests, and the ladder down: seen or not, open or blocked. When blocked, show how many more kills are needed: `MONSTERS_KILLED_TO_CLEAR_LEVEL - state.monsters_killed[level]`. This counts as player knowledge (its own kills; the threshold is in the tutorial).
  - **Stations:** crafting table, furnace and enchantment tables, each "in view (n tiles)" / "seen (n tiles)" / "none seen".
  - **Craftable (hypothetical):** two lists, "with a crafting table" and "with a crafting table + furnace".
    - **Source:** the existing recipe table in `control_primitives/craft.py`. Move it from inside `craft()` to a module-level constant that `craft()` and the report both use.
    - **Verified:** all 12 recipes match `craftax/craftax/game_logic.py` `do_crafting`, including materials, stations, tier rules and stack yields.
    - **Rules per recipe:**
      - the player has all materials
      - tool tier: current `pickaxe`/`sword` < the recipe level
      - armour: some slot < the recipe level
      - arrows/torches: below 99
    - **Grouping:** by the recipe's required stations.

    The real station positions are in the Stations section.
  - **Enchantable (hypothetical):** two lists, "at a fire enchantment table" and "at an ice enchantment table". Each lists which of sword, bow and armour could be enchanted.
    - **Source:** the requirement constants in `control_primitives/enchant.py`: `elements` (element → enchantment value, table block, gem), `enchant_actions` and `mana_cost`. Move them from inside `enchant()` to module level, shared by `enchant()` and the report.
    - **Verified:** they match `craftax/craftax/game_logic.py` `enchant` (9 mana, ruby for fire, sapphire for ice, equipment owned).
    - **Rules per equipment/element:**
      - the player owns the equipment (`sword > 0`, `bow > 0`, any armour slot > 0)
      - mana ≥ the mana cost
      - gem ≥ 1
      - not already enchanted with that element (for armour: not every slot already has it), mirroring the primitive's own early return
    - Enchantment tables can't be placed, so the Stations section showing where tables are matters here.
  - **Floor:** number + name (reuse `CurriculumAgent.FLOOR_NAMES`).
  - **Missing achievements:** the `Achievement` names with `state.achievements[i] == 0`.
- Resources = all minable blocks.
- Builder's call: exact formatting, distance metric.

## 2. Curriculum agent (`agents/curriculum.py`, `prompts/curriculum.txt`)
- **Human message:** replace `textual_state` (the 99-line map dump) with the situation report.
- **Last-turn recap,** from the rollout result:
  - task
  - verdict + critique
  - number of attempts
  - vitals before → after (from the report data)
  - whether the player died
- **Death notice:** "You died during the last task. The world was reset: inventory, equipment and floor progress are gone. Learned skills remain."
- **Progress split:**
  - `completed_tasks` (persistent, what was learned)
  - new `world_progress` (tasks completed in the current world, cleared on death)

  Render both. A task that ended by death is handled like any other failed task: it is added to `failed_tasks`. No special case.
- **QA:** turn off by default (new CLI flag, e.g. `--use_qa`, default off). The tutorial is already in the curriculum's and action agent's system prompts. The 4B QA answers were redundant and introduced hallucinations, and they are cached forever. With QA off, `get_task_context` returns no context. *(Agreed.)*
- **Prompt rewrite:**
  - How to read the report.
  - Each turn: look at vitals vs. their maxima and at threats first, and anticipate. A task that will take a while must not start with a vital that will run out during it.
  - Then pick the most valuable progress step: better equipment, new resources, missing achievements, descending when it's the best move.
  - Amounts in tasks are additions and must fit within "can gain up to".
  - A blocked ladder needs kills first. The curriculum schedules kill tasks itself (using the "N more kills needed" count) before proposing a descent. The action agent never fights to open a ladder.
  - Use the recap to judge whether the last choice was good.
  - Balanced few-shot examples (not survival-heavy).
  - Remove rule 11's guesswork about deaths, since the death notice replaces it.

## 3. Action agent (`agents/action.py`, `prompts/action_template.txt`, `craftax_voyage.py`)
Prompt changes:
- **Role:** executor only. It does the task as written plus its direct prerequisites on the current floor (materials, tools, crafting stations via primitives). It never changes floors, eats, drinks, sleeps or starts fights the task didn't ask for, and never does a different task. If the task can't be done here, it attempts it as written and lets it fail.
- **Fixed sentence in the human message right after `Task:`:** "Amounts in the task are added on top of what you have now (the state above is the starting point)." Generic, so it works for any task.
- **Replace the opening example** with one showing all three correct patterns:
  - `state = step_func(Action.X.value)` (one argument)
  - `state = primitive(state, log_fn, step_func, ...)`
  - an additive count (`target = state.inventory.coal + 3`)
- **Rewrite rule 3** (prerequisite checks): checking that you own the *materials/tools* is fine; never skip or shorten the task itself because you already own some of the target.
- **Rule 15** becomes the general additive-amount rule.
- **Logging:** `log_fn` is for progress notes only. Never state success or failure, and don't start lines with `[` (that prefix is reserved for primitives).
- **Critiques:** the critic's verdict is final. Fix what it reports; never argue the task was already done.
- **Naming:** never name the skill after a program in the list (`sleep`, `drink`, `craft`, `known_blocks`, …).
- **Knowledge helpers:** add one correct usage line each for `known_blocks(state)` (returns an array) and `is_visible(state, row, col)`.
  - **Make sure the helpers are callable at execution time.** `execute_skill` builds its namespace from `craftax_voyage.py`'s globals, which get them via `from control_primitives import *`. Add a check that every knowledge helper named in the prompt (`known_blocks`, `known_items`, `is_visible`, `visible_mask`, `visible_mobs`, `ladder_open`, `UNKNOWN`) is present in that namespace, and fail loudly at startup if one is missing.
  - The it85 `UnboundLocalError` came from the skill assigning to a helper's name inside the function (`known_blocks = known_blocks(state)`), not from a missing import. The code check below covers that.
- **State info:** keep the readable-fields list and the `Inventory` dataclass. Drop the dump of hidden `EnvState` fields, `Mobs`, `EnvParams` and `StaticEnvParams`.

Code check in `ActionAgent.process_ai_message` (AST, API mistakes only, no task interpretation):
- function name collides with a primitive or knowledge function (names from `load_control_primitives_context` + `control_primitives.knowledge`)
- a primitive or knowledge-function name is assigned to inside the skill (shadowing, the cause of the it85 `UnboundLocalError`)
- `step_func(...)` called with ≠ 1 argument
- `BlockType.X` / `ItemType.X` / `MobType.X` / `Action.X` / `Achievement.X` where `X` is not a member

On a parse or validation error, including a missing code block, `generate_skill` re-asks the LLM immediately with the error appended. At most 2 extra calls; these **do not** use up an attempt or game steps. *(My call on the count of 2.)*

## 4. Critic agent (`agents/critic.py`, `prompts/critic.txt`, `craftax_voyage.py`)
- **Inputs:**
  - task
  - situation report before and after
  - a **code-computed diff**:
    - inventory and equipment changes
    - vitals before → after with maxima
    - floor change
    - new achievements
    - changes in counts of station/resource blocks in view, so placements show
  - the **primitive event log**: only lines starting with `[<primitive>]` that are not per-step lines (`Step n/m`). The skill's own `log_fn` lines are excluded. **All** of those lines, no truncation. The action agent also gets the entire execution log, without the current 60-line cut (`MAX_SKILL_LOG_LINES` in `craftax_voyage.py`).
  - the execution error
  - **no QA context**
- **Death:** if the execution error is `EpisodeEnded`, the critic LLM is **not** called. The task fails, and code writes the critique:
  - "The player died"
  - the vitals and visible threats at the last step before the reset
  - the primitive event lines of that attempt: the same filtered lines the critic would normally see, e.g. `[explore_until] Warning: health dropped from 6.0 to 3.0`, `[kill_mob] Start hunting MELEE ...` `CraftaxVoyage.step` keeps the pre-step state so these are available. The rollout **ends immediately** (no further attempts in the new world) and returns `died=True` to the curriculum. The task goes into `failed_tasks` like any other failure.
- **Prompt rules:**
  - Judge only from the diff, states and primitive events.
  - Amounts are additions. For food, drink and energy, the vital being at its maximum after execution counts as success, even if it was already at the maximum before *(user's decision)*. Known risk: do-nothing skills can enter the library this way. Watch for it in the next run. The report's "can gain up to 0" should keep the curriculum from proposing such tasks.
  - A failed descend because the ladder is blocked is just a fail. The critique states the remaining kills and offers no strategy.
  - The critique describes what happened and what is still missing for *this* task. No strategy beyond the task, no "game bug" claims, no advice to discard items.
  - Examples updated for the new input format.

## Left to the builder
- Module and function names, report formatting, the distance metric.
- Resources = all minable blocks (decided).
- How the recap/diff data travels (e.g. extend the dict returned by `rollout()` / `execute_skill()`).
- Exact prompt wording within the rules above.

## Candidates after the next run (not now)
- Narrow "about to die" interrupt (see non-goals).
- Showing the action agent only relevant skills instead of the whole library.

## Verification
- Render the situation report for the saved `ckpt/env/env_state.pbz2` and eyeball it against the textual state.
- Feed `process_ai_message` a skill named `sleep`, one calling `step_func(state, 5)` and one using `BlockType.MELEE`. Each must return an error.
- Short run (`python craftax_voyage.py --max_iterations 60`), after you've archived the old checkpoint yourself. Compare with this log:
  - success ratio
  - number of deaths and their starting vitals
  - API errors (`TypeError|AttributeError|UnboundLocalError`)
  - repeated survival tasks
  - deepest floor
  - unique achievements
  - action-agent log lines claiming success: should be 0
