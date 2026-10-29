# Games core: architecture, math, AI, procedural generation

*Last updated: 2026-10-13 | Version-sensitive: none significant (engine-agnostic math and patterns) | Re-check current docs before pinning versions, prices, or API names.*

Engine-agnostic. Snippets are JavaScript for clarity; the ideas port directly to C# and C++. Starter: `scripts/scaffold.py canvas-game <dir>`. Balance numbers with `scripts/economy_sim.py`.

## Contents
1. Pick the platform
2. Game loop and time
3. Architecture patterns
4. Math cheatsheet
5. Collision
6. Pathfinding and AI
7. Procedural generation
8. Save systems
9. Balancing method
10. Game design documents
11. Verification

## 1. Pick the platform

| Goal | Default |
|---|---|
| Playable by link, fastest | Browser: Canvas 2D / Three.js / Phaser |
| Android app without native code | Browser game + Capacitor (see `browser-android.md`) |
| Serious 2D/3D, mobile + PC | Unity (C#) or Godot |
| High-fidelity 3D | Unreal Engine |
| 3D assets, animation | Blender (`bpy`) |

## 2. Game loop and time

```js
const STEP = 1/60; let acc = 0, last = performance.now();
function frame(now){ acc += Math.min(0.05, (now-last)/1000); last = now;   // clamp avoids spiral of death
  while(acc >= STEP){ update(STEP); acc -= STEP; }                         // fixed step: stable physics
  render(acc/STEP); requestAnimationFrame(frame); }                        // alpha for interpolation
```

Rules: gameplay uses `dt`, never frame counts; fixed step for physics/simulation; variable for visuals; pause by stopping `update`, not `render`.

## 3. Architecture patterns

**State machine** (game flow, enemy AI, player):
```js
const states = { idle:{ enter(e){}, update(e,dt){ if(e.seesPlayer) return 'chase'; } },
                 chase:{ update(e,dt){ e.moveToward(e.target,dt); if(e.inRange) return 'attack'; } },
                 attack:{ enter(e){ e.cooldown = 0.8; }, update(e,dt){ if((e.cooldown-=dt)<=0) return 'chase'; } } };
function tick(e,dt){ const next = states[e.state].update?.(e,dt); if(next && next!==e.state){ e.state=next; states[next].enter?.(e); } }
```

**Object pool**: preallocate bullets/particles, `acquire()` returns an inactive one, `release()` flags it inactive; no allocation in the hot loop.

**Event bus**: `bus.on('enemyDied', fn)` / `bus.emit('enemyDied', e)` decouples score, audio, VFX, and achievements.

**Entity-Component (light)**: entities are IDs, components are plain data (`pos`, `vel`, `sprite`, `health`), systems iterate entities that have the needed components. Use when many object types share behavior.

**Data-driven**: items, enemies, waves, recipes, levels in JSON/ScriptableObjects/DataTables. Designers change numbers without touching code.

**Input abstraction**: map actions (`jump`, `fire`, `moveX`) to keyboard, gamepad, and touch in one layer.

## 4. Math cheatsheet

```js
lerp = (a,b,t) => a+(b-a)*t;                  clamp = (v,lo,hi) => Math.min(hi,Math.max(lo,v));
smoothDamp: x += (target-x) * (1 - Math.exp(-k*dt));   // frame-rate independent smoothing
dist = Math.hypot(bx-ax, by-ay);              angle = Math.atan2(by-ay, bx-ax);
dir = {x:Math.cos(a), y:Math.sin(a)};          normalize: len=hypot(x,y)||1; x/=len; y/=len;
// Easing
easeOutCubic = t => 1-(1-t)**3;   easeInOut = t => t<.5 ? 4*t**3 : 1-(-2*t+2)**3/2;   easeOutBack = t => 1+2.7*(t-1)**3+1.7*(t-1)**2;
// Aim with projectile speed (lead the target)
// solve |target + v*t - shooter| = speed*t for smallest positive t (quadratic)
// Isometric: screenX=(x-y)*tw/2; screenY=(x+y)*th/2   inverse: x=(sx/(tw/2)+sy/(th/2))/2 ; y=(sy/(th/2)-sx/(tw/2))/2
// Weighted random: pick r=rand()*sum(weights), walk until cumulative >= r
// Damage curve: dmg = base * (1 + level*0.15);  defense: dmg * 100/(100+armor)
```

## 5. Collision

- Rect vs rect (AABB): `a.x<b.x+b.w && a.x+a.w>b.x && a.y<b.y+b.h && a.y+a.h>b.y`.
- Circle vs circle: `hypot(dx,dy) < r1+r2`.
- Tile maps: convert position to tile index, test neighbors; resolve X then Y separately.
- Fast objects: swept test or raycast to prevent tunneling.
- Many objects: spatial hash (grid buckets keyed by `floor(x/cell)`) before pairwise checks.
- Platformer feel: coyote time (~0.1 s), jump buffer (~0.1 s), variable jump height (cut velocity on release).

## 6. Pathfinding and AI

- A* on a grid: open set (priority queue by `f=g+h`), heuristic Manhattan (4-dir) or Octile (8-dir), reconstruct via parent links. Cache paths; recompute on a timer, not every frame.
- Steering: seek, flee, arrive (slow near target), separation (avoid crowding), wander. Blend with weights.
- Perception: vision cone (angle + distance + line-of-sight ray), hearing radius, memory of last-seen position.
- Fairness: reaction delay (150-400 ms), aim error that shrinks with difficulty, limited simultaneous attackers (token system).
- Behavior trees or utility AI when state machines get tangled.

## 7. Procedural generation

- **Seeded RNG** always (mulberry32/LCG) so bugs and levels are reproducible.
- **Noise terrain**: value/Perlin/simplex, sum octaves (`amp*=0.5, freq*=2`), threshold into water/sand/grass/rock.
- **Dungeon rooms**: place random rooms with rejection, connect centers with L-shaped corridors (minimum spanning tree), add doors.
- **Cave**: fill 45% random, run 4-5 cellular-automata passes (wall if >=5 wall neighbors).
- **BSP**: recursively split the map, put a room in each leaf, connect siblings.
- **Wave Function Collapse** (advanced): tiles with adjacency rules, collapse lowest-entropy cell, propagate constraints.
- Validate output: ensure spawn and exit are connected (flood fill) before accepting a level.

## 8. Save systems

```js
const SAVE_VERSION = 3;
const migrate = { 1: s => ({...s, gems: 0, v: 2}), 2: s => ({...s, settings: {sfx: 1}, v: 3}) };
function load(raw){ let s = JSON.parse(raw); while (s.v < SAVE_VERSION) s = migrate[s.v](s); return s; }
```

Version every save, migrate forward, validate ranges on load, autosave at safe points, keep a backup slot, and separate settings from progress. For online games the server owns the truth.

## 9. Balancing method

1. Write the numbers in data tables.
2. Simulate in a script (`economy_sim.py` for idle/tycoon; damage-per-second and time-to-kill tables for combat).
3. Compare target pacing to simulated pacing (first upgrade in 30 s, first prestige in 30-60 min, boss killable in N attempts).
4. Change one variable at a time; re-run.
5. Playtest with someone else; watch, do not explain.

## 10. Game design documents

One-page GDD: pitch, core loop (verb → reward → upgrade), player fantasy, controls, progression, systems list, art/audio direction, scope for v1 (cut list), risks. See `extra/planning.md` for the template.

## 11. Verification

Run `scripts/verify_web.py` on the game (see `extra/verify.md`): errors, blank screen, scenario assertions, a viewed screenshot; use `--skip-draw` plus an in-page simulation for balance (keep tuning numbers in one `TUNE` object). Simulate logic headlessly; run at low frame rate and after a long pause to test time clamping; save → reload → compare state; test restart 5 times for leaks; check controls on the target device; confirm the game is winnable and losable.

## 12. Related

Multiplayer and netcode: `games/multiplayer.md`. Production, QA, telemetry, release: `games/production.md`. Reinforcement-learning bots and playtest agents: `ai/rl.md`. Engine-specific work: `games/unity.md`, `games/unreal.md`, `games/browser-android.md`.
