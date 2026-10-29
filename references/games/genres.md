# Genre playbooks

*Last updated: 2026-10-13 | Version-sensitive: none significant (design patterns and formulas) | Re-check current docs before pinning versions, prices, or API names.*

Each playbook gives: core loop, systems, formulas, and pitfalls. Combine with `games/core.md` and the engine file for implementation. Balance numbers with a script (`scripts/economy_sim.py` for economies).

## Contents
1. Idle / incremental
2. Tycoon / management simulator
3. Shooter
4. Survival / crafting
5. RPG
6. Platformer
7. Roguelike
8. Tower defense
9. Puzzle
10. Racing and physics toys
11. Choosing scope

## 1. Idle / incremental

**Loop:** earn → buy generator → earn faster → unlock tier → prestige → repeat.

Formulas:
- Cost of the nth unit: `cost(n) = base * growth^n`, growth 1.07-1.15.
- Bulk buy k units from n: `base * growth^n * (growth^k - 1) / (growth - 1)`.
- Max affordable k: `floor(log(money*(growth-1)/(base*growth^n) + 1) / log(growth))`.
- Income: `units * baseIncome * multipliers`. Milestone multipliers (x2 at 25/50/100 owned) keep long-term upgrades meaningful.
- Offline: `earned = incomePerSec * min(elapsed, capSeconds) * offlineRate` (0.5-1.0); show a welcome-back screen.
- Prestige: `currency = floor((lifetimeEarnings / threshold)^0.5)`; each point gives +1-10% permanent multiplier; first prestige at 30-60 minutes.
- Big numbers: format K/M/B/T then scientific (`1.23e45`); use a big-number library beyond 1e308.

Design: every purchase must visibly change the screen (new sprite, counter, sound). Pacing: something to buy every 10-30 s early, every few minutes later. Add automation upgrades (auto-buyers) around the mid game. Test the curve with the simulator and adjust growth until milestones land on target times.

## 2. Tycoon / management simulator

**Loop:** earn → expand/upgrade → automate → optimize → new tier.

Systems: resources and converters (input → output per second), workers/staff with stats, customers or demand model (`demand = base * satisfaction * marketing`), prices with elasticity (`sales = demand * (1 - price/maxPrice)`), upkeep costs, build grid with placement rules, unlock tree, events (random opportunities, crises), reports (income/expense graph).

Feel: clear feedback (floating "+$" numbers), satisfying visual growth, tooltips showing ROI ("pays back in 2m10s"), undo for placement. Pitfalls: one dominant strategy (test by simulating naive vs optimal), snowballing with no sink (add upkeep/scaling costs), opaque numbers (show breakdowns).

## 3. Shooter

**Loop:** engage → shoot → survive → progress/loot.

Weapon data table: damage, fire rate (RPM → interval `60/RPM`), magazine, reload time, spread (base + bloom per shot, recovery), recoil pattern, range falloff (`dmg *= clamp(1 - (d-min)/(max-min), 0.4, 1)`), headshot multiplier (1.5-2.5).
- Time-to-kill = `ceil(hp/dmg) - 1) * interval`; target TTK 0.3-1.0 s for arena shooters, 1.5-3 s for tactical.
- Hitscan (instant ray) vs projectile (speed, gravity, drop, lead the target).
- Enemy AI: state machine (patrol, alert, chase, attack, take cover, retreat); reaction delay 200-400 ms; aim error decreasing with skill; attack tokens (max 2-3 attackers at once).
- Feedback: muzzle flash, tracer, impact particles, hit marker + sound, damage numbers, camera kick, hit-stop on kills.
- Waves: budget system (`waveBudget = 10 + wave*6`, spend on enemy costs), boss every N waves, breathing room between waves.
- Multiplayer: server-authoritative hits, client prediction for movement, lag compensation (rewind hitboxes); flag if out of scope.
Pitfalls: bullet sponges, unreadable enemies, no audio cues, aim assist missing on controller/touch.

## 4. Survival / crafting

**Loop:** gather → craft → build/defend → explore farther.

Systems:
- Needs: hunger/thirst/energy/temperature decay at fixed rates (e.g. 100 → 0 in 20-30 min); penalties below thresholds, damage at zero.
- Crafting as data: `{id, inputs:[{item,qty}], output, station, time}`; recipes discovered or unlocked by tech.
- Inventory: slots + stack limits, or weight; hotbar; quick-stack.
- World: resource nodes with respawn timers and tool tiers (wood → stone → iron), day/night changing risk (spawn rate, visibility), weather, biomes.
- Building: grid or free placement with snapping, structural rules, storage containers.
- Threats: predators/enemies scaling with time or player power, raids at night.
- Save: world delta (placed structures, node states, container contents), not just the player.
Pitfalls: grind walls (add multiple sources of each resource), tedious needs (make them tuning pressure, not chores), lost progress (autosave).

## 5. RPG

Stats: HP, attack, defense, speed, crit; derived: `dmg = attack * skillMult * (100/(100+defense))`. XP curve: `xpToNext = 50 * level^1.6`. Stat growth per level plus gear for spikes. Combat: turn-based (speed order, action menu, status effects) or real-time (cooldowns, stamina). Skills as data (cost, cooldown, effect list). Loot tables with weighted rarity (60/25/10/4/1). Quests as state machines (`locked → active → complete`) with objectives and rewards; dialogue trees as data. Inventory + equipment slots. Pitfalls: linear power curve making early gear irrelevant, unskippable long dialogue, too many stats.

## 6. Platformer

Feel first: acceleration/deceleration, variable jump height, coyote time, jump buffer, wall slide/jump, dash with cooldown. Level design: teach one mechanic in a safe space, test it, twist it, combine it. Checkpoints every 20-40 s of play. Hazards telegraphed. Camera: look-ahead in the movement direction, vertical dead-zone. Collectibles that reward exploration. Pitfalls: floaty or sticky controls (tune gravity ~2x real), invisible hazards, cheap off-screen deaths.

## 7. Roguelike

Loop: run → choices → death → meta-progression. Systems: seeded procedural levels (rooms/BSP/cave, see core), item synergy pool, run-based upgrades (pick 1 of 3), permanent unlocks with currency, difficulty scaling per floor, boss rooms, shops and events. Guarantee winnable seeds (validate connectivity, ensure a healing source). Pitfalls: RNG that ruins runs early (bias first floors), meta-progression that trivializes challenge, too many near-identical items.

## 8. Tower defense

Loop: place → survive wave → earn → upgrade. Systems: path (fixed or maze), tower stats (range, damage, rate, targeting mode: first/last/strongest), upgrade tiers with branching, enemy types (fast, tanky, flying, healer, boss), wave table as data (`{type,count,interval,delay}`), sell refund 60-70%, economy per kill plus interest. Balance: enemy HP grows ~1.1-1.2x per wave, rewards grow slower so choices matter. Pitfalls: one tower that solves everything, invisible range, no wave preview.

## 9. Puzzle

Define rules on paper, then implement as pure functions (`state → nextState`) so undo, hints, and solvers are easy. Level generation: work backwards from a solved state or use a solver to verify solvability and measure difficulty. Introduce one rule at a time; add undo/restart; give clear win/lose feedback; keep sessions short. Match-3: cascade resolution loop (find matches → clear → gravity → refill → repeat), guarantee at least one valid move. Sokoban/grid: BFS to verify solvable. Pitfalls: unsolvable levels, ambiguous rules, no feedback on why a move failed.

## 10. Racing and physics toys

Arcade car: velocity along forward vector, lateral grip factor (`lateral *= 0.9`), steering scaled by speed, drift by reducing grip, drafting bonus. Track: spline with checkpoints for lap validation; rubber-band AI lightly (never obviously). Physics toys: sandbox with spawnable objects, tunable gravity/friction, satisfying collision sound; use a physics library (Box2D/Matter/Rapier) rather than hand-rolling.

## 11. Choosing scope

Ship the smallest version of the loop first (one level, one enemy, one upgrade). Write the cut list up front. Prototype the fun in a day; if the core verb is not fun, no content will save it. Add content only after the loop feels good and the numbers are simulated.

## 12. Related

Shooters and any online play: `games/multiplayer.md` (authoritative server, prediction, lag compensation, anti-cheat). Shipping: `games/production.md`. Adaptive AI opponents and automated balancing agents: `ai/rl.md`.
