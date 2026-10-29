# Unreal Engine (Blueprints + C++)

*Last updated: 2026-09-30 | Version-sensitive: Unreal Engine version; Enhanced Input and gameplay API details | Re-check current docs before pinning versions, prices, or API names.*

State the assumed version (UE 5.x) at the top of every answer. Unreal cannot be run here: describe Blueprint logic node by node, give C++ that follows engine conventions, and mark results **open gap**.

## Contents
1. Decision guide: Blueprint vs C++
2. Gameplay framework
3. Project setup
4. C++ character with Enhanced Input
5. Blueprint recipes (node walkthroughs)
6. Weapons and damage
7. UI (UMG)
8. Data-driven design
9. AI (Behavior Tree)
10. Multiplayer basics
11. VFX (Niagara) and materials
12. Packaging
13. Common errors
14. Verification

## 1. Blueprint vs C++

| Use Blueprint for | Use C++ for |
|---|---|
| Prototyping, UI, level scripting, designer tuning, asset wiring | Performance-critical loops, base classes, systems shared across many Blueprints, networking-heavy code |

Pattern: C++ base class exposing `UPROPERTY(EditAnywhere/BlueprintReadWrite)` and `UFUNCTION(BlueprintCallable/BlueprintImplementableEvent)`, Blueprint subclass for content.

## 2. Gameplay framework

GameMode (rules, which classes spawn; server only) · GameState (replicated match state) · PlayerController (input, UI, possession) · Pawn/Character (the body) · PlayerState (per-player replicated data: score, name) · HUD/UMG (display) · GameInstance (persists across levels). Put logic where its lifetime and authority fit: score in PlayerState, input in Controller, movement in Character.

## 3. Project setup

Create from the Third Person or blank C++ template. Enable plugins: Enhanced Input (default in 5.1+), Niagara, Gameplay Abilities if needed. Source in `Source/<Project>/`; add classes via Tools > New C++ Class; build with Live Coding (Ctrl+Alt+F11) or close the editor and build from the IDE for header changes. Use Git or Perforce with the standard `.gitignore` (ignore `Binaries`, `Intermediate`, `Saved`, `DerivedDataCache`).

## 4. C++ character with Enhanced Input

```cpp
// MyCharacter.h
#pragma once
#include "GameFramework/Character.h"
#include "InputActionValue.h"
#include "MyCharacter.generated.h"
class UInputMappingContext; class UInputAction; class USpringArmComponent; class UCameraComponent;

UCLASS()
class AMyCharacter : public ACharacter {
    GENERATED_BODY()
public:
    AMyCharacter();
protected:
    virtual void BeginPlay() override;
    virtual void SetupPlayerInputComponent(UInputComponent* Input) override;
    void Move(const FInputActionValue& V); void Look(const FInputActionValue& V);
    UPROPERTY(EditAnywhere, Category="Input") UInputMappingContext* DefaultContext;
    UPROPERTY(EditAnywhere, Category="Input") UInputAction* MoveAction;
    UPROPERTY(EditAnywhere, Category="Input") UInputAction* LookAction;
    UPROPERTY(EditAnywhere, Category="Input") UInputAction* JumpAction;
    UPROPERTY(VisibleAnywhere) USpringArmComponent* Boom; UPROPERTY(VisibleAnywhere) UCameraComponent* Cam;
};
```
```cpp
// MyCharacter.cpp
#include "MyCharacter.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "GameFramework/SpringArmComponent.h"
#include "Camera/CameraComponent.h"
#include "GameFramework/CharacterMovementComponent.h"

AMyCharacter::AMyCharacter() {
    Boom = CreateDefaultSubobject<USpringArmComponent>("Boom"); Boom->SetupAttachment(RootComponent); Boom->TargetArmLength = 400.f; Boom->bUsePawnControlRotation = true;
    Cam = CreateDefaultSubobject<UCameraComponent>("Cam"); Cam->SetupAttachment(Boom);
    bUseControllerRotationYaw = false; GetCharacterMovement()->bOrientRotationToMovement = true;
}
void AMyCharacter::BeginPlay() {
    Super::BeginPlay();
    if (auto* PC = Cast<APlayerController>(GetController()))
        if (auto* Sub = ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(PC->GetLocalPlayer())) Sub->AddMappingContext(DefaultContext, 0);
}
void AMyCharacter::SetupPlayerInputComponent(UInputComponent* Input) {
    if (auto* E = Cast<UEnhancedInputComponent>(Input)) {
        E->BindAction(MoveAction, ETriggerEvent::Triggered, this, &AMyCharacter::Move);
        E->BindAction(LookAction, ETriggerEvent::Triggered, this, &AMyCharacter::Look);
        E->BindAction(JumpAction, ETriggerEvent::Started, this, &ACharacter::Jump);
        E->BindAction(JumpAction, ETriggerEvent::Completed, this, &ACharacter::StopJumping);
    }
}
void AMyCharacter::Move(const FInputActionValue& V) {
    const FVector2D A = V.Get<FVector2D>(); const FRotator Yaw(0, GetControlRotation().Yaw, 0);
    AddMovementInput(FRotationMatrix(Yaw).GetUnitAxis(EAxis::X), A.Y); AddMovementInput(FRotationMatrix(Yaw).GetUnitAxis(EAxis::Y), A.X);
}
void AMyCharacter::Look(const FInputActionValue& V) { const FVector2D L = V.Get<FVector2D>(); AddControllerYawInput(L.X); AddControllerPitchInput(L.Y); }
```
Add `"EnhancedInput"` to `PublicDependencyModuleNames` in `<Project>.Build.cs`. In the editor: create `IA_Move` (Axis2D), `IA_Look` (Axis2D), `IA_Jump` (Digital), an `IMC_Default` mapping WASD (with Swizzle/Negate modifiers), mouse XY, Space; assign in the Blueprint subclass defaults; set it as Default Pawn in the GameMode.

## 5. Blueprint recipes (node walkthroughs)

**Pickup that adds a coin:** BP_Coin (Actor) with SphereCollision + Static Mesh. Event `OnComponentBeginOverlap (Sphere)` → Cast `Other Actor` to `BP_Player` → (Cast success) `Add Coins` custom event (+1) → Play Sound at Location → Spawn Emitter (Niagara) at Location → `Destroy Actor`.

**Door that opens on interact:** Timeline `OpenDoor` (float 0→1, 0.6 s) → `Lerp (Rotator)` A=closed, B=open → Set Relative Rotation on the door mesh. Trigger: Box overlap sets `bPlayerNear`; input action `Interact` → Branch (bPlayerNear) → Play/Reverse Timeline (Flip Flop).

**Health and damage:** Variable `Health` (float, 100). Event `AnyDamage` → `Health = Clamp(Health - Damage, 0, MaxHealth)` → update HUD → Branch (Health <= 0) → Death (disable input, play montage, delayed respawn).

**Spawn enemies in waves:** BP_WaveManager: `Set Timer by Event` (2 s, looping) → Spawn Actor from Class at random point around player (`GetRandomReachablePointInRadius` on NavMesh) → increment `SpawnedThisWave`; when equal to `WaveSize`, clear timer, wait until enemies dead, `WaveIndex++`.

## 6. Weapons and damage

Hitscan: `LineTraceByChannel` from camera location along forward vector × range → on hit: `ApplyDamage`/`UGameplayStatics::ApplyPointDamage`, spawn impact effect at `ImpactPoint` oriented by `ImpactNormal`. Projectile: Actor with `ProjectileMovementComponent`, `OnHit` → apply damage → destroy. Recoil: add pitch/yaw impulse to controller and recover over time (curve). Ammo: `AmmoInMag`, `ReserveAmmo`, reload timer.

```cpp
FHitResult Hit; FVector Start = Cam->GetComponentLocation(), End = Start + Cam->GetForwardVector() * 10000.f;
FCollisionQueryParams P; P.AddIgnoredActor(this);
if (GetWorld()->LineTraceSingleByChannel(Hit, Start, End, ECC_Visibility, P)) UGameplayStatics::ApplyPointDamage(Hit.GetActor(), 20.f, (End-Start).GetSafeNormal(), Hit, GetController(), this, nullptr);
```

## 7. UI (UMG)

Widget Blueprint: Canvas Panel + Progress Bar (health) + Text (ammo/score). Bind values via functions or update by events (preferred: event-driven, not per-tick bindings). Create in the PlayerController (`Create Widget` → `Add to Viewport`). Input mode: `Set Input Mode Game And UI` for menus with `Show Mouse Cursor`. Menus: `Open Level (by Name)`, `Quit Game`.

## 8. Data-driven design

DataTable from a row struct (`FTableRowBase` subclass) imported from CSV/JSON for items, enemies, weapons; Data Assets (`UPrimaryDataAsset`) for rich configs; Gameplay Tags for flags and categories. Designers edit data without recompiling.

## 9. AI

AIController + Behavior Tree + Blackboard. Blackboard keys: `TargetActor`, `LastKnownLocation`. Tree: Selector → [Sequence: has target → MoveTo target → Attack] → [Sequence: has LastKnown → MoveTo → clear] → Wander. Perception: `AIPerception` with Sight (radius, angle) and Hearing configs updating the Blackboard. Requires a Nav Mesh Bounds Volume in the level (press P to visualize).

## 10. Multiplayer basics

Server authoritative. Replicate state with `UPROPERTY(Replicated)` + `GetLifetimeReplicatedProps`; use `ReplicatedUsing=OnRep_X` to react on clients. Events: `UFUNCTION(Server, Reliable)` for client→server requests (validate!), `NetMulticast` for cosmetic effects. Never trust client-supplied damage or positions. Test with Play > Number of Players: 2, Net Mode: Play As Listen Server. Say explicitly when a design is single-player only.

## 11. VFX and materials

Niagara System: Emitter with Spawn Rate/Burst, Initialize Particle (lifetime, size, color), Add Velocity, Scale Color/Size over life, Sprite Renderer (additive material for fire/magic). Layer: flash + sparks + smoke + light. Materials: Dissolve = noise texture → `Step`/`Smoothstep` with a threshold parameter → Opacity Mask + emissive edge; expose `Dissolve` as a scalar parameter and drive it from a Timeline.

## 12. Packaging

File > Package Project (Windows/Android). Android needs Android Studio, SDK/NDK per the engine's Android setup page, and a signing keystore for shipping. Set Project Settings > Project > Description (name, version) and Maps & Modes (default maps) first. Package a Development build for testing, Shipping for release.

## 13. Common errors

| Error | Cause | Fix |
|---|---|---|
| Unresolved external symbol | Module missing in `Build.cs` | Add it to `PublicDependencyModuleNames` |
| Editor crash on hot reload | Header changes with Live Coding | Close editor, rebuild from IDE |
| Input does nothing | Mapping context not added, or wrong Default Pawn | `AddMappingContext` in BeginPlay; check GameMode |
| AI does not move | No NavMesh, or actor not on it | Add Nav Mesh Bounds Volume, press P |
| Cast fails | Wrong class or unpossessed pawn | Print the actual class; check `Get Player Character` index |
| Replication not working | Actor `bReplicates` false, or authority mistake | Set `bReplicates = true`; run logic with `HasAuthority()` |

## 14. Verification

Read the code for includes, macros (`UCLASS/GENERATED_BODY/UPROPERTY`), and module dependencies; give the editor setup as numbered steps; provide a test checklist (spawns, moves, jumps, hits, UI updates, restarts). Mark **open gap** unless confirmed in-editor.
