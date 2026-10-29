# CAD and 3D printing (FDM focus)

*Last updated: 2026-10-17 | Version-sensitive: slicer features; material properties by manufacturer | Re-check current docs before pinning versions, prices, or API names.*

Design parts that print well and fit together: parametric modeling, design rules, tolerances, materials, slicer settings, troubleshooting, and mesh checks. Tool: `scripts/stl_tools.py` (generate simple solids, check meshes). OpenSCAD and CadQuery snippets were **not run** (not installed in the test environment); the Python calculations and STL tooling were run. Physical results depend on the printer: label them **open gap** until a test print.

## Contents
1. Workflow
2. Choose the CAD approach
3. Design rules for FDM
4. Tolerances and fits
5. Strength and orientation
6. Common features: threads, snap fits, inserts, hinges
7. Parametric code examples (OpenSCAD, CadQuery)
8. Materials
9. Slicer settings
10. Troubleshooting table
11. Mesh checking and repair
12. Other processes: resin, CNC, laser
13. Verification

## 1. Workflow

Requirements (loads, environment, fit, appearance) → measure the real parts (calipers; do not trust nominal sizes) → sketch dimensions and tolerances → model parametrically → export STL/3MF → check the mesh (`stl_tools.py check`) → slice → **print a small test piece first** (fit coupons, one hole and one pin) → iterate on clearances → print the final part. Record the printer, nozzle, material, and settings with each design.

## 2. Choose the CAD approach

| Approach | Best for | Notes |
|---|---|---|
| OpenSCAD (code, CSG) | Parametric boxes, brackets, enclosures; version control | Everything is a script; easy to change dimensions |
| CadQuery / build123d (Python) | Parametric parts with fillets and sketches, programmatic generation | Needs the OCC kernel; scriptable pipelines |
| FreeCAD | Open-source feature-based CAD, assemblies | Learning curve; parametric history |
| Fusion/Onshape/SolidWorks | Complex mechanical design, sketches, drawings | Cloud/licensing terms vary |
| Blender | Organic shapes, sculpts (see `games/blender-art-vfx.md`) | Mesh-based; check watertightness; not dimension-driven |
Prefer parametric tools for functional parts: a dimension change should be one edit, not a remodel.

## 3. Design rules for FDM

Assume a 0.4 mm nozzle and 0.2 mm layers; adjust for your printer.
| Feature | Guideline |
|---|---|
| Wall thickness | At least 2 perimeters (about 0.8-1.2 mm); structural walls 1.6-2.4 mm |
| Smallest feature | About 0.8 mm wide; details below 0.4 mm will not print |
| Overhangs | Up to about 45-60 degrees without support; steeper needs supports or redesign (chamfer instead of a horizontal ceiling) |
| Bridges | Short spans (under about 30-50 mm) are fine; tune bridging settings |
| First layer | Large flat contact area on the bed; add chamfers (0.4-1 mm) on bottom edges to avoid elephant's foot |
| Holes | Print undersized: add 0.1-0.3 mm to diameter; vertical holes better than horizontal; teardrop shape for horizontal holes |
| Text/embossing | At least 0.6 mm stroke and 0.4-0.6 mm height; engrave less reliably than emboss |
| Corners | Fillets or chamfers (1-3 mm) reduce stress and warping |
| Large flat parts | Warp; add brims, reduce size, or split |
| Print-in-place | Moving parts need 0.3-0.5 mm clearance and tuned printer |
Design so the part prints **without supports** if possible: choose orientation, split into pieces, and use chamfers.

## 4. Tolerances and fits

Printed dimensions deviate by about 0.1-0.3 mm. Starting clearances per side (tune with a test coupon):
| Fit | Clearance (total diametral) |
|---|---|
| Press fit | 0.0-0.1 mm |
| Snug / locating | 0.15-0.25 mm |
| Sliding | 0.3-0.4 mm |
| Loose / print-in-place | 0.4-0.6 mm |
```python
# hole and pin sizes from nominal dimensions and a fit class (run to produce a table)
FIT = {"press": 0.05, "snug": 0.20, "sliding": 0.35, "loose": 0.50}   # diametral clearance in mm: tune per printer
def hole_diameter(pin_d, fit="sliding", shrink_comp=0.10):
    return round(pin_d + FIT[fit] + shrink_comp, 2)                 # shrink_comp: holes print small
for fit in FIT:
    print(f"{fit:8s} 8 mm pin -> {hole_diameter(8, fit)} mm hole")
```
Print a **tolerance coupon**: a row of holes (0.1 mm steps) and a gauge pin; pick the best fit and store the offset in your design parameters.

## 5. Strength and orientation

FDM parts are weakest between layers: orient so loads run along layers (tension across layers is the failure mode). Strength levers in order: orientation, wall/perimeter count (more perimeters beat infill), material, layer adhesion (temperature, slower cooling), infill (15-40% gyroid/cubic is usually plenty; 100% rarely helps). Thicken near holes and stress points; add ribs and fillets; avoid sharp internal corners. For critical loads test destructively with a sample, add a safety factor (at least 2-4), and never rely on 3D-printed parts for life-safety without qualified engineering.
Quick beam check (cantilever of rectangular section, small deflection): `deflection = F*L^3 / (3*E*I)`, `I = b*h^3/12`; printed PLA `E` about 2-3.5 GPa depending on direction (verify for your material).
```python
def cantilever_deflection_mm(force_n, length_mm, width_mm, height_mm, e_mpa=2500.0):
    inertia = width_mm * height_mm ** 3 / 12.0
    return force_n * length_mm ** 3 / (3.0 * e_mpa * inertia)
print(round(cantilever_deflection_mm(5, 50, 10, 3), 2), "mm for a 50x10x3 mm PLA tab with 5 N at the tip")
```

## 6. Common features

- **Threads:** model as simple coarse threads with clearance, or print a hole and tap it, or use heat-set inserts (best for repeated assembly). Large printed threads (M10+ or 8 mm pitch trapezoidal) work; tiny M3 threads usually do not.
- **Heat-set inserts:** design the hole 0.2-0.4 mm smaller than the insert's outer diameter per its datasheet, with depth for the insert plus 1-2 mm and a chamfer lead-in.
- **Screw holes:** clearance hole 0.3-0.5 mm larger than the screw; counterbore for heads; leave 2-3 perimeters of material around.
- **Snap fits:** cantilever length at least 5-10x thickness; fillet the root; keep strain low (PETG/Nylon flex better than PLA); orient layers along the beam, not across.
- **Living hinges:** thin (0.4-0.8 mm) PETG/TPU/Nylon, printed flat.
- **Magnets and bearings:** model pockets 0.1-0.2 mm oversized; pause the print to insert if needed.
- **Enclosures:** wall 2-3 mm, lid lip, standoffs for boards, ventilation, strain relief, cable exits, and access to ports; check the board dimensions with calipers.

## 7. Parametric code examples (not run here)

OpenSCAD:
```
// parametric box with lid lip (units: mm)
w = 60; d = 40; h = 25; wall = 2; tol = 0.3;
module shell() { difference() { cube([w, d, h]); translate([wall, wall, wall]) cube([w - 2*wall, d - 2*wall, h]); } }
module lid() { cube([w, d, wall]); translate([wall + tol, wall + tol, wall]) cube([w - 2*(wall + tol), d - 2*(wall + tol), 2]); }
shell(); translate([0, d + 10, 0]) lid();
```
CadQuery:
```python
import cadquery as cq
w, d, h, wall = 60, 40, 25, 2
box = cq.Workplane("XY").box(w, d, h).edges("|Z").fillet(3).faces(">Z").shell(-wall)
cq.exporters.export(box, "box.stl")
```
Keep dimensions as named parameters at the top; derive everything else; render and export from a script so changes are reproducible.

## 8. Materials

| Material | Strengths | Limits | Notes |
|---|---|---|---|
| PLA | Easy, stiff, detailed | Brittle, softens about 55-60 C, creeps | Default for prototypes; not for hot cars |
| PETG | Tougher, chemical/moisture resistant, better layer adhesion | Stringing, softer surface | Good functional all-rounder |
| ABS/ASA | Heat resistant, sandable/vapor-smoothable | Warps, fumes: needs enclosure and ventilation | ASA is UV stable |
| TPU | Flexible, impact resistant | Slow to print, bridging poor | Use direct-drive, slow speeds |
| Nylon / PA-CF | Strong, wear resistant | Absorbs moisture, warps | Dry filament; hardened nozzle for carbon fiber |
| Resin (SLA/MSLA) | High detail | Toxic uncured resin, post-processing | Gloves, ventilation, proper disposal |
Store filament dry (silica gel, dryer); wet filament causes stringing and weak parts.

## 9. Slicer settings

Layer height 0.1-0.3 mm (0.2 default), line width about nozzle diameter, perimeters 3-4 for functional parts, top/bottom layers 4-6, infill 15-40%, speed 40-60 mm/s for quality (outer wall slower), temperatures per filament datasheet (PLA about 190-215 C bed 55-65 C; PETG about 230-250 C bed 70-85 C; verify), cooling per material, retraction tuned to stop stringing, supports only where needed (tree supports for organic shapes), brim for warping. Slicers: Cura, PrusaSlicer, OrcaSlicer, Bambu Studio. Use the manufacturer's profile as the base and change one setting at a time. Always preview layer by layer before printing.

## 10. Troubleshooting table

| Symptom | Likely cause | Fix |
|---|---|---|
| First layer does not stick | Bed dirty/unlevel, nozzle too high, cold bed | Clean (IPA), re-level/adjust Z offset, raise bed temp, use glue/PEI |
| Warping/corners lift | Cooling, big flat area, drafts | Brim, enclosure, higher bed temp, reduce part cooling |
| Stringing/oozing | Wet filament, hot nozzle, weak retraction | Dry filament, lower temp 5-10 C, tune retraction |
| Layer shifting | Loose belts/pulleys, too fast, collisions | Tighten, slow down, check for obstructions |
| Under-extrusion (gaps) | Clog, low temp, worn extruder, wrong flow | Clean nozzle, raise temp, calibrate E-steps/flow |
| Over-extrusion/blobs | Flow too high, temp too high | Calibrate flow, lower temp |
| Weak parts | Wrong orientation, low temp, few perimeters | Re-orient, more perimeters, raise temp, slow cooling |
| Holes too small / parts too tight | Plastic expansion, no compensation | Add clearance/offset (section 4), tune horizontal expansion |
| Rough overhangs | Too steep, poor cooling | Chamfer design, more cooling, supports |

## 11. Mesh checking and repair

Generate or check meshes:
```
python scripts/stl_tools.py gen box --size 40 20 10 --out box.stl
python scripts/stl_tools.py gen tube --outer 10 --inner 7 --height 20 --segments 90 --out sleeve.stl --binary
python scripts/stl_tools.py check part.stl            # watertight? oriented? volume positive? degenerate faces?
```
A printable mesh is a **closed, consistently oriented solid with positive volume**. Typical repairs: close holes, merge duplicate vertices, fix inverted normals, remove degenerate faces, remove internal faces, make non-manifold edges manifold (MeshLab, Blender 3D-Print Toolbox, slicer auto-repair, Meshmixer-style tools). The check does not measure wall thickness, overhangs, or tolerances: use the slicer preview and a test print for those.

## 12. Other processes: resin, CNC, laser

Resin: orient at an angle to reduce suction/peel forces, add drain holes to hollow parts, support islands, post-wash and cure. CNC: design for tool radius (internal corner radius at least tool radius), standard stock sizes, workholding, and tolerances per process. Laser cutting: kerf compensation (about 0.1-0.3 mm), finger/tab joints, material thickness tolerance. Consider machines' safety requirements (enclosures, ventilation, fire safety).

## 13. Verification

Run the Python snippets; generate and check any STL you produce (`stl_tools.py check` must pass); document the printer, material, and the clearances used; list **open gap**: real fit, strength, and print quality until a test print; provide a test-coupon plan for the first print.
