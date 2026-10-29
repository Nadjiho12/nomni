# Browser games and Android APK

*Last updated: 2026-10-03 | Version-sensitive: Capacitor/Three.js/Phaser versions; Android SDK and Play Store requirements | Re-check current docs before pinning versions, prices, or API names.*

## Contents
1. Choosing a browser tech
2. Canvas 2D patterns
3. Three.js starter
4. Phaser starter
5. Audio and touch
6. Performance
7. Turning a web game into an Android APK
8. Other APK routes
9. Mobile checklist
10. Verification and limits

## 1. Choosing a browser tech

| Need | Pick |
|---|---|
| Small 2D, full control, no dependencies | Canvas 2D + your own loop (`scaffold.py canvas-game`) |
| 2D with physics, tilemaps, scenes | Phaser 3 |
| 3D | Three.js (or Babylon.js for a full engine) |
| Pixel-perfect retro | Canvas at low resolution, CSS upscaled with `image-rendering: pixelated` |
| Physics only | Matter.js (2D), Rapier or cannon-es (3D) |

Serve modules with `python -m http.server`; `file://` blocks ES modules.

## 2. Canvas 2D patterns

```js
// Crisp on retina
function fit(cv){ const r=devicePixelRatio||1; cv.width=cv.clientWidth*r; cv.height=cv.clientHeight*r; cv.getContext('2d').setTransform(r,0,0,r,0,0); }
// Sprite sheet animation: frames in a row, size fw x fh
function drawFrame(ctx,img,frame,fw,fh,x,y){ ctx.drawImage(img, frame*fw, 0, fw, fh, x|0, y|0, fw, fh); }
// Camera follow with smoothing + clamp
cam.x += (player.x - cam.w/2 - cam.x) * (1 - Math.exp(-8*dt)); cam.x = clamp(cam.x, 0, world.w - cam.w);
ctx.save(); ctx.translate(-cam.x|0, -cam.y|0); drawWorld(); ctx.restore(); drawHUD();
// Tilemap render only visible tiles
for (let ty=cam.y/T|0; ty<=(cam.y+cam.h)/T|0; ty++) for (let tx=cam.x/T|0; tx<=(cam.x+cam.w)/T|0; tx++) drawTile(map[ty]?.[tx], tx*T, ty*T);
// Screen shake
shake = Math.max(0, shake - dt*30); ctx.translate((Math.random()-.5)*shake, (Math.random()-.5)*shake);
// Preload images
const load = src => new Promise(r => { const i = new Image(); i.onload = () => r(i); i.src = src; });
```

Offscreen cache for static art: draw once to an offscreen canvas, blit each frame.

## 3. Three.js starter

```html
<script type="importmap">{"imports":{"three":"https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.module.js"}}</script>
```
(For a page with no import map, use the classic script from cdnjs and the global `THREE`.)

```js
const scene = new THREE.Scene(); scene.background = new THREE.Color(0x0b0d12);
const camera = new THREE.PerspectiveCamera(60, innerWidth/innerHeight, 0.1, 200); camera.position.set(0, 3, 6);
const renderer = new THREE.WebGLRenderer({antialias:true}); renderer.setSize(innerWidth, innerHeight); renderer.setPixelRatio(Math.min(devicePixelRatio,2));
document.body.appendChild(renderer.domElement);
scene.add(new THREE.HemisphereLight(0xffffff, 0x223344, 1)); const sun = new THREE.DirectionalLight(0xffffff, 1); sun.position.set(5,10,5); scene.add(sun);
const cube = new THREE.Mesh(new THREE.BoxGeometry(1,1,1), new THREE.MeshStandardMaterial({color:0x6ee7b7})); scene.add(cube);
const floor = new THREE.Mesh(new THREE.PlaneGeometry(50,50), new THREE.MeshStandardMaterial({color:0x1b2330})); floor.rotation.x = -Math.PI/2; scene.add(floor);
const clock = new THREE.Clock();
renderer.setAnimationLoop(() => { const dt = clock.getDelta(); cube.rotation.y += dt; renderer.render(scene, camera); });
addEventListener('resize', () => { camera.aspect = innerWidth/innerHeight; camera.updateProjectionMatrix(); renderer.setSize(innerWidth, innerHeight); });
```

Notes: r128 has no `CapsuleGeometry` and `OrbitControls` is a separate file; use Box/Sphere/Cylinder or custom geometry. Reuse geometries and materials; use `InstancedMesh` for hundreds of identical objects; raycasting for picking (`Raycaster.setFromCamera`).

## 4. Phaser starter

```js
new Phaser.Game({ type: Phaser.AUTO, width: 800, height: 450, physics: { default: 'arcade', arcade: { gravity: { y: 600 } } },
  scene: { preload(){ this.load.image('p', 'player.png'); }, create(){ this.p = this.physics.add.sprite(100,100,'p'); this.cur = this.input.keyboard.createCursorKeys();
    const ground = this.add.rectangle(400,440,800,20,0x444444); this.physics.add.existing(ground, true); this.physics.add.collider(this.p, ground); },
    update(){ this.p.setVelocityX(this.cur.left.isDown?-160:this.cur.right.isDown?160:0); if(this.cur.up.isDown && this.p.body.blocked.down) this.p.setVelocityY(-380); } } });
```

## 5. Audio and touch

```js
// Unlock audio on first gesture, then synth SFX with no files
const AC = new (window.AudioContext||window.webkitAudioContext)(); addEventListener('pointerdown', () => AC.resume(), {once:true});
function beep(freq=440, dur=.1, type='square', vol=.1){ const o=AC.createOscillator(), g=AC.createGain(); o.type=type; o.frequency.value=freq;
  g.gain.setValueAtTime(vol, AC.currentTime); g.gain.exponentialRampToValueAtTime(0.0001, AC.currentTime+dur); o.connect(g).connect(AC.destination); o.start(); o.stop(AC.currentTime+dur); }
// coin: beep(880,.08); then beep(1320,.12)  | hit: noise burst | jump: frequency slide up
```

Touch: use pointer events; draw a virtual joystick (base + knob, clamp knob radius, output vector); buttons at least 48 px; set `touch-action:none` on the canvas; prevent page scroll and double-tap zoom.

## 6. Performance

Keep draw calls low (batch sprites, texture atlases); avoid allocating in `update`; pool bullets and particles; cull off-screen objects; cap `devicePixelRatio` at 2; profile with the browser Performance tab; target 60 fps on a mid-range phone with the resolution scaled down if needed.

## 7. Turning a web game into an Android APK (Capacitor)

Prerequisites on the user's machine: Node 18+, Android Studio (SDK + platform tools), JDK 17.

```bash
mkdir mygame-app && cd mygame-app
npm init -y && npm i @capacitor/core @capacitor/cli @capacitor/android
npx cap init MyGame com.yourname.mygame --web-dir=www
mkdir www && cp -r ../my-game/* www/          # index.html at www/index.html
npx cap add android
npx cap sync android
npx cap open android                            # Android Studio: Build > Build Bundle(s)/APK(s) > Build APK(s)
```

Debug APK appears under `android/app/build/outputs/apk/debug/`. Release: create a keystore (`keytool -genkey -v -keystore my.jks -alias key -keyalg RSA -keysize 2048 -validity 10000`), configure signing in `android/app/build.gradle`, build a signed AAB for Play Store (or signed APK for sideloading).

Config touches: `android/app/src/main/AndroidManifest.xml` for `screenOrientation="landscape"`; app icons via Android Studio Image Asset; `capacitor.config.json` for `appId`, `appName`, `webDir`.

## 8. Other APK routes

| Route | When | Key steps |
|---|---|---|
| TWA (Trusted Web Activity) / Bubblewrap | Hosted PWA, thin wrapper | `npx @bubblewrap/cli init --manifest https://site/manifest.json`, `build` |
| Godot 4 export | Game built in Godot | Install export templates, set Android SDK path in Editor Settings, Project > Export > Android |
| Unity | Game built in Unity | Build Settings > Android > Switch Platform, Player Settings (package name, min API), Build |
| Native Kotlin | Deep Android integration | Android Studio, `SurfaceView` or Jetpack Compose canvas |

## 9. Mobile checklist

Orientation locked · safe-area insets respected · 60 fps target · texture memory small · pause on `visibilitychange` and app background · handle the Android back button (Capacitor `App.addListener('backButton', ...)`) · touch targets 48 px · audio resumes after interruption · offline works (assets bundled) · app icon and splash set · permissions minimal.

## 10. Verification and limits

Browser games are verifiable here: run `scripts/verify_web.py` (headless Chromium, scenarios, screenshots) and view a screenshot. **Needs a real run:** the APK build (Android SDK hosts are usually blocked), real-device performance, and touch feel. Deliver exact commands, list the first three things to test on a device, and mark them **open gap**.
