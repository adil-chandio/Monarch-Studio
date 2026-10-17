#!/usr/bin/env python3
"""Procedurally sculpt three-dimensional hair, skin, clothes and rig props.

No flat human cutouts/cards are used. The only image is a one-time diffuse
texture projected onto the 468-vertex face mesh created by fit_face.py.
Sensitive geometries are written to an ignored .runtime/model directory.
"""
from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np


class TriMesh:
    def __init__(self) -> None:
        self.vertices: list[tuple[float, float, float]] = []
        self.faces: list[tuple[int, int, int]] = []

    def vertex(self, p: tuple[float, float, float] | np.ndarray) -> int:
        self.vertices.append(tuple(map(float, p)))
        return len(self.vertices) - 1

    def face(self, a: int, b: int, c: int) -> None:
        if len({a, b, c}) == 3:
            self.faces.append((a, b, c))

    def quad(self, a: int, b: int, c: int, d: int) -> None:
        self.face(a, b, c)
        self.face(a, c, d)

    def save(self, path: Path, uv_project=None) -> None:
        with path.open("w") as f:
            f.write("# Procedural 3D mesh, Monarch true3d. Not an image plane.\n")
            for x, y, z in self.vertices:
                f.write(f"v {x:.7f} {y:.7f} {z:.7f}\n")
            if uv_project:
                for x, y, z in self.vertices:
                    u, v = uv_project(x, y, z)
                    f.write(f"vt {u:.7f} {v:.7f}\n")
            for a, b, c in self.faces:
                if uv_project:
                    f.write(f"f {a+1}/{a+1} {b+1}/{b+1} {c+1}/{c+1}\n")
                else:
                    f.write(f"f {a+1} {b+1} {c+1}\n")


def ellipsoid(m: TriMesh, center: tuple[float, float, float], radii: tuple[float, float, float], rings: int = 14, sides: int = 24) -> None:
    """Closed, shaded ellipsoid; Y is depth, Z is up."""
    first = m.vertex((center[0], center[1], center[2] + radii[2]))
    prev: list[int] | None = None
    for j in range(1, rings):
        latitude = math.pi * j / rings
        band = []
        for k in range(sides):
            theta = 2 * math.pi * k / sides
            band.append(m.vertex((center[0] + radii[0] * math.sin(latitude) * math.cos(theta),
                                  center[1] + radii[1] * math.sin(latitude) * math.sin(theta),
                                  center[2] + radii[2] * math.cos(latitude))))
        if prev is None:
            for k in range(sides):
                m.face(first, band[k], band[(k + 1) % sides])
        else:
            for k in range(sides):
                nxt = (k + 1) % sides
                m.quad(prev[k], prev[nxt], band[nxt], band[k])
        prev = band
    last = m.vertex((center[0], center[1], center[2] - radii[2]))
    assert prev
    for k in range(sides):
        m.face(prev[k], last, prev[(k + 1) % sides])


def tube(m: TriMesh, points: list[tuple[float, float, float]], radius: float | list[float], sides: int = 8) -> None:
    """An honest tubular 3D mesh (hair strands, cyber-cables or a finger)."""
    if len(points) < 2:
        raise ValueError("A tube requires at least two control points")
    pts = [np.asarray(p, dtype=float) for p in points]
    r = [radius] * len(points) if isinstance(radius, (int, float)) else radius
    if len(r) != len(points):
        raise ValueError("One radius per ring is required")
    bands: list[list[int]] = []
    for i, p in enumerate(pts):
        tangent = pts[min(i + 1, len(pts) - 1)] - pts[max(0, i - 1)]
        tangent /= np.linalg.norm(tangent)
        ref = np.array((0., 1., 0.)) if abs(tangent[1]) < .8 else np.array((0., 0., 1.))
        a = np.cross(tangent, ref); a /= np.linalg.norm(a)
        b = np.cross(tangent, a); b /= np.linalg.norm(b)
        band = [m.vertex(p + float(r[i]) * (a * math.cos(2 * math.pi * j / sides)
                                              + b * math.sin(2 * math.pi * j / sides))) for j in range(sides)]
        if bands:
            prev = bands[-1]
            for j in range(sides):
                nxt = (j + 1) % sides
                m.quad(prev[j], prev[nxt], band[nxt], band[j])
        bands.append(band)
    cap0, cap1 = m.vertex(pts[0]), m.vertex(pts[-1])
    for j in range(sides):
        m.face(cap0, bands[0][(j + 1) % sides], bands[0][j])
        m.face(cap1, bands[-1][j], bands[-1][(j + 1) % sides])


def fabric_piece(m: TriMesh, polygon_xz: list[tuple[float, float]], y: float, thickness: float = .004) -> None:
    """Thick sewn geometry; the visible face normal points toward the camera."""
    front = [m.vertex((x, y, z)) for x, z in polygon_xz]
    back = [m.vertex((x, y + thickness, z)) for x, z in polygon_xz]
    # Triangle fan. All pieces here are convex. Flip winding to face negative Y.
    for i in range(1, len(front) - 1):
        a, b, c = front[0], front[i], front[i+1]
        va = np.array(m.vertices[a]);vb = np.array(m.vertices[b]);vc = np.array(m.vertices[c])
        if np.cross(vb-va, vc-va)[1] > 0:
            b, c = c, b
        m.face(a,b,c)
        m.face(back[0], back[i+1], back[i])
    for i in range(len(front)):
        j = (i + 1) % len(front)
        m.quad(front[i], front[j], back[j], back[i])


def make_sphere() -> TriMesh:
    m = TriMesh(); ellipsoid(m, (0, 0, 0), (1, 1, 1), 16, 28); return m


def make_skin() -> TriMesh:
    m = TriMesh()
    # Skull lies BEHIND the photographed face surface; cheeks, profile and back
    # are actual modeled geometry, not a billboard.
    ellipsoid(m, (0.002, .097, .004), (.080, .063, .103), 20, 32)
    # Slightly tapered neck emerges from the model's jaw into the open collar.
    tube(m, [(.001,.07,-.097),(.001,.071,-.126),(.001,.076,-.194)], [.033,.038,.042], 22)
    for side in (-1,1):
        ellipsoid(m,(side*.073,.065,-.020),(.011,.015,.026),10,16)
        ellipsoid(m,(side*.073,.050,-.030),(.007,.006,.010),8,12)
    return m


def make_hair() -> tuple[TriMesh, TriMesh, TriMesh, TriMesh]:
    cap, locks, flyaways = TriMesh(), TriMesh(), TriMesh()
    sides=48; layers=13
    bands=[]
    for j in range(layers):
        u=j/layers
        band=[]
        for k in range(sides):
            a=2*math.pi*k/sides
            frontness=math.cos(a)
            bottom=(.067+.004*math.sin(7*a)+.003*math.sin(13*a))*max(0.,frontness) - .057*max(0.,-frontness) - .018*abs(math.sin(a))
            z=bottom + (.157-bottom)*u
            rx=(.096+.0016*math.sin(26*a+u*3))*math.cos(math.pi*u/2)
            ry=(.082+.0013*math.sin(25*a+u*5))*math.cos(math.pi*u/2)
            x=.002+rx*math.sin(a)
            y=.076-ry*math.cos(a)
            band.append(cap.vertex((x,y,z)))
        if bands:
            for k in range(sides):
                nxt=(k+1)%sides
                cap.quad(bands[-1][k],bands[-1][nxt],band[nxt],band[k])
        bands.append(band)
    tip=cap.vertex((.002,.076,.157))
    for k in range(sides):
        cap.face(bands[-1][k],bands[-1][(k+1)%sides],tip)
    # The front hair has a photographic surface texture on a real dome, not
    # a row of hard tube-spikes. Side locks remain independently sculpted.
    for side in (-1,1):
        # Ear stays visible; sideburn and back-of-head hair taper to collar.
        tube(locks,[(side*.074,.018,.079),(side*.093,.029,.044),
                    (side*.089,.040,-.023),(side*.085,.063,-.073)],
             [.005,.008,.007,.002],8)
        for j in range(5):
            x=side*(.065+j*.006)
            tube(flyaways,[(x,.024,.060),(x+side*.006,.050,.035),
                           (x+side*.009,.075,.003)], [.0005,.0023,.0003],6)
    # Split by face orientation, so the photograph-baked hair only covers the
    # actual front dome. The unphotographed back retains its own 3D material.
    def subset(keep_front: bool) -> TriMesh:
        result=TriMesh();mapping={}
        for a,b,c in cap.faces:
            f=(cap.vertices[a][1]+cap.vertices[b][1]+cap.vertices[c][1])/3 < .077
            if f!=keep_front: continue
            indices=[]
            for i in (a,b,c):
                if i not in mapping:mapping[i]=result.vertex(cap.vertices[i])
                indices.append(mapping[i])
            result.face(*indices)
        return result
    return subset(True),subset(False),locks,flyaways


def make_blazer() -> dict[str,TriMesh]:
    coat=TriMesh()
    rings=[(-.78,.143,.091),(-.73,.148,.096),(-.67,.153,.100),
           (-.60,.164,.104),(-.52,.176,.109),(-.44,.189,.113),
           (-.37,.202,.117),(-.31,.216,.122),(-.267,.220,.121),
           (-.231,.158,.100),(-.188,.057,.060)]
    prior=None
    for z,rx,ry in rings:
        band=[]
        for j in range(28):
            a=2*math.pi*j/28
            band.append(coat.vertex((rx*math.cos(a),.055+ry*math.sin(a),z)))
        if prior:
            for j in range(28):coat.quad(prior[j],prior[(j+1)%28],band[(j+1)%28],band[j])
        prior=band
    shirt=TriMesh(); lapels=TriMesh(); collar=TriMesh()
    fabric_piece(shirt,[(-.102,-.78),(.102,-.78),(.081,-.345),
                        (0,-.194),(-.081,-.345)],y=-.064)
    # Distinct three-dimensional tailored lapels, not painted over a photo.
    for side in (-1,1):
        fabric_piece(lapels,[(side*.211,-.276),(side*.115,-.266),
                             (side*.065,-.385),(side*.118,-.416)], y=-.071)
        fabric_piece(collar,[(side*.073,-.198),(side*.029,-.217),
                             (side*.075,-.280),(side*.112,-.262)],y=-.070)
    buttons=TriMesh()
    for z in (-.61,-.71):
        ellipsoid(buttons,(.045,-.062,z),(.006,.003,.006),8,12)
    return {'coat':coat,'shirt':shirt,'lapels':lapels,'collar':collar,'buttons':buttons}


def make_arms() -> dict[str,TriMesh]:
    out={}
    for side in (-1,1):
        sleeve=TriMesh(); cuff=TriMesh(); hand=TriMesh()
        tube(sleeve,[(side*.190,.045,-.285), (side*.222,.016,-.45),
                     (side*.206,-.005,-.635), (side*.187,-.010,-.720)],
             [.056,.061,.047,.036],16)
        tube(cuff,[(side*.19,-.011,-.708),(side*.188,-.013,-.748)], [.038,.037],16)
        ellipsoid(hand,(side*.188,-.013,-.772),(.026,.023,.048),12,16)
        out[f'sleeve_{side}']=sleeve
        out[f'cuff_{side}']=cuff
        out[f'hand_{side}']=hand
    return out


def make_cables() -> TriMesh:
    cable=TriMesh()
    for side in (-1,1):
        for j in range(3):
            off=j*.062
            tube(cable,[(side*(.14+off),.43,-.42),
                        (side*(.20+off),.54,-.18),
                        (side*(.29+off),.71,-.07),
                        (side*(.33+off),1.10,-.12)],
                 [.011,.011,.009,.008],10)
    return cable


def build(output: Path) -> dict[str,dict[str,int]]:
    output.mkdir(parents=True,exist_ok=True)
    assets={'sphere':make_sphere(),'skin':make_skin(),'cables':make_cables()}
    hair=make_hair()
    assets.update(dict(zip(('hair_front','hair_back','hair_locks','hair_strands'),hair)))
    assets.update(make_blazer());assets.update(make_arms())
    import json
    manifest=json.loads((output/'model_manifest.json').read_text())
    crop=manifest['source_crop'];scale=manifest['metric_metres_per_pixel']
    uvs=[tuple(float(v) for v in line.split()[1:3]) for line in
         (output/'monarch_face_v5.obj').read_text().splitlines() if line.startswith('vt ')]
    if len(uvs)!=468:raise ValueError('Fit the face mesh before sculpting hair')
    mid=(uvs[33][0]+uvs[263][0])/2
    bridge=uvs[168][1]
    def project_hair(x:float,y:float,z:float) -> tuple[float,float]:
        return max(0.,min(1.,mid+x/((crop[2]-crop[0])*scale))),max(0.,min(1.,bridge+z/((crop[3]-crop[1])*scale)))
    result={}
    for name,mesh in assets.items():
        mesh.save(output/f'{name}.obj',uv_project=project_hair if name=='hair_front' else None)
        result[name]={'vertices':len(mesh.vertices),'triangles':len(mesh.faces)}
    return result


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    import json
    print(json.dumps(build(args.output),indent=2))


if __name__=='__main__':main()
