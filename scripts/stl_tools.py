#!/usr/bin/env python3
"""STL tools for 3D-printing work (no dependencies): generate simple parametric solids and check meshes.

  python stl_tools.py gen box --size 40 20 10 --out box.stl
  python stl_tools.py gen cylinder --radius 5 --height 12 --segments 64 --out peg.stl
  python stl_tools.py gen tube --outer 10 --inner 7 --height 20 --out sleeve.stl [--binary]
  python stl_tools.py check part.stl            # triangles, bounding box, volume, area, watertight, orientation, degenerate faces
  python stl_tools.py check part.stl --json
Units are whatever you model in (normally millimeters). `check` reports a mesh as printable-ready only in the geometric sense
(closed, consistently oriented, positive volume); it does not check wall thickness, overhangs, or tolerances (see references/extra/cad-3d-printing.md).
Exit code 1 if the mesh is not closed/consistent or has non-positive volume.
"""
import argparse
import json
import math
import struct
import sys
from collections import Counter


def die(msg, code=2):
    print("error: " + msg, file=sys.stderr)
    sys.exit(code)


# ---------- geometry (triangles are ((x,y,z),(x,y,z),(x,y,z)), counter-clockwise seen from outside) ----------
def box(sx, sy, sz):
    x0, y0, z0, x1, y1, z1 = 0, 0, 0, sx, sy, sz
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    quads = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]  # outward normals
    t = []
    for a, b, c, d in quads:
        t += [(v[a], v[b], v[c]), (v[a], v[c], v[d])]
    return t


def ring(r, z, n):
    return [(r * math.cos(2 * math.pi * i / n), r * math.sin(2 * math.pi * i / n), z) for i in range(n)]


def cylinder(r, h, n):
    top, bot = ring(r, h, n), ring(r, 0, n)
    tc, bc = (0, 0, h), (0, 0, 0)
    t = []
    for i in range(n):
        j = (i + 1) % n
        t.append((tc, top[i], top[j]))        # top cap (normal +z)
        t.append((bc, bot[j], bot[i]))        # bottom cap (normal -z)
        t.append((bot[i], bot[j], top[j]))    # side
        t.append((bot[i], top[j], top[i]))
    return t


def tube(ro, ri, h, n):
    to, bo, ti, bi = ring(ro, h, n), ring(ro, 0, n), ring(ri, h, n), ring(ri, 0, n)
    t = []
    for i in range(n):
        j = (i + 1) % n
        t += [(bo[i], bo[j], to[j]), (bo[i], to[j], to[i])]            # outer wall, normal outward
        t += [(bi[j], bi[i], ti[i]), (bi[j], ti[i], ti[j])]            # inner wall, normal toward axis
        t += [(to[i], to[j], ti[j]), (to[i], ti[j], ti[i])]            # top annulus, +z
        t += [(bo[j], bo[i], bi[i]), (bo[j], bi[i], bi[j])]            # bottom annulus, -z
    return t


def normal(tri):
    (ax, ay, az), (bx, by, bz), (cx, cy, cz) = tri
    ux, uy, uz, vx, vy, vz = bx - ax, by - ay, bz - az, cx - ax, cy - ay, cz - az
    nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
    ln = math.sqrt(nx * nx + ny * ny + nz * nz)
    return (nx / ln, ny / ln, nz / ln) if ln > 1e-15 else (0.0, 0.0, 0.0)


def write_ascii(path, tris, name="part"):
    with open(path, "w", encoding="ascii") as f:
        f.write(f"solid {name}\n")
        for t in tris:
            n = normal(t)
            f.write(f"  facet normal {n[0]:.6e} {n[1]:.6e} {n[2]:.6e}\n    outer loop\n")
            for v in t:
                f.write(f"      vertex {v[0]:.6e} {v[1]:.6e} {v[2]:.6e}\n")
            f.write("    endloop\n  endfacet\n")
        f.write(f"endsolid {name}\n")


def write_binary(path, tris):
    with open(path, "wb") as f:
        f.write(b"binary STL written by stl_tools.py".ljust(80, b" "))
        f.write(struct.pack("<I", len(tris)))
        for t in tris:
            f.write(struct.pack("<3f", *normal(t)))
            for v in t:
                f.write(struct.pack("<3f", *v))
            f.write(b"\0\0")


def read_stl(path):
    try:
        data = open(path, "rb").read()
    except OSError as e:
        die(f"cannot read {path}: {e.strerror}")
    if len(data) < 15:
        die(f"{path} is too small to be an STL file")
    if len(data) >= 84:
        count = struct.unpack("<I", data[80:84])[0]
        if 84 + 50 * count == len(data):                       # binary layout matches exactly
            tris = []
            for i in range(count):
                rec = struct.unpack("<12fH", data[84 + 50 * i:134 + 50 * i])
                tris.append(((rec[3], rec[4], rec[5]), (rec[6], rec[7], rec[8]), (rec[9], rec[10], rec[11])))
            return tris
    text = data.decode("ascii", errors="replace")
    if "facet" not in text:
        die(f"{path} is neither a valid binary nor ASCII STL")
    verts = []
    for line in text.splitlines():
        p = line.split()
        if p and p[0] == "vertex":
            try:
                verts.append((float(p[1]), float(p[2]), float(p[3])))
            except (ValueError, IndexError):
                die(f"malformed vertex line: {line.strip()[:60]}")
    if not verts or len(verts) % 3:
        die("ASCII STL has no vertices or a vertex count that is not a multiple of 3")
    return [tuple(verts[i:i + 3]) for i in range(0, len(verts), 3)]


def analyze(tris, eps=1e-6):
    key = lambda v: (round(v[0] / eps), round(v[1] / eps), round(v[2] / eps))
    verts = {}
    idx = lambda v: verts.setdefault(key(v), len(verts))
    faces = [tuple(idx(v) for v in t) for t in tris]
    directed = Counter()
    degenerate = 0
    for f, t in zip(faces, tris):  # noqa: B905 - faces is built 1:1 from tris just above
        if len(set(f)) < 3 or normal(t) == (0.0, 0.0, 0.0):
            degenerate += 1
            continue
        for a, b in ((f[0], f[1]), (f[1], f[2]), (f[2], f[0])):
            directed[(a, b)] += 1
    open_edges = consistent = 0
    non_manifold = 0
    seen = set()
    for (a, b), c in directed.items():
        if (min(a, b), max(a, b)) in seen:
            continue
        seen.add((min(a, b), max(a, b)))
        fwd, rev = directed.get((a, b), 0), directed.get((b, a), 0)
        if fwd + rev != 2:
            if fwd + rev == 1:
                open_edges += 1
            else:
                non_manifold += 1
        elif fwd != 1 or rev != 1:
            consistent += 1                                   # two faces share the edge in the same direction (flipped face)
    vol = area = 0.0
    xs = [v for t in tris for v in t]
    for (a, b, c) in tris:
        vol += (a[0] * (b[1] * c[2] - b[2] * c[1]) - a[1] * (b[0] * c[2] - b[2] * c[0]) + a[2] * (b[0] * c[1] - b[1] * c[0])) / 6.0
        ux, uy, uz, vx, vy, vz = b[0] - a[0], b[1] - a[1], b[2] - a[2], c[0] - a[0], c[1] - a[1], c[2] - a[2]
        area += 0.5 * math.sqrt((uy * vz - uz * vy) ** 2 + (uz * vx - ux * vz) ** 2 + (ux * vy - uy * vx) ** 2)
    bb = [[min(v[i] for v in xs) for i in range(3)], [max(v[i] for v in xs) for i in range(3)]]
    return {"triangles": len(tris), "vertices": len(verts), "bbox_min": [round(x, 4) for x in bb[0]], "bbox_max": [round(x, 4) for x in bb[1]],
            "size": [round(bb[1][i] - bb[0][i], 4) for i in range(3)], "volume": round(vol, 4), "surface_area": round(area, 4),
            "open_edges": open_edges, "non_manifold_edges": non_manifold, "inconsistent_orientation_edges": consistent, "degenerate_triangles": degenerate,
            "watertight": open_edges == 0 and non_manifold == 0, "consistently_oriented": consistent == 0}


def cmd_gen(a):
    if a.shape == "box":
        if not a.size or len(a.size) != 3 or min(a.size) <= 0:
            die("box needs --size X Y Z (all > 0)")
        tris = box(*a.size)
    else:
        if a.segments < 3:
            die("--segments must be >= 3")
        if a.height is None or a.height <= 0:
            die("--height must be > 0")
        if a.shape == "cylinder":
            if a.radius is None or a.radius <= 0:
                die("cylinder needs --radius > 0")
            tris = cylinder(a.radius, a.height, a.segments)
        else:
            if a.outer is None or a.inner is None or not (0 < a.inner < a.outer):
                die("tube needs --outer and --inner with 0 < inner < outer")
            tris = tube(a.outer, a.inner, a.height, a.segments)
    (write_binary if a.binary else write_ascii)(a.out, tris) if a.binary else write_ascii(a.out, tris)
    print(f"wrote {a.out} ({len(tris)} triangles)")


def cmd_check(a):
    r = analyze(read_stl(a.file))
    ok = r["watertight"] and r["consistently_oriented"] and r["volume"] > 0 and r["degenerate_triangles"] == 0
    r["ok"] = ok
    if a.json:
        print(json.dumps(r, indent=1))
    else:
        print(f"triangles {r['triangles']}, vertices {r['vertices']}, size {r['size']}, volume {r['volume']}, area {r['surface_area']}")
        print(f"watertight: {r['watertight']} (open edges {r['open_edges']}, non-manifold {r['non_manifold_edges']}); consistently oriented: {r['consistently_oriented']}; degenerate triangles: {r['degenerate_triangles']}")
        if r["volume"] <= 0:
            print("volume is not positive: normals may be inverted (flip normals) or the mesh is not a closed solid")
        print("RESULT:", "geometry OK (still check wall thickness, overhangs, and tolerances)" if ok else "PROBLEMS FOUND: repair before slicing (e.g. close holes, fix normals)")
    sys.exit(0 if ok else 1)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("gen"); g.add_argument("shape", choices=["box", "cylinder", "tube"]); g.add_argument("--size", type=float, nargs=3)
    g.add_argument("--radius", type=float); g.add_argument("--outer", type=float); g.add_argument("--inner", type=float); g.add_argument("--height", type=float)
    g.add_argument("--segments", type=int, default=64); g.add_argument("--out", required=True); g.add_argument("--binary", action="store_true"); g.set_defaults(fn=cmd_gen)
    c = sub.add_parser("check"); c.add_argument("file"); c.add_argument("--json", action="store_true"); c.set_defaults(fn=cmd_check)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
