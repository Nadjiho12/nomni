---
name: games
description: "Design and build games: browser games, Android APK, Unity, Unreal, Blender, pixel art, 2D/2.5D/3D, VFX, genre design (idle, tycoon, shooter, survival, RPG, roguelike), multiplayer netcode, balancing, and game production. Use for any game idea, mechanic, engine script, or game launch."
---

# N-Omni: games

Apply the shared N-Omni core first: read `${CLAUDE_PLUGIN_ROOT}/SKILL.md` for the mode contract (Quick / Standard / Deep), the senior-mode rules, and the safety boundary. Then use this domain's references.

## Domain references

| Task | Reference |
|---|---|
| Any game: game loop (fixed timestep), vector math, collision, A* pathfinding, enemy AI, procedural generation, save systems with versioning, balancing | `references/games/core.md` |
| Browser games (Canvas, Three.js, Phaser), touch controls, HTML5 game to Android APK (Capacitor, TWA, Godot, Unity) | `references/games/browser-android.md` |
| Unity C# scripts: CharacterController, Rigidbody, Input System, ScriptableObject inventory, prefabs, UI, build | `references/games/unity.md` |
| Unreal Engine: Blueprints and C++, Enhanced Input, gameplay framework, UMG, replication, Niagara | `references/games/unreal.md` |
| Blender bpy scripting, pixel art and sprite sheets, particle effects (explosion VFX), shaders, 2.5D and isometric art | `references/games/blender-art-vfx.md` |
| Genre design and balance: idle/incremental economy, tycoon, simulator, shooter, survival crafting system, RPG, platformer, roguelike dungeon, tower defense, puzzle | `references/games/genres.md` |
| Multiplayer netcode: authoritative server, client prediction, interpolation, lag compensation, anti-cheat, matchmaking | `references/games/multiplayer.md` |
| Game production: pipeline, performance budgets, QA/playtesting, telemetry, Steam/itch/mobile release, live ops | `references/games/production.md` |

Load only the sections you need (each reference has a Contents list). Reference paths are relative to the plugin root: `references/...`, scripts are `${CLAUDE_PLUGIN_ROOT}/scripts/...`.
