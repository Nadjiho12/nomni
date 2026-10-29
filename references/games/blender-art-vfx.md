# Blender scripting, pixel art, particles and VFX

*Last updated: 2026-10-01 | Version-sensitive: Blender bpy API and exporter operators; engine particle module names | Re-check current docs before pinning versions, prices, or API names.*

## Contents
1. Blender (bpy): setup, recipes, export
2. Geometry Nodes and modifiers
3. Pixel art: rules and generation script
4. Sprite sheets
5. Particles and VFX: theory and per-engine settings
6. JS particle system (drop-in)
7. Shader recipes
8. 2.5D and isometric art
9. Verification

## 1. Blender (bpy)

Run scripts headless: `blender -b -P script.py -- --out ./out` (add `--python-exit-code 1` in CI). In the GUI: Scripting workspace > New > paste > Run Script. Blender uses metric units, Z-up, right-handed axes. Apply scale (`Ctrl+A`) before export.

```python
import bpy, bmesh, math, sys
def clear():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete()
def mat(name, rgba, rough=0.5, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = rgba
    b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal; return m

clear()
# Primitive + material
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1)); cube = bpy.context.active_object; cube.name = "Crate"
cube.data.materials.append(mat("Wood", (0.45, 0.28, 0.12, 1), 0.8))
# Modifiers (non-destructive)
bev = cube.modifiers.new("Bevel", 'BEVEL'); bev.width = 0.05; bev.segments = 3
bpy.ops.object.shade_smooth()
# Keyframe animation: spin over 60 frames
cube.rotation_euler = (0, 0, 0); cube.keyframe_insert("rotation_euler", frame=1)
cube.rotation_euler = (0, 0, math.radians(360)); cube.keyframe_insert("rotation_euler", frame=60)
for fc in cube.animation_data.action.fcurves:
    for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
# Camera + light
bpy.ops.object.camera_add(location=(6, -6, 5), rotation=(math.radians(60), 0, math.radians(45))); bpy.context.scene.camera = bpy.context.active_object
bpy.ops.object.light_add(type='SUN', location=(4, -4, 8)); bpy.context.active_object.data.energy = 3
# Render
sc = bpy.context.scene; sc.render.resolution_x, sc.render.resolution_y = 1280, 720
sc.render.filepath = "//render.png"; bpy.ops.render.render(write_still=True)
```

Procedural mesh with `bmesh` (a low-poly tree):
```python
def cone(name, r, h, loc, segs=8):
    bpy.ops.mesh.primitive_cone_add(vertices=segs, radius1=r, depth=h, location=loc); o = bpy.context.active_object; o.name = name; return o
trunk = (bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.15, depth=1, location=(0,0,0.5)), bpy.context.active_object)[1]
trunk.data.materials.append(mat("Bark", (0.3,0.18,0.08,1)))
for i, z in enumerate((1.2, 1.7, 2.2)): cone(f"Leaf{i}", 0.9-i*0.25, 1.0, (0,0,z)).data.materials.append(mat("Leaf", (0.1,0.5,0.15,1)))
```

Batch export every object as a separate glTF (for web/Unity/Unreal):
```python
import os
out = os.path.abspath("./export"); os.makedirs(out, exist_ok=True)
for o in [o for o in bpy.data.objects if o.type == 'MESH']:
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
    bpy.ops.export_scene.gltf(filepath=os.path.join(out, o.name + ".glb"), export_format='GLB', use_selection=True)
    # FBX for Unity/Unreal: bpy.ops.export_scene.fbx(filepath=..., use_selection=True, apply_scale_options='FBX_SCALE_ALL')
```

Pipeline: block out → clean topology → UV unwrap (`Smart UV Project`) → materials/textures (bake if needed) → rig (Armature, weight paint or automatic weights) → animate (Action, NLA) → export. Say which stage a script covers. Low-poly game rule of thumb: props 500-3k tris, characters 3k-15k mobile, more on PC/console.

## 2. Geometry Nodes and modifiers

Reusable procedural setups: scatter instances on a surface (`Distribute Points on Faces` → `Instance on Points` with `Random Value` for rotation/scale), array with curve, procedural buildings (repeat zone), terrain (`Noise Texture` → `Set Position` offset in Z). Modifier order matters (Mirror → Subdivision → Bevel). Keep modifiers live until export; apply only when needed. Describe node graphs as "node A (settings) → node B" since they cannot be pasted as text.

## 3. Pixel art

Rules: fix a palette (16-32 colors, e.g. from a known set) and a grid (16, 32, 64 px); one light direction; shade with hue shifts (shadows cooler/more saturated, highlights warmer); no soft brushes or partial transparency; clean single-pixel outlines, or selective outlines colored darker than the fill; consistent pixel scale across all assets (no mixed resolutions).

Generate sprites and textures in code (Python + Pillow):
```python
from PIL import Image
PAL = {".": (0,0,0,0), "k": (20,20,30,255), "g": (80,180,90,255), "d": (40,110,60,255), "y": (250,220,90,255)}
SPRITE = ["................", "....kkkkkkkk....", "...kggggggggk...", "..kggyggggyggk..", "..kggggggggggk..", "..kgddggggddgk..",
          "..kgggddddgggk..", "...kggggggggk...", "....kkkkkkkk...."]  # 16 wide
def render(rows, scale=8):
    w, h = len(rows[0]), len(rows); im = Image.new("RGBA", (w, h))
    for y, r in enumerate(rows):
        for x, c in enumerate(r): im.putpixel((x, y), PAL[c])
    return im.resize((w*scale, h*scale), Image.NEAREST)
render(SPRITE).save("slime.png")
```
Techniques: dithering (Bayer matrix threshold) for gradients; palette swap for enemy variants (map indices, not recolor by hand); outlines by dilating the alpha mask; procedural terrain tiles from noise thresholds. Browser: `image-rendering: pixelated; imageSmoothingEnabled = false`, integer scale only.

## 4. Sprite sheets

Uniform cells (e.g. 32x32), rows per animation (idle 4, walk 6-8, attack 4-6, hurt 2, death 6). Slice and pack:
```python
from PIL import Image
def pack(frames, cols=8):
    fw, fh = frames[0].size; rows = -(-len(frames)//cols); sheet = Image.new("RGBA", (fw*cols, fh*rows))
    for i, f in enumerate(frames): sheet.paste(f, ((i%cols)*fw, (i//cols)*fh))
    return sheet
def slice_sheet(path, fw, fh): im = Image.open(path); return [im.crop((x,y,x+fw,y+fh)) for y in range(0,im.height,fh) for x in range(0,im.width,fw)]
```
Animation timing: 8-12 fps for pixel animation (hold each frame 80-125 ms); anticipation → action → recovery; squash on landing. Export JSON atlas (`{name:{x,y,w,h}}`) for engines; Unity: Sprite Mode Multiple + Slice by Grid, Filter Point (no filter), Compression None; Godot: `AnimatedSprite2D` + SpriteFrames; Phaser: `load.spritesheet(key, url, {frameWidth, frameHeight})`.

## 5. Particles and VFX

Every effect = parameters. Design by layering (an explosion = flash + fireball + sparks + smoke + shockwave + light + camera shake).

| Parameter | Fire | Smoke | Sparks | Magic | Rain |
|---|---|---|---|---|---|
| Emission | 30-60/s | 10-20/s | burst 20-40 | 20-40/s | 200-500/s |
| Lifetime (s) | 0.6-1.2 | 2-4 | 0.3-0.8 | 1-2 | 0.5-1 |
| Start speed | 0.5-1.5 up | 0.3-0.8 up | 3-8 radial | 0.5-2 swirl | 8-15 down |
| Size over life | 1 → 0 | 0.5 → 2 | 1 → 0 | 1 → 0.2 | constant |
| Color over life | yellow→orange→red, alpha→0 | dark grey, alpha→0 | white→orange | cyan→purple | pale blue |
| Blend | Additive | Alpha | Additive | Additive | Alpha |
| Gravity | -0.2 (rises) | -0.05 | 1 | 0 | 1 |

Engine mapping:
- **Unity Particle System**: Duration, Looping, Start Lifetime/Speed/Size/Color (Random Between Two Constants), Gravity Modifier; modules: Emission (Rate/Bursts), Shape (Cone/Sphere/Edge), Color over Lifetime (gradient), Size over Lifetime (curve), Noise, Trails, Renderer (Material: Particles/Standard Unlit, Additive), Collision, Sub Emitters (for explosion debris).
- **Unreal Niagara**: Emitter Update (Spawn Rate/Burst), Particle Spawn (Initialize Particle: Lifetime, Color, Sprite Size; Add Velocity), Particle Update (Scale Color, Scale Sprite Size, Curl Noise Force), Render (Sprite Renderer, additive translucent material).
- **Blender**: Particle System (Emitter) or Geometry Nodes instances; for game VFX bake flipbook textures via a Smoke/Fire sim.

Performance: cap live particles (hundreds on mobile), avoid large overlapping alpha quads (overdraw), pool effect prefabs, GPU particles when counts are high, LOD (fewer particles at distance).

## 6. JS particle system (drop-in)

```js
class Particles {
  constructor(){ this.list = []; }
  burst(x, y, n, o = {}){
    for (let i = 0; i < n; i++){ const a = Math.random() * Math.PI*2, s = (o.speed||100) * (0.4 + Math.random()*0.6);
      this.list.push({ x, y, vx: Math.cos(a)*s, vy: Math.sin(a)*s, life: 0, max: (o.life||0.7) * (0.6+Math.random()*0.8), size: o.size||3, gravity: o.gravity??200, c: o.colors||['#fff2a8','#ffb347','#ff5a3c'] }); } }
  update(dt){ for (const p of this.list){ p.life += dt; p.vy += p.gravity*dt; p.x += p.vx*dt; p.y += p.vy*dt; } this.list = this.list.filter(p => p.life < p.max); }
  draw(ctx){ ctx.save(); ctx.globalCompositeOperation = 'lighter';               // additive
    for (const p of this.list){ const t = p.life/p.max, c = p.c[Math.min(p.c.length-1, (t*p.c.length)|0)];
      ctx.globalAlpha = 1 - t; ctx.fillStyle = c; const s = p.size*(1-t*0.7); ctx.fillRect(p.x-s/2, p.y-s/2, s, s); } ctx.restore(); }
}
// usage: const fx = new Particles(); on hit: fx.burst(enemy.x, enemy.y, 24, {speed:160}); each frame: fx.update(dt); fx.draw(ctx);
```
Variants: trail = spawn one particle per frame at the projectile; smoke = negative gravity, grow size, alpha blend; confetti = random colors + rotation + drag.

## 7. Shader recipes

GLSL fragment sketches (translate to HLSL/Shader Graph/Unreal material nodes):
```glsl
// Dissolve: noise threshold + glowing edge
float n = texture2D(uNoise, vUv).r; if (n < uCut) discard;
float edge = smoothstep(uCut, uCut + 0.05, n); vec3 col = mix(vec3(1.0,0.5,0.1), baseColor, edge);
// Fresnel rim
float f = pow(1.0 - max(dot(normalize(vNormal), normalize(vViewDir)), 0.0), 3.0); col += uRimColor * f;
// Scrolling UV (water/lava/energy)
vec2 uv = vUv + vec2(uTime*0.05, uTime*0.02);
// Outline (post-process idea): sample depth/normals at 4 neighbors, edge = length(difference)
// Toon shading: step/quantize NdotL into 3 bands: float b = floor(ndl*3.0)/3.0;
// Hit flash: col = mix(col, vec3(1.0), uFlash);   // animate uFlash 1 -> 0 over 0.1 s
```

## 8. 2.5D and isometric art

Parallax: layers scroll at `factor` of camera speed (far 0.2, mid 0.5, near 0.8, foreground 1.2). Y-sorting: draw by `y` (bottom of sprite) so lower objects overlap higher ones. Isometric tiles: 2:1 ratio (64x32) diamonds; depth order by `x+y`; convert with the isometric formulas in `games/core.md`. Billboards: sprites in a 3D scene rotated to face the camera (`sprite.lookAt(camera.position)` or Sprite objects in Three.js); fixed-camera 3D with 2D gameplay uses constraints on one axis.

## 9. Verification

Blender scripts: run headless and confirm the output file exists (`blender -b -P s.py`); when Blender is unavailable, syntax-check with `python -m py_compile` and mark **open gap**. Pixel art scripts: run them and open the PNG. Particles: run the JS in a browser preview or reason through lifetime, alpha, and cleanup; confirm particles are removed when dead.
