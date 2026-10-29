// Drives scripts/examples/mp_server.js with three clients: speed-hack clamp, snapshot rate, rate limit, garbage input.
const WebSocket = require('ws');
const { startServer, SPEED } = require('../../scripts/examples/mp_server.js');
const srv = startServer(0 + (9100 + Math.floor(Math.random() * 500)));
const port = srv.wss.options.port; const url = 'ws://127.0.0.1:' + port;
const mk = () => new Promise(res => { const ws = new WebSocket(url), st = { snaps: [], id: null, ws }; ws.on('message', d => { const m = JSON.parse(d); if (m.t === 'welcome') { st.id = m.id; res(st); } else st.snaps.push(m); }); });
const sleep = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  const A = await mk(), B = await mk(), C = await mk();
  let seq = 0; const t0 = Date.now();
  while (Date.now() - t0 < 1000) { A.ws.send(JSON.stringify({ t: 'input', dx: 1000, dz: 0, seq: ++seq })); await sleep(50); }
  await sleep(150);
  const last = (cl, id) => [...cl.snaps].reverse().find(s => s.players.find(p => p.id === id)).players.find(p => p.id === id);
  const lastA = last(B, A.id);
  const rate = B.snaps.length / ((Date.now() - t0) / 1000);
  for (let i = 1; i <= 300; i++) C.ws.send(JSON.stringify({ t: 'input', dx: 1, dz: 0, seq: i }));
  C.ws.send('x'.repeat(5000)); C.ws.send('not json');
  await sleep(300);
  const lastC = last(B, C.id);
  console.log('A moved x =', lastA.x, '(expected about', SPEED * 1.15, ', never thousands)', '| snapshot rate', rate.toFixed(1), '| C acked', lastC.ack);
  const pass = lastA.x > 4 && lastA.x < 9 && lastC.ack <= 60 && rate > 15 && rate < 25;
  console.log(pass ? 'MP TEST PASS' : 'MP TEST FAIL'); srv.stop(); process.exit(pass ? 0 : 1);
})();
