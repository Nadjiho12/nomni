# Multiplayer and netcode

*Last updated: 2026-10-13 | Version-sensitive: features and pricing of Photon/Nakama/Colyseus and cloud game hosting; WebTransport support | Re-check current docs before pinning versions, prices, or API names.*

Design real-time multiplayer the way shipped games do: authoritative server, input-based protocol, prediction and reconciliation, interpolation, lag compensation, and validation. Tested example: `scripts/examples/mp_server.js` (Node + `ws`: 20 Hz tick, speed-hack clamp, rate limits, snapshots with input acks).

## Contents
1. Choose the model
2. Transport options
3. Authoritative server architecture
4. Protocol design
5. Client-side prediction and reconciliation (runs)
6. Entity interpolation
7. Lag compensation for shooters
8. Bandwidth: snapshots, deltas, interest management
9. Anti-cheat and validation
10. Rooms, matchmaking, scaling
11. Persistence and accounts
12. Engine and service options
13. Testing under bad networks
14. Verification

## 1. Choose the model

| Model | Use | Trade-off |
|---|---|---|
| **Authoritative server** (clients send inputs) | Competitive games, anything with cheating risk | Needs server hosting; prediction needed for feel |
| Client-hosted (listen server / P2P host) | Co-op, casual | Cheap; host can cheat, host leaves = game ends, NAT traversal |
| Lockstep (deterministic simulation, exchange inputs) | RTS, fighting games | Perfect sync with tiny bandwidth; requires determinism, input delay or rollback |
| State sync (server sends state) | Most action games | Bandwidth grows with entities |
| Turn-based | Cards, strategy | Simple: REST/WebSocket and a database |
Default for action games: **authoritative server + state snapshots + client prediction**. Default for turn-based and slow games: plain HTTP/WebSocket with server-side validation.

## 2. Transport options

- **WebSocket (TCP):** simplest, works in browsers and behind proxies; head-of-line blocking causes stutter on packet loss. Fine for casual and mid-paced games.
- **WebRTC DataChannel (unreliable/unordered mode):** UDP-like semantics in browsers; more setup (signaling, STUN/TURN); good for fast action in the browser.
- **UDP (native games):** ENet, KCP, QUIC, custom reliability layers; best for fast games.
- **WebTransport (QUIC):** emerging browser option with datagrams.
Separate reliable messages (chat, purchases, events) from unreliable frequent ones (positions) when the transport allows.

## 3. Authoritative server architecture

```
Client: capture input -> send {seq, input} -> predict locally -> render interpolated remote entities
Server: receive inputs -> validate -> simulate fixed tick (20-60 Hz) -> broadcast snapshots (10-30 Hz) with last processed input seq
Client: on snapshot -> reconcile own state, buffer remote states for interpolation
```
Rules: the server owns positions, health, ammo, cooldowns, score. Clients never send "I am at X" or "I hit player Y"; they send inputs and fire requests. Fixed server tick independent of frame rate. One simulation function shared by client prediction and server (same code or same logic ported exactly).

## 4. Protocol design

- Small, versioned messages: `{t:'input', seq, dx, dz, fire, dt}`, `{t:'snap', tick, players:[...]}`, `{t:'event', ...}`. Send a protocol version in the handshake and reject mismatches.
- Include sequence numbers (inputs) and server tick numbers (snapshots) to order and ack.
- Use compact encodings for production (binary, quantized floats: positions in 1/100 units as int16, angles in 8-10 bits); JSON is fine for prototypes.
- Validate everything server-side: types, ranges, rates, sizes. Ignore unknown or malformed messages.
- Heartbeats and timeouts to drop dead connections; reconnect tokens for resuming.

## 5. Client-side prediction and reconciliation (runs)

The client applies its own inputs immediately (feels instant), keeps unacknowledged inputs, and when a server snapshot arrives it resets to the server state and replays the pending inputs.

```js
const SPEED = 6, DT = 1 / 20;
const applyInput = (s, i) => ({ x: s.x + i.dx * SPEED * DT, z: s.z + i.dz * SPEED * DT });   // identical on client and server
function makeClient() {
  let state = { x: 0, z: 0 }, seq = 0, pending = [];
  return {
    get state() { return state; },
    input(dx, dz) { const i = { seq: ++seq, dx, dz }; pending.push(i); state = applyInput(state, i); return i; },   // predict now, send i to the server
    onSnapshot(server) {                                                                                            // server = {x, z, ack}
      pending = pending.filter(i => i.seq > server.ack);                                                           // drop acknowledged inputs
      state = pending.reduce(applyInput, { x: server.x, z: server.z });                                            // rewind to server truth, replay the rest
    },
  };
}
// simulation: the server runs 2 ticks behind the client's inputs and a hostile correction shows the replay works
const c = makeClient(), inputs = [c.input(1, 0), c.input(1, 0), c.input(0, 1), c.input(0, 1)];
const serverAfter2 = inputs.slice(0, 2).reduce(applyInput, { x: 0, z: 0 });
c.onSnapshot({ ...serverAfter2, ack: 2 });
const serverAfter4 = inputs.reduce(applyInput, { x: 0, z: 0 });
console.log(Math.abs(c.state.x - serverAfter4.x) < 1e-9 && Math.abs(c.state.z - serverAfter4.z) < 1e-9 ? 'reconciled' : 'diverged');
```
If the server disagrees (collision, correction), the replay produces a small visible correction; smooth it with a short blend (lerp over 100 ms) instead of snapping, and snap only for large errors (teleport, respawn).

## 6. Entity interpolation

Remote entities are rendered **in the past** (about 2 snapshot intervals, e.g. 100 ms at 20 Hz): keep a buffer of timestamped snapshots, find the two surrounding the render time, and lerp between them. This hides jitter and packet loss. Extrapolate only briefly (under about 200 ms) with velocity, then freeze. Rotate with slerp/angle lerp; do not interpolate teleports (flag them).

## 7. Lag compensation for shooters

Players shoot at what they see (the past). The server keeps a short history of hitboxes (about 500 ms). When a shot arrives with the client's view time `t`, rewind other players' hitboxes to `t`, run the hit test, then restore. Cap rewind (for example 200 ms) so high-ping players cannot exploit it. Favor the shooter, but accept that victims may be hit "behind cover" at high latency; document the trade-off. Projectiles can be server-simulated with spawn-time compensation.

## 8. Bandwidth: snapshots, deltas, interest management

- Budget: for example 20 snapshots/s x 10 players x 12 bytes = ~2.4 KB/s per client downstream; verify against mobile data limits.
- Quantize and bit-pack; send deltas against the last acked snapshot; send full snapshots periodically for recovery.
- **Interest management:** send each client only entities near or visible to them (grid/spatial hash); reduce update rate for distant entities.
- Compress rarely (small packets compress poorly); batch messages per tick.

## 9. Anti-cheat and validation

- Never trust the client: validate movement (max speed per tick, collisions on the server), fire rate, ammo, cooldowns, and line of sight.
- Do not send hidden information (positions of enemies behind walls) if wall-hacks matter; use server-side visibility culling.
- Normalize and bound inputs (see the example server), rate-limit messages, cap message sizes, and ban or throttle repeat offenders.
- Detect statistical anomalies (aim snap, impossible reaction times) server-side and flag for review.
- Sign sessions with short-lived tokens; do not put secrets in the client.
- Be honest about the limit: a determined cheater can automate input; layered server-side checks raise the cost. Follow platform rules for any client-side anti-cheat.

## 10. Rooms, matchmaking, scaling

- **Rooms:** one process per match or many matches per process (Node/Go/Rust); room object owns players and tick loop. Cap players per room; destroy empty rooms.
- **Matchmaking:** queue by mode and skill (Elo/Glicko/TrueSkill), widen the window over time, region-aware, fill with bots when waiting too long.
- **Lobby/gateway:** stateless gateway that authenticates, finds or allocates a room server, and returns the address; use Redis for presence and room registry.
- **Scaling:** scale by adding game servers (horizontal); allocate with an orchestrator (Agones/Kubernetes, Nomad, or a simple scheduler); put servers near players; autoscale on free slots, not CPU alone.
- **Reconnects and migration:** keep a player slot for 30-60 s; no host migration needed with dedicated servers.

## 11. Persistence and accounts

Accounts and progress live in a database behind an API (not in the game server's memory); the game server reports results at match end (idempotent endpoint with a signed payload). Write inventory/currency changes server-to-server only. Plan for duplicate sessions, rollback after bugs, and account recovery. Never trust the client for purchases; verify receipts server-side.

## 12. Engine and service options

| Tool | Notes |
|---|---|
| Colyseus (Node) | Rooms, state sync, good for browser games |
| Socket.IO / ws | Build your own protocol (this example) |
| Nakama (Go) | Accounts, matchmaking, storage, realtime |
| Photon (PUN/Fusion/Quantum) | Hosted relay + prediction frameworks for Unity |
| Unity Netcode for GameObjects / Entities, Mirror, Fish-Net | Unity networking stacks |
| Unreal replication | Built-in server-authoritative replication and RPCs (`games/unreal.md`) |
| Godot high-level multiplayer | ENet-based with RPC annotations |
| PlayFab / Unity Gaming Services / GameLift / Agones | Hosting, matchmaking, allocation |
Pick a framework unless networking itself is your product; rolling your own costs months.

## 13. Testing under bad networks

Simulate latency (50-250 ms), jitter, and loss (1-10%). Linux: `tc qdisc add dev eth0 root netem delay 100ms 20ms loss 5%` (remove with `tc qdisc del dev eth0 root`). In-app: wrap send/receive with a delay queue and random drops. Test: reconnect, duplicate/out-of-order packets, client flood, oversize messages, clock drift, server restart, 2x and 10x load. Record desyncs by hashing authoritative state on both sides at intervals (lockstep) or comparing snapshots.

## 14. Verification

Run `scripts/examples/mp_server.js` with a test client: check the snapshot rate, that speed-hack inputs are clamped, that floods are rate-limited, and that garbage and oversized messages do not crash the server. Run the reconciliation snippet. Test with simulated latency and loss. Mark real-internet play, NAT traversal, and large-scale load **open gap** unless run.
