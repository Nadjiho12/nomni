// Minimal authoritative multiplayer server (Node + ws). Run: npm i ws && node mp_server.js
// Server owns all state. Clients send INPUT (direction + sequence number), never positions.
// Includes: tick loop, speed clamp (input normalization), size + rate limits, snapshots with input acks.
const { WebSocketServer } = require('ws');
const TICK = 20, SPEED = 6, ARENA = 38, MAX_MSG = 512, MAX_MSGS_PER_SEC = 60;
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));

function startServer(port) {
  const wss = new WebSocketServer({ port });
  const players = new Map(); let nextId = 1;
  wss.on('connection', ws => {
    const id = nextId++, p = { id, ws, x: 0, z: 0, seq: 0, input: { dx: 0, dz: 0 }, msgs: 0, windowStart: Date.now() };
    players.set(id, p);
    ws.send(JSON.stringify({ t: 'welcome', id, tick: TICK, speed: SPEED }));
    ws.on('message', raw => {
      if (raw.length > MAX_MSG) return;                                            // size limit
      const now = Date.now();
      if (now - p.windowStart > 1000) { p.windowStart = now; p.msgs = 0; }
      if (++p.msgs > MAX_MSGS_PER_SEC) return;                                      // rate limit
      let m; try { m = JSON.parse(raw); } catch { return; }
      if (m.t === 'input' && Number.isFinite(m.dx) && Number.isFinite(m.dz) && Number.isInteger(m.seq) && m.seq > p.seq) {
        const len = Math.hypot(m.dx, m.dz), k = len > 1 ? 1 / len : 1;              // cap input magnitude at 1: speed hacks fail
        p.input = { dx: m.dx * k, dz: m.dz * k }; p.seq = m.seq;
      }
    });
    ws.on('close', () => players.delete(id));
  });
  const timer = setInterval(() => {
    const dt = 1 / TICK;
    for (const p of players.values()) { p.x = clamp(p.x + p.input.dx * SPEED * dt, -ARENA, ARENA); p.z = clamp(p.z + p.input.dz * SPEED * dt, -ARENA, ARENA); }
    const snap = JSON.stringify({ t: 'snap', time: Date.now(), players: [...players.values()].map(p => ({ id: p.id, x: +p.x.toFixed(3), z: +p.z.toFixed(3), ack: p.seq })) });
    for (const p of players.values()) if (p.ws.readyState === 1) p.ws.send(snap);
  }, 1000 / TICK);
  return { wss, players, stop: () => { clearInterval(timer); wss.close(); } };
}
module.exports = { startServer, TICK, SPEED };
if (require.main === module) { startServer(+process.env.PORT || 8080); console.log('listening on', process.env.PORT || 8080); }
