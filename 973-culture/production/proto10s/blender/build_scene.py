"""Prototype 10 s — scène 3D : décor, personnages, lumière, caméras, animation.

Usage : blender -b chars.blend --python build_scene.py -- <proto10s_dir> <sortie.blend> [vertical]
Toutes les animations sont générées depuis timing.json (dialogue) et mouth.json (bouche).
"""
import json
import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Euler, Quaternion, Vector

ARGS = sys.argv[sys.argv.index("--") + 1:]
PDIR, OUT = ARGS[0], ARGS[1]
VERTICAL = len(ARGS) > 2 and ARGS[2] == "vertical"
FPS, DUR = 25, 10.0
NF = int(FPS * DUR)
TIMING = json.load(open(os.path.join(PDIR, "timing.json")))
MOUTH = json.load(open(os.path.join(PDIR, "mouth.json")))
rnd = random.Random(973)
sc = bpy.context.scene
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, NF


def F(t):
    return 1 + int(round(t * FPS))


def mat(name, color, rough=0.6, metal=0.0, emit=None, emit_strength=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = emit_strength
    return m


def wood_mat():
    """Bois de teck patiné : veinage étiré le long des lames (coordonnées objet) + joints de lames."""
    m = bpy.data.materials.new("bois")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (0.35, 14.0, 14.0)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 6.0
    nz.inputs["Detail"].default_value = 8.0
    nz.inputs["Distortion"].default_value = 2.5
    nt.links.new(mp.outputs[0], nz.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.055, 0.035, 0.022, 1)
    ramp.color_ramp.elements[1].color = (0.20, 0.125, 0.07, 1)
    nt.links.new(nz.outputs["Fac"], ramp.inputs[0])
    # joints de lames tous les 12 cm (sur la hauteur des contremarches et la profondeur des assises)
    mp2 = nt.nodes.new("ShaderNodeMapping")
    nt.links.new(tc.outputs["Object"], mp2.inputs["Vector"])
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.wave_type = "BANDS"
    wave.bands_direction = "Z"
    wave.inputs["Scale"].default_value = 2.6
    wave.wave_profile = "SAW"
    nt.links.new(mp2.outputs[0], wave.inputs["Vector"])
    seam = nt.nodes.new("ShaderNodeMath")
    seam.operation = "GREATER_THAN"
    seam.inputs[1].default_value = 0.96
    nt.links.new(wave.outputs["Fac"], seam.inputs[0])
    mixc = nt.nodes.new("ShaderNodeMix")
    mixc.data_type = "RGBA"
    nt.links.new(seam.outputs[0], mixc.inputs[0])
    nt.links.new(ramp.outputs[0], mixc.inputs[6])
    mixc.inputs[7].default_value = (0.02, 0.012, 0.008, 1)
    nt.links.new(mixc.outputs[2], b.inputs["Base Color"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.25
    nt.links.new(nz.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs[0], b.inputs["Normal"])
    b.inputs["Roughness"].default_value = 0.5
    return m


def box(name, loc, size, material, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    o.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(material)
    return o


# ------------------------------------------------------------------ personnages : assise sur les gradins
SEAT_Z = 0.46            # dessus de la marche d'assise
STEP_D = 0.55
deps = bpy.context.evaluated_depsgraph_get()


def body_bounds(name):
    ob = bpy.data.objects[name + "_body"].evaluated_get(deps)
    me = ob.to_mesh()
    mw = ob.matrix_world
    zs = [(mw @ v.co) for v in me.vertices]
    ob.to_mesh_clear()
    return zs


PLACE = {"KENZO": (-0.66, 0.0, 22.0), "MAEVA": (0.62, 0.0, -24.0)}
for name, (x, y, yaw) in PLACE.items():
    rig = bpy.data.objects[name + "_rig"]
    rig.location = (0, 0, 0)
    bpy.context.view_layer.update()
    deps = bpy.context.evaluated_depsgraph_get()
    hip = rig.matrix_world @ rig.pose.bones["pelvis.L"].head
    # contact d'assise : ≈ 10 cm sous l'articulation de la hanche (anatomie adulte assise)
    bottom = hip.z - 0.10
    back_y = hip.y + 0.12
    rig.location = (x, y - back_y + 0.12, SEAT_Z - bottom + 0.005)
    rig.rotation_euler = (0, 0, math.radians(yaw))
    rig["seat_info"] = [bottom, back_y]
bpy.context.view_layer.update()

# ------------------------------------------------------------------ gradins (plateau éphémère)
wood = wood_mat()
metal = mat("metal_noir", (0.03, 0.03, 0.035), 0.35, 0.9)
for i, (z, y) in enumerate([(SEAT_Z - 0.42, -0.62), (SEAT_Z, -0.07), (SEAT_Z + 0.42, 0.48), (SEAT_Z + 0.84, 1.03)]):
    box(f"marche{i}", (0, y, z / 2), (4.6, STEP_D, max(z, 0.04)), wood)
    box(f"nez{i}", (0, y - STEP_D / 2 + 0.02, z - 0.012), (4.62, 0.05, 0.03), wood)
    # LED sous le nez de marche
    led = box(f"led{i}", (0, y - STEP_D / 2 - 0.01, max(0.02, z - 0.05)), (4.5, 0.01, 0.012),
              mat(f"led_m{i}", (1, 0.7, 0.3), emit=(1.0, 0.66, 0.32), emit_strength=2.0))
# coussins
for name, col in (("KENZO", (0.85, 0.62, 0.12)), ("MAEVA", (0.05, 0.32, 0.20))):
    x = PLACE[name][0]
    bpy.ops.mesh.primitive_cube_add(location=(x, -0.07, SEAT_Z + 0.03))
    c = bpy.context.active_object
    c.scale = (0.25, 0.22, 0.035)
    bpy.ops.object.transform_apply(scale=True)
    c.modifiers.new("b", "BEVEL").width = 0.03
    c.modifiers[-1].segments = 4
    c.data.materials.append(mat("coussin_" + name, col, 0.9))

# ------------------------------------------------------------------ micros sur bras articulés
mic_m = mat("micro", (0.05, 0.05, 0.055), 0.4, 0.6)
gold = mat("bague_or", (0.95, 0.68, 0.22), 0.25, 1.0)
for name in PLACE:
    rig = bpy.data.objects[name + "_rig"]
    head = rig.matrix_world @ rig.pose.bones["head"].head
    fwd = (rig.matrix_world.to_3x3() @ Vector((0, -1, 0))).normalized()
    side = -1 if name == "KENZO" else 1
    mpos = head + fwd * 0.24 + Vector((0, 0, -0.20)) + Vector((side * 0.06, 0, 0))
    # micro dynamique : corps + grille, orienté vers la bouche
    aim = (head + Vector((0, 0, -0.08)) - mpos).normalized()
    bpy.ops.mesh.primitive_cylinder_add(radius=0.024, depth=0.13, location=mpos - aim * 0.05)
    body_m = bpy.context.active_object
    body_m.rotation_euler = aim.to_track_quat("Z", "Y").to_euler()
    body_m.data.materials.append(mic_m)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.03, location=mpos + aim * 0.03)
    grille = bpy.context.active_object
    grille.scale = (1, 1, 1.25)
    grille.rotation_euler = body_m.rotation_euler
    grille.data.materials.append(mat("grille", (0.12, 0.12, 0.13), 0.55, 0.8))
    bpy.ops.mesh.primitive_cylinder_add(radius=0.026, depth=0.012, location=mpos - aim * 0.01)
    ring = bpy.context.active_object
    ring.rotation_euler = body_m.rotation_euler
    ring.data.materials.append(gold)
    # pied : tige verticale depuis la marche inférieure + perche courte
    foot = Vector((mpos.x + side * 0.05, mpos.y - 0.10, SEAT_Z - 0.42))
    top = Vector((foot.x, foot.y, mpos.z - 0.12))
    for a_, b_ in ((foot, top), (top, mpos - aim * 0.11)):
        d = b_ - a_
        bpy.ops.mesh.primitive_cylinder_add(radius=0.009, depth=d.length, location=(a_ + b_) / 2)
        cyl = bpy.context.active_object
        cyl.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
        cyl.data.materials.append(metal)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.11, depth=0.015, location=foot)
    bpy.context.active_object.data.materials.append(metal)

# ------------------------------------------------------------------ sol, allée
ground = mat("pelouse", (0.10, 0.20, 0.06), 0.95)
bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 40, 0))
bpy.context.active_object.data.materials.append(ground)
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 12, 0.005))
path = bpy.context.active_object
path.scale = (6, 30, 1)
path.data.materials.append(mat("allee", (0.45, 0.38, 0.30), 0.9))

# ------------------------------------------------------------------ palmiers royaux (palmistes)
trunk_m = mat("tronc", (0.48, 0.45, 0.40), 0.85)
_tn = trunk_m.node_tree
_w = _tn.nodes.new("ShaderNodeTexWave")
_w.bands_direction = "Z"
_w.inputs["Scale"].default_value = 1.2
_bp = _tn.nodes.new("ShaderNodeBump")
_bp.inputs["Strength"].default_value = 0.4
_tn.links.new(_w.outputs["Fac"], _bp.inputs["Height"])
_tn.links.new(_bp.outputs[0], _tn.nodes["Principled BSDF"].inputs["Normal"])
shaft_m = mat("manchon", (0.18, 0.32, 0.12), 0.7)
leaf_m = mat("palme", (0.08, 0.20, 0.05), 0.6)
leaf_m.node_tree.nodes["Principled BSDF"].inputs["Subsurface Weight"].default_value = 0.15


def make_palm_mesh():
    """Couronne de palmier royal : palmes arquées, folioles fines (pennées) de part et d'autre du rachis."""
    bm = bmesh.new()
    n_fronds = 16
    for f in range(n_fronds):
        az = f / n_fronds * 2 * math.pi + rnd.uniform(-0.12, 0.12)
        L = rnd.uniform(3.0, 4.0)
        lift = rnd.uniform(0.6, 1.3)
        segs = 22
        pts = []
        for s_ in range(segs + 1):
            u = s_ / segs
            r = L * u
            z = lift * math.sin(u * math.pi * 0.5) * 1.1 - (1.9 - lift) * u ** 2.0 * 1.4
            pts.append(Vector((math.cos(az) * r, math.sin(az) * r, z)))
        perp = Vector((-math.sin(az), math.cos(az), 0))
        for i in range(1, segs):
            u = i / segs
            c = pts[i]
            ll = (0.75 * math.sin(math.pi * min(1.0, u * 1.1)) + 0.08)
            fw = (pts[i + 1] - pts[i - 1]).normalized()
            for sg in (-1, 1):
                tip = c + perp * sg * ll + Vector((0, 0, -0.35 * ll)) + fw * 0.18
                w = 0.035
                v1 = bm.verts.new(c - fw * w)
                v2 = bm.verts.new(c + fw * w)
                v3 = bm.verts.new(tip)
                bm.faces.new((v1, v2, v3))
        for i in range(segs):
            a1 = bm.verts.new(pts[i] + Vector((0, 0, 0.02)))
            a2 = bm.verts.new(pts[i + 1] + Vector((0, 0, 0.02)))
            a3 = bm.verts.new(pts[i + 1] - Vector((0, 0, 0.02)))
            bm.faces.new((a1, a2, a3))
    me = bpy.data.meshes.new("palme_mesh")
    bm.to_mesh(me)
    bm.free()
    return me


PALM_MESHES = [make_palm_mesh() for _ in range(4)]
palm_objs = []


def palm(x, y, h):
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.22, depth=h, location=(x, y, h / 2))
    t = bpy.context.active_object
    t.data.materials.append(trunk_m)
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.24, depth=1.6, location=(x, y, h + 0.8))
    bpy.context.active_object.data.materials.append(shaft_m)
    crown = bpy.data.objects.new("couronne", rnd.choice(PALM_MESHES))
    crown.data.materials.append(leaf_m) if not crown.data.materials else None
    sc.collection.objects.link(crown)
    crown.location = (x, y, h + 1.6)
    crown.rotation_euler = (0, 0, rnd.uniform(0, 6.28))
    palm_objs.append(crown)


for x_, y_, h_ in ((-3.9, 5.5, 3.6), (3.4, 6.2, 4.0), (-1.4, 8.5, 4.8), (5.2, 9.0, 5.6), (-6.0, 8.0, 5.2), (1.2, 11.0, 6.0)):
    palm(x_, y_, h_)
for y, n, spread in ((11.5, 8, 22), (16, 10, 28), (24, 12, 40)):
    for i in range(n):
        x = -spread / 2 + (i + 0.5) * spread / n + rnd.uniform(-0.8, 0.8)
        if y < 7 and abs(x) < 1.6:
            continue
        palm(x, y + rnd.uniform(-1, 1), rnd.uniform(9.5, 13.5))

# ------------------------------------------------------------------ façades créoles de Cayenne
FACADES = [(0.93, 0.78, 0.45), (0.85, 0.52, 0.36), (0.62, 0.76, 0.64), (0.92, 0.88, 0.80), (0.50, 0.65, 0.80),
           (0.90, 0.66, 0.62), (0.95, 0.85, 0.63)]
roof_m = mat("toit", (0.42, 0.16, 0.10), 0.7, 0.3)
shutter_m = mat("persiennes", (0.12, 0.35, 0.28), 0.6)
x = -40.0
while x < 40:
    w = rnd.uniform(7, 11)
    floors = rnd.choice([2, 2, 3])
    h = floors * 3.3 + 0.6
    y0 = 34 + rnd.uniform(-1.5, 1.5)
    col = rnd.choice(FACADES)
    box("facade", (x + w / 2, y0, h / 2), (w, 8, h), mat("facade", col, 0.85))
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=w * 0.75, depth=2.2, location=(x + w / 2, y0, h + 1.1),
                                    rotation=(0, 0, math.pi / 4))
    roof = bpy.context.active_object
    roof.scale = (1.0, 8 / w, 1)
    roof.data.materials.append(roof_m)
    # balcon filant
    box("balcon", (x + w / 2, y0 - 4.4, 3.4), (w, 0.8, 0.12), mat("balcon", (0.25, 0.18, 0.12), 0.7))
    for f in range(floors):
        nwin = int(w / 2.2)
        for k in range(nwin):
            wx = x + 1.1 + k * (w - 2.2) / max(1, nwin - 1)
            lit = rnd.random() < 0.6
            box("fenetre", (wx, y0 - 4.02, 1.4 + f * 3.3), (0.9, 0.05, 1.6),
                mat("vitre", (0.05, 0.04, 0.03), 0.2, emit=(1.0, 0.72, 0.38) if lit else None,
                    emit_strength=rnd.uniform(1.5, 4) if lit else 0))
            for s in (-1, 1):
                box("volet", (wx + s * 0.6, y0 - 4.05, 1.4 + f * 3.3), (0.28, 0.05, 1.7), shutter_m)
    x += w + rnd.uniform(0.2, 1.5)
# évocation lointaine du monument (portique)
stone = mat("pierre", (0.80, 0.77, 0.70), 0.8)
box("portique", (-9, 22, 2.5), (6, 1.2, 5), stone)
box("statue", (-9, 21.3, 2.4), (0.7, 0.6, 2.6), mat("bronze", (0.22, 0.24, 0.20), 0.5, 0.7))

# ------------------------------------------------------------------ guirlande guinguette + enseigne néon
bulb_m = mat("ampoule", (1, 0.85, 0.6), emit=(1.0, 0.70, 0.38), emit_strength=14.0)
for row in range(3):
    zA, sag = 2.7 + row * 0.3, 0.45
    yA = 2.8 + row * 1.5
    for i in range(30):
        u = i / 29
        bx = -3.6 + 7.2 * u
        bz = zA - sag * 4 * u * (1 - u)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.045, location=(bx, yA, bz), segments=12, ring_count=8)
        bpy.context.active_object.data.materials.append(bulb_m)
    for s in (-1, 1):
        box("poteau", (s * 3.6, yA, zA / 2), (0.08, 0.08, zA), metal)
bpy.ops.object.text_add(location=(0, 1.95, 2.42), rotation=(math.radians(90), 0, 0))
neon = bpy.context.active_object
neon.data.body = "973 CULTURE"
neon.data.align_x = "CENTER"
neon.data.size = 0.32
neon.data.extrude = 0.015
try:
    neon.data.font = bpy.data.fonts.load("/usr/share/fonts/opentype/inter/InterDisplay-Black.otf")
except Exception:
    pass
neon.data.materials.append(mat("neon", (1, 0.75, 0.2), emit=(1.0, 0.70, 0.18), emit_strength=18.0))
box("panneau", (0, 2.0, 2.50), (2.5, 0.06, 0.58), mat("panneau", (0.02, 0.03, 0.03), 0.6))
# plantes : héliconias stylisées en pot
pot_m = mat("pot", (0.85, 0.82, 0.76), 0.6)
for px in (-2.0, 2.0):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.22, depth=0.5, location=(px, -0.5, SEAT_Z + 0.25))
    bpy.context.active_object.data.materials.append(pot_m)
    for k in range(9):
        bpy.ops.mesh.primitive_plane_add(size=1, location=(px, -0.5, SEAT_Z + 0.95))
        lf = bpy.context.active_object
        lf.scale = (0.18, 0.7, 1)
        lf.rotation_euler = (rnd.uniform(0.2, 0.7), 0, k / 9 * 6.28)
        lf.data.materials.append(leaf_m)

# ------------------------------------------------------------------ lumière : fin de journée + éclairage de plateau
world = bpy.data.worlds.new("ciel")
sc.world = world
world.use_nodes = True
nt = world.node_tree
sky = nt.nodes.new("ShaderNodeTexSky")
sky.sky_type = "NISHITA"
sky.sun_elevation = math.radians(6.0)
sky.sun_rotation = math.radians(150)
sky.air_density = 1.0
sky.dust_density = 1.0
nt.links.new(sky.outputs[0], nt.nodes["Background"].inputs[0])
nt.nodes["Background"].inputs[1].default_value = 0.22


def light(name, kind, loc, target, energy, color, size=1.0, spot=None):
    ld = bpy.data.lights.new(name, kind)
    ld.energy = energy
    ld.color = color
    if kind == "AREA":
        ld.size = size
        ld.shape = "DISK"
    if kind == "SPOT" and spot:
        ld.spot_size = spot
        ld.spot_blend = 0.6
    ob = bpy.data.objects.new(name, ld)
    sc.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return ob


sunl = light("soleil", "SUN", (10, 25, 6), (0, 0, 1), 1.4, (1.0, 0.70, 0.48))
sunl.data.angle = math.radians(2)
light("cle_softbox", "AREA", (-1.6, -2.6, 2.3), (0, 0, 1.2), 170, (1.0, 0.93, 0.86), 1.6)
light("contre_froid", "AREA", (1.2, 2.2, 2.6), (0, 0, 1.2), 160, (0.55, 0.70, 1.0), 1.0)
light("debouchage", "AREA", (2.2, -2.4, 1.2), (0, 0, 1.1), 45, (0.85, 0.85, 1.0), 2.5)
light("guirlande_rebond", "AREA", (0, 0.8, 3.0), (0, 0, 1.0), 70, (1.0, 0.65, 0.35), 3.0)

# ------------------------------------------------------------------ animation des personnages
INFO = {}
for name in PLACE:
    rig = bpy.data.objects[name + "_rig"]
    body = bpy.data.objects[name + "_body"]
    assert all(pb.rotation_mode == "QUATERNION" for pb in rig.pose.bones), "pose non convertie"
    INFO[name] = {"rig": rig, "body": body, "base": {pb.name: pb.rotation_quaternion.copy() for pb in rig.pose.bones}}

KEYS = {}


def key_shape(name, sk, frame, value):
    kb = INFO[name]["body"].data.shape_keys.key_blocks.get(sk)
    if kb is None:
        return
    kb.value = max(0.0, min(1.0, value))
    kb.keyframe_insert("value", frame=frame)


def key_bone(name, bone, frame, euler_deg):
    pb = INFO[name]["rig"].pose.bones[bone]
    d = Euler([math.radians(a) for a in euler_deg], "XYZ").to_quaternion()
    pb.rotation_quaternion = INFO[name]["base"][bone] @ d
    pb.keyframe_insert("rotation_quaternion", frame=frame)


def smooth(t, a, b):
    if b <= a:
        return 1.0 if t >= b else 0.0
    u = max(0.0, min(1.0, (t - a) / (b - a)))
    return u * u * (3 - 2 * u)


def noise(t, s):
    return math.sin(t * 1.3 + s) * 0.5 + math.sin(t * 2.7 + s * 1.7) * 0.3 + math.sin(t * 5.1 + s * 2.3) * 0.2


LINES = {l["id"]: l for l in TIMING}
K_SPEAK = [(l["t0"], l["t1"]) for l in TIMING if l["who"] == "K"]
M_SPEAK = [(l["t0"], l["t1"]) for l in TIMING if l["who"] == "M"]
P1, P2, P3, P4 = LINES["P1"], LINES["P2"], LINES["P3"], LINES["P4"]
VIS = {"open": "viseme_aa", "wide": "viseme_E", "round": "viseme_O", "closed": "viseme_PP", "fv": "viseme_FF",
       "neutral": "viseme_nn"}
CAM_POS = {}

# blinks
BLINKS = {"KENZO": [0.9, 3.4, 5.1, 7.0, 9.3], "MAEVA": [1.3, 2.0, 4.6, 6.6, 8.9]}
for f in range(1, NF + 1):
    t = (f - 1) / FPS
    for name, code in (("KENZO", "K"), ("MAEVA", "M")):
        mo = MOUTH[code]
        idx = min(len(mo["open"]) - 1, f - 1)
        op, shp = mo["open"][idx], mo["shape"][idx]
        # bouche : visème principal + mâchoire (léger lissage de l'ouverture)
        for vk in set(VIS.values()):
            key_shape(name, vk, f, (op * 0.85 if VIS.get(shp) == vk else 0.0))
        key_shape(name, "jawOpen", f, op * 0.35)
        # clignements
        bl = 0.0
        for b in BLINKS[name]:
            if 0 <= t - b < 0.16:
                bl = 1 - abs((t - b) - 0.08) / 0.08
        key_shape(name, "eyeBlinkLeft", f, bl)
        key_shape(name, "eyeBlinkRight", f, bl)
        # expressions selon l'action
        laugh = smooth(t, P4["t0"] - 0.05, P4["t0"] + 0.35) * (1 - smooth(t, 9.6, 10.0) * 0.3)
        if name == "KENZO":
            excited = smooth(t, 0.2, 0.6) * (1 - smooth(t, 2.0, 2.6))
            proud = smooth(t, P3["t0"], P3["t0"] + 0.4)
            surprise_react = smooth(t, 2.6, 3.0) * (1 - smooth(t, 4.6, 5.2))   # réagit à Maëva
            smile = max(0.35 * excited + 0.25, 0.55 * proud, 0.95 * laugh, 0.30 + 0.25 * surprise_react)
            brow = 0.6 * excited + 0.35 * surprise_react + 0.2 * proud
            squint = 0.7 * laugh
        else:
            surprised = smooth(t, P2["t0"] - 0.15, P2["t0"] + 0.2) * (1 - smooth(t, 4.2, 5.0))
            listening = smooth(t, 0.4, 1.0) * (1 - smooth(t, P2["t0"] - 0.3, P2["t0"]))
            amused = smooth(t, P3["t0"] + 0.6, P3["t1"])
            smile = max(0.25 + 0.2 * listening, 0.15 * surprised + 0.2, 0.6 * amused, 1.0 * laugh)
            brow = 0.9 * surprised + 0.25 * listening + 0.2 * amused
            squint = 0.75 * laugh
            key_shape(name, "eyeWideLeft", f, 0.5 * surprised)
            key_shape(name, "eyeWideRight", f, 0.5 * surprised)
        key_shape(name, "mouthSmileLeft", f, smile * (1 - op * 0.4))
        key_shape(name, "mouthSmileRight", f, smile * (1 - op * 0.4) * 0.92)
        key_shape(name, "browInnerUp", f, brow * 0.8)
        key_shape(name, "browOuterUpLeft", f, brow * 0.6)
        key_shape(name, "browOuterUpRight", f, brow * 0.5)
        key_shape(name, "cheekSquintLeft", f, squint)
        key_shape(name, "cheekSquintRight", f, squint)
        key_shape(name, "eyeSquintLeft", f, squint * 0.6)
        key_shape(name, "eyeSquintRight", f, squint * 0.6)
        if laugh > 0.05:
            key_shape(name, "jawOpen", f, max(op * 0.35, 0.18 * laugh + 0.06 * abs(math.sin(t * 14))))

    # ---------------- corps : tête, regard, gestes (deltas par rapport à la pose assise)
    for name in PLACE:
        s = 0 if name == "KENZO" else 2.0
        toward = 1 if name == "KENZO" else -1        # vers le partenaire (yaw)
        laugh = smooth(t, P4["t0"] - 0.05, P4["t0"] + 0.3)
        if name == "KENZO":
            look_partner = 0.85 * (1 - smooth(t, 0.3, 0.8)) + 0.9 * smooth(t, 2.1, 2.5) * (1 - smooth(t, P3["t0"] + 0.5, P3["t0"] + 1.0)) \
                + 0.9 * laugh
            to_cam = smooth(t, P3["t0"] + 0.6, P3["t0"] + 1.1) * (1 - laugh)
            nod = 3.0 * math.sin(t * 9) * (smooth(t, 0.4, 0.7) * (1 - smooth(t, 1.8, 2.1)))
            nod += 4.0 * math.sin((t - P3["t0"]) * 6) * smooth(t, P3["t0"], P3["t0"] + 0.2) * (1 - smooth(t, P3["t0"] + 0.8, P3["t0"] + 1.1))
        else:
            look_partner = 0.95 * (1 - smooth(t, P2["t0"] + 1.6, P2["t0"] + 2.0)) + 0.9 * smooth(t, P2["t1"] - 0.4, P2["t1"]) \
                - 0.0
            look_partner = min(1.0, look_partner + laugh)
            to_cam = smooth(t, P2["t0"] + 1.6, P2["t0"] + 2.0) * (1 - smooth(t, P2["t1"] - 0.4, P2["t1"]))
            nod = 3.5 * math.sin(t * 7) * smooth(t, 0.6, 0.9) * (1 - smooth(t, 1.7, 2.0))
            nod += 2.5 * math.sin((t - P3["t0"]) * 5) * smooth(t, P3["t0"] + 0.3, P3["t0"] + 0.6) * (1 - smooth(t, P3["t1"], P3["t1"] + 0.3))
        # axes vérifiés par mesure : Y+ tourne la tête vers +x ; le corps est déjà orienté de ±22-24° vers le partenaire
        yaw = toward * 38 * look_partner + noise(t * 0.6, s) * 2.5
        if to_cam > 0:
            yaw = yaw * (1 - to_cam) + (-toward * 20) * to_cam   # se tourne vers la caméra
        pitch = nod + noise(t * 0.5, s + 1) * 1.5 - 4 * laugh * abs(math.sin(t * 7)) - 2 * laugh + 3   # léger regard vers le bas au repos
        roll = noise(t * 0.4, s + 2) * 1.8 - toward * 3 * look_partner
        key_bone(name, "neck02", f, (pitch * 0.4, yaw * 0.4, roll * 0.4))
        key_bone(name, "head", f, (pitch * 0.6, yaw * 0.6, roll * 0.6))
        # yeux (os orientés vers l'avant) : Z+ déplace le regard vers -x ; ils anticipent la tête
        ey = toward * 16 * look_partner - toward * 8 * to_cam + noise(t * 1.7, s) * 1.2
        key_bone(name, "eye.L", f, (0, 0, -ey))
        key_bone(name, "eye.R", f, (0, 0, -ey))
        # respiration + rire (épaules)
        br = math.sin(t * 2 * math.pi / 3.6 + s) * 1.2
        lean_in = 0.0
        if name == "MAEVA":
            lean_in = 6 * smooth(t, P2["t0"] - 0.1, P2["t0"] + 0.4) * (1 - smooth(t, 4.8, 5.4))
        else:
            lean_in = 4 * smooth(t, 0.2, 0.5) * (1 - smooth(t, 1.9, 2.3))
        bounce = 3.5 * laugh * abs(math.sin(t * 12))
        key_bone(name, "spine03", f, (br * 0.5 + lean_in * 0.6 + bounce * 0.4, 0, -toward * 2 * lean_in / 6))
        key_bone(name, "spine01", f, (lean_in * 0.4 + bounce * 0.3, 0, 0))
        # gestes
        if name == "KENZO":
            g1 = smooth(t, 0.35, 0.75) * (1 - smooth(t, 1.9, 2.4))            # « cinq cent quatre-vingt-quinze mille »
            g2 = smooth(t, P3["t0"] + 0.5, P3["t0"] + 0.9) * (1 - smooth(t, P3["t1"] + 0.2, P3["t1"] + 0.7))  # « ça, c'est Lyphik »
            beat = math.sin(t * 7) * 6 * g1
            key_bone(name, "upperarm01.R", f, (0, 0, 14 * g1 + 10 * g2))
            key_bone(name, "lowerarm01.R", f, (0, 0, 38 * g1 + 32 * g2 + beat))
            key_bone(name, "lowerarm01.L", f, (0, 0, -12 * laugh))
        else:
            g1 = smooth(t, P2["t0"] + 0.1, P2["t0"] + 0.5) * (1 - smooth(t, P2["t1"] - 0.4, P2["t1"] + 0.2))  # « attends… »
            beat = math.sin(t * 5.5) * 5 * g1
            key_bone(name, "upperarm01.L", f, (0, 0, -10 * g1))
            key_bone(name, "lowerarm01.L", f, (0, 0, -42 * g1 - beat))
            key_bone(name, "lowerarm01.R", f, (0, 0, 22 * laugh))

# ------------------------------------------------------------------ caméras (découpage)
def head_pos(name):
    rig = INFO[name]["rig"]
    return rig.matrix_world @ rig.pose.bones["head"].head


sc.frame_set(1)
HK, HM = head_pos("KENZO") + Vector((0, 0, 0.08)), head_pos("MAEVA") + Vector((0, 0, 0.08))
MID = (HK + HM) / 2


def camera(name, loc, target, lens, focus, fstop=2.0):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_width = 36
    cd.dof.use_dof = True
    cd.dof.aperture_fstop = fstop
    cd.dof.focus_distance = (Vector(focus) - Vector(loc)).length
    co = bpy.data.objects.new(name, cd)
    sc.collection.objects.link(co)
    co.location = loc
    co.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return co


if not VERTICAL:
    sc.render.resolution_x, sc.render.resolution_y = 1280, 720
    camA = camera("A_plan_a_deux", MID + Vector((-0.6, -3.0, -0.45)), MID + Vector((0.05, 0, 0.05)), 35, MID, 2.0)
    camB = camera("B_contrechamp_Maeva", HM + Vector((-0.75, -1.35, -0.10)), HM + Vector((0.02, 0, -0.02)), 70, HM, 1.8)
    camC = camera("C_Kenzo", HK + Vector((0.70, -1.35, -0.10)), HK + Vector((-0.02, 0, -0.02)), 70, HK, 1.8)
    camD = camera("D_large_rire", MID + Vector((0.55, -3.5, -0.50)), MID + Vector((0, 0.5, 0.15)), 30, MID, 2.4)
else:
    sc.render.resolution_x, sc.render.resolution_y = 720, 1280
    camA = camera("A_plan_a_deux", MID + Vector((-1.7, -2.0, -0.55)), MID + Vector((0.15, 0, -0.08)), 26, MID, 2.4)
    camB = camera("B_contrechamp_Maeva", HM + Vector((-0.75, -1.35, -0.10)), HM + Vector((0.02, 0, -0.12)), 50, HM, 1.8)
    camC = camera("C_Kenzo", HK + Vector((0.70, -1.35, -0.10)), HK + Vector((-0.02, 0, -0.12)), 50, HK, 1.8)
    camD = camera("D_large_rire", MID + Vector((1.6, -2.0, -0.55)), MID + Vector((-0.15, 0, -0.05)), 26, MID, 2.6)
# lents mouvements de caméra (poussées)
for co, f0, f1, push in ((camA, 1, F(2.0), 0.25), (camB, F(2.0), F(5.35), 0.12), (camC, F(5.35), F(7.85), 0.12),
                         (camD, F(7.85), NF, 0.45)):
    fwd = co.matrix_world.to_3x3() @ Vector((0, 0, -1))
    start = co.location.copy()
    co.location = start
    co.keyframe_insert("location", frame=f0)
    co.location = start + fwd * push
    co.keyframe_insert("location", frame=f1)
    co.data.dof.keyframe_insert("focus_distance", frame=f0)
    co.data.dof.focus_distance -= push
    co.data.dof.keyframe_insert("focus_distance", frame=f1)
# coupes : marqueurs liés aux caméras
for co, t in ((camA, 0.0), (camB, 2.0), (camC, 5.35), (camD, 7.85)):
    m = sc.timeline_markers.new(co.name, frame=F(t))
    m.camera = co
sc.camera = camA

# ------------------------------------------------------------------ rendu
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = 20
sc.cycles.adaptive_threshold = 0.05
sc.cycles.use_denoising = True
sc.cycles.denoiser = "OPENIMAGEDENOISE"
sc.cycles.max_bounces = 4
sc.cycles.diffuse_bounces = 2
sc.cycles.glossy_bounces = 2
sc.cycles.transparent_max_bounces = 16
sc.cycles.caustics_reflective = False
sc.cycles.caustics_refractive = False
sc.render.use_persistent_data = True
sc.view_settings.view_transform = "AgX"
sc.view_settings.look = "AgX - Medium High Contrast"
sc.view_settings.exposure = -0.15
sc.render.image_settings.file_format = "PNG"
# brume atmosphérique en post (passe mist) + légère vignette
vl = sc.view_layers[0]
vl.use_pass_mist = True
world.mist_settings.start = 8
world.mist_settings.depth = 60
world.mist_settings.falloff = "QUADRATIC"
sc.use_nodes = True
cn = sc.node_tree
for n in list(cn.nodes):
    cn.nodes.remove(n)
rl = cn.nodes.new("CompositorNodeRLayers")
comp = cn.nodes.new("CompositorNodeComposite")
mixn = cn.nodes.new("CompositorNodeMixRGB")
mixn.blend_type = "MIX"
haze = cn.nodes.new("CompositorNodeRGB")
haze.outputs[0].default_value = (0.78, 0.66, 0.58, 1)
mul = cn.nodes.new("CompositorNodeMath")
mul.operation = "MULTIPLY"
mul.inputs[1].default_value = 0.12
cn.links.new(rl.outputs["Mist"], mul.inputs[0])
cn.links.new(mul.outputs[0], mixn.inputs[0])
cn.links.new(rl.outputs["Image"], mixn.inputs[1])
cn.links.new(haze.outputs[0], mixn.inputs[2])
glare = cn.nodes.new("CompositorNodeGlare")
glare.glare_type = "FOG_GLOW"
glare.threshold = 1.2
glare.mix = -0.75
cn.links.new(mixn.outputs[0], glare.inputs[0])
lens = cn.nodes.new("CompositorNodeLensdist")
lens.inputs["Dispersion"].default_value = 0.008
cn.links.new(glare.outputs[0], lens.inputs[0])
cn.links.new(lens.outputs[0], comp.inputs[0])

bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SCENE_SAVED", OUT, "objets:", len(bpy.data.objects))
