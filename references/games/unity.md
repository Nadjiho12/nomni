# Unity (C#)

*Last updated: 2026-09-30 | Version-sensitive: Unity version, Input System and physics API names (for example Rigidbody.linearVelocity), package versions | Re-check current docs before pinning versions, prices, or API names.*

State the assumed Unity version and render pipeline (Built-in / URP / HDRP) at the top of every Unity answer; APIs and menus differ. Code here targets Unity 2022 LTS / Unity 6 with the Input System package. Unity cannot be run here: deliver scripts plus exact editor steps and mark them **open gap**.

## Contents
1. Project setup
2. Core concepts
3. Player controllers (2D, 3D)
4. Input System
5. ScriptableObject data
6. Object pooling
7. Events and decoupling
8. UI (TextMeshPro, Canvas)
9. Save/load
10. Audio, particles, animation
11. Camera (Cinemachine)
12. Build and optimize
13. Common errors
14. Verification

## 1. Project setup

Templates: 2D (URP), 3D (URP). Install packages via Window > Package Manager: Input System, Cinemachine, TextMeshPro, 2D Sprite/Tilemap (for 2D). Folder layout: `Assets/{Scripts, Prefabs, Scenes, Art, Audio, Data}`. One assembly per big module only if compile times hurt. Use Git with the Unity `.gitignore` and Force Text serialization (default).

## 2. Core concepts

GameObject = container; Component = behavior/data; Prefab = reusable GameObject; Scene = level. Lifecycle: `Awake` (self setup) → `OnEnable` → `Start` (references to others) → `Update` (input, non-physics) → `FixedUpdate` (physics) → `LateUpdate` (camera follow) → `OnDisable`/`OnDestroy` (unsubscribe). Cache `GetComponent` in `Awake`; never call `Find*` per frame.

## 3. Player controllers

**2D platformer** (`Rigidbody2D` Dynamic, `CapsuleCollider2D`, ground check child):
```csharp
using UnityEngine; using UnityEngine.InputSystem;
[RequireComponent(typeof(Rigidbody2D))]
public class PlayerController2D : MonoBehaviour {
    [SerializeField] float speed = 7f, jumpForce = 12f, coyote = 0.1f, buffer = 0.1f;
    [SerializeField] Transform groundCheck; [SerializeField] float groundRadius = 0.15f; [SerializeField] LayerMask groundMask;
    Rigidbody2D rb; float move, coyoteTimer, bufferTimer; bool grounded;
    void Awake() => rb = GetComponent<Rigidbody2D>();
    public void OnMove(InputAction.CallbackContext c) => move = c.ReadValue<Vector2>().x;
    public void OnJump(InputAction.CallbackContext c) { if (c.started) bufferTimer = buffer; if (c.canceled && rb.linearVelocity.y > 0) rb.linearVelocity = new Vector2(rb.linearVelocity.x, rb.linearVelocity.y * 0.5f); }
    void Update() { grounded = Physics2D.OverlapCircle(groundCheck.position, groundRadius, groundMask);
        coyoteTimer = grounded ? coyote : coyoteTimer - Time.deltaTime; bufferTimer -= Time.deltaTime;
        if (bufferTimer > 0 && coyoteTimer > 0) { rb.linearVelocity = new Vector2(rb.linearVelocity.x, jumpForce); bufferTimer = coyoteTimer = 0; } }
    void FixedUpdate() => rb.linearVelocity = new Vector2(move * speed, rb.linearVelocity.y);
}
```
(On Unity 2022 and earlier use `rb.velocity`; `linearVelocity` is Unity 6.) Editor steps: add `PlayerInput` component (Behavior: Invoke Unity Events), map Move/Jump to the two methods; create a Ground layer and set `groundMask`.

**3D third-person / first-person** with `CharacterController`:
```csharp
[RequireComponent(typeof(CharacterController))]
public class PlayerController3D : MonoBehaviour {
    [SerializeField] float speed = 6f, gravity = -20f, jump = 1.2f; CharacterController cc; Vector3 vel; Vector2 move; bool jumpPressed;
    void Awake() => cc = GetComponent<CharacterController>();
    public void OnMove(InputAction.CallbackContext c) => move = c.ReadValue<Vector2>();
    public void OnJump(InputAction.CallbackContext c) { if (c.started) jumpPressed = true; }
    void Update() {
        if (cc.isGrounded && vel.y < 0) vel.y = -2f;
        var dir = transform.right * move.x + transform.forward * move.y; cc.Move(dir * speed * Time.deltaTime);
        if (jumpPressed && cc.isGrounded) vel.y = Mathf.Sqrt(jump * -2f * gravity); jumpPressed = false;
        vel.y += gravity * Time.deltaTime; cc.Move(vel * Time.deltaTime);
    }
}
```
Camera-relative movement: rotate the input by `Camera.main.transform.eulerAngles.y`.

## 4. Input System

Create `Assets > Create > Input Actions`, define an action map `Player` with Move (Vector2), Jump, Fire, Look; bind keyboard, gamepad, and touch. Generate a C# class or use `PlayerInput`. Read continuous input with `action.ReadValue<T>()`, discrete with `started/performed/canceled` callbacks. Rebinding: `InputActionRebindingExtensions.PerformInteractiveRebinding`.

## 5. ScriptableObject data

```csharp
[CreateAssetMenu(menuName = "Game/Item")]
public class ItemData : ScriptableObject { public string id; public string displayName; public Sprite icon; public int maxStack = 99; public int value; }
[CreateAssetMenu(menuName = "Game/Enemy")]
public class EnemyData : ScriptableObject { public float hp = 30, speed = 2, damage = 5; public GameObject prefab; public ItemData drop; }
```
Right-click in Project > Create > Game > Item to author data without code changes. Never mutate ScriptableObject fields at runtime for per-instance state (it persists in the editor); copy to runtime structs.

## 6. Object pooling

```csharp
using UnityEngine.Pool;
public class BulletPool : MonoBehaviour {
    [SerializeField] Bullet prefab; ObjectPool<Bullet> pool;
    void Awake() => pool = new ObjectPool<Bullet>(() => Instantiate(prefab), b => b.gameObject.SetActive(true), b => b.gameObject.SetActive(false), b => Destroy(b.gameObject), false, 20, 200);
    public Bullet Get(Vector3 pos, Quaternion rot) { var b = pool.Get(); b.transform.SetPositionAndRotation(pos, rot); b.Init(pool); return b; }
}
public class Bullet : MonoBehaviour { ObjectPool<Bullet> pool; public void Init(ObjectPool<Bullet> p) { pool = p; Invoke(nameof(Release), 3f); } void Release() { if (gameObject.activeSelf) pool.Release(this); } }
```

## 7. Events and decoupling

```csharp
public static class GameEvents { public static event System.Action<int> ScoreChanged; public static void RaiseScore(int s) => ScoreChanged?.Invoke(s); }
// subscribe in OnEnable, unsubscribe in OnDisable to avoid leaks and null refs
```
Or `UnityEvent` in the inspector for designer wiring, or a `ScriptableObject` event channel.

## 8. UI

Canvas (Screen Space - Overlay), Canvas Scaler = Scale With Screen Size (1920x1080, match 0.5). Use TextMeshPro (`TMP_Text`). Anchors and layout groups instead of pixel positions. Buttons: `button.onClick.AddListener(...)`. Health bar: `Image` with Fill Amount, `image.fillAmount = hp / maxHp`. Pause: `Time.timeScale = 0` (use `Time.unscaledDeltaTime` for UI animation).

## 9. Save/load

```csharp
[System.Serializable] public class SaveData { public int version = 1; public int coins; public Vector3 pos; public List<string> unlocked = new(); }
public static class SaveSystem {
    static string Path => System.IO.Path.Combine(Application.persistentDataPath, "save.json");
    public static void Save(SaveData d) { var tmp = Path + ".tmp"; System.IO.File.WriteAllText(tmp, JsonUtility.ToJson(d)); System.IO.File.Copy(tmp, Path, true); System.IO.File.Delete(tmp); }
    public static SaveData Load() => System.IO.File.Exists(Path) ? JsonUtility.FromJson<SaveData>(System.IO.File.ReadAllText(Path)) : new SaveData();
}
```
`JsonUtility` does not serialize dictionaries; use lists of pairs or Newtonsoft JSON.

## 10. Audio, particles, animation

- Audio: `AudioSource.PlayOneShot(clip)`; group in an AudioMixer (Music/SFX) with exposed volume parameters (dB = `Mathf.Log10(v) * 20`).
- Particles: Particle System module settings are in `games/blender-art-vfx.md` (table). Trigger with `ps.Play()`, or spawn a pooled prefab.
- Animation: Animator Controller with parameters (`Speed` float, `Jump` trigger); drive with `animator.SetFloat("Speed", Mathf.Abs(move))`; Animation Events for footstep/hit frames.
- Tweening: DOTween or manual `Mathf.SmoothDamp` / `AnimationCurve`.

## 11. Camera

Cinemachine: Virtual Camera with Follow = player, damping 0.5-1, Confiner 2D for level bounds, Impulse Source for screen shake (`GetComponent<CinemachineImpulseSource>().GenerateImpulse()`).

## 12. Build and optimize

Build Settings: add scenes, choose platform, Player Settings (company, product, package name, icon, orientation, min API level for Android, IL2CPP + ARM64 for Play Store). Optimize: batch materials, sprite atlases, compress textures, bake lighting, avoid `Update` for things events can drive, use the Profiler (Window > Analysis) before guessing.

## 13. Common errors

| Error | Cause | Fix |
|---|---|---|
| NullReferenceException | Unassigned inspector field, or `GetComponent` on the wrong object | Assign in inspector or cache in `Awake`; add `[RequireComponent]` |
| Jitter in follow camera | Camera moved in `Update` while target uses physics | Move in `LateUpdate` or use Cinemachine |
| Player falls through floor | Missing collider, fast speed, moved via `transform` | Add collider, `Collision Detection: Continuous`, move via Rigidbody |
| Input does nothing | Wrong Active Input Handling | Player Settings > Active Input Handling = Input System Package (or Both) |
| Events fire after destroy | Unsubscribe missing | Unsubscribe in `OnDisable` |
| Pink materials | Shader mismatch with pipeline | Upgrade materials (Edit > Rendering > Materials > Convert) |

## 14. Verification

Compile-check the scripts by reading types and namespaces; list the exact inspector assignments; give a 5-item playtest checklist (moves, jumps, collides, UI updates, restart works). Mark the result **open gap** unless the user confirmed it in the editor.
