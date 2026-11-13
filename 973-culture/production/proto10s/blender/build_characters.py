"""Construit Kenzo et Maëva en 3D avec MPFB (actifs MakeHuman CC0) et sauvegarde un .blend.

Usage : blender -b --python build_characters.py -- <sortie.blend>
"""
import os
import sys

import bpy

import bl_ext.user_default.mpfb as mpfb  # noqa: F401  (assure l'enregistrement)
from bl_ext.user_default.mpfb.services.humanservice import HumanService
from bl_ext.user_default.mpfb.services.targetservice import TargetService
from bl_ext.user_default.mpfb.services.locationservice import LocationService
from bl_ext.user_default.mpfb.services.animationservice import AnimationService

_A = sys.argv[sys.argv.index("--") + 1:]
OUT = _A[0]
K_HAIR = _A[1] if len(_A) > 1 else "short01"
DATA = LocationService.get_user_data()


def p(*parts):
    return os.path.join(DATA, *parts)


CHARS = {
    "KENZO": {
        "macro": {"gender": 1.0, "age": 0.58, "muscle": 0.62, "weight": 0.52, "proportions": 0.7, "height": 0.55,
                  "cupsize": 0.5, "firmness": 0.5, "race": {"african": 0.9, "caucasian": 0.08, "asian": 0.02}},
        "skin": p("skins", "young_african_male", "young_african_male.mhmat"),
        "hair": p("hair", K_HAIR, K_HAIR + ".mhclo"),
        "hair_tint": (0.035, 0.028, 0.025),
        "pose": p("poses", "callharvey3d_sittingnatural", "callharvey3d_sittingnatural.bvh"),
        "tints": {"male_casualsuit05": (0.30, 0.62, 0.45)},
        "eyebrows": p("eyebrows", "eyebrow001", "eyebrow001.mhclo"),
        "eyelashes": p("eyelashes", "eyelashes02", "eyelashes02.mhclo"),
        "clothes": [p("clothes", "male_casualsuit05", "male_casualsuit05.mhclo"),
                    p("clothes", "shoes05", "shoes05.mhclo")],
        "x": -0.42,
    },
    "MAEVA": {
        "macro": {"gender": 0.0, "age": 0.5, "muscle": 0.5, "weight": 0.48, "proportions": 0.75, "height": 0.5,
                  "cupsize": 0.55, "firmness": 0.6, "race": {"african": 0.5, "caucasian": 0.45, "asian": 0.05}},
        "skin": p("skins", "young_african_female", "young_african_female.mhmat"),
        "hair": p("hair", "punkduck_alpha7_curly", "punkduck_alpha7_curly.mhclo"),
        "hair_tint": (0.55, 0.30, 0.17),
        "pose": p("poses", "callharvey3d_sittinglegscrossed", "callharvey3d_sittinglegscrossed.bvh"),
        "tints": {"female_elegantsuit01": (1.0, 0.42, 0.36)},
        "lips_from_skin": True,
        "eyebrows": p("eyebrows", "eyebrow010", "eyebrow010.mhclo"),
        "eyelashes": p("eyelashes", "eyelashes04", "eyelashes04.mhclo"),
        "clothes": [p("clothes", "female_elegantsuit01", "female_elegantsuit01.mhclo"),
                    p("clothes", "shoes06", "shoes06.mhclo")],
        "x": 0.42,
    },
}


def tint_object_materials(obj, rgb, strength=1.0):
    """Multiplie la couleur de base des matières par une teinte (recoloration sans logo)."""
    for slot in obj.material_slots:
        m = slot.material
        if not m or not m.use_nodes:
            continue
        nt = m.node_tree
        for n in nt.nodes:
            if n.type == "BSDF_PRINCIPLED" or n.type == "BSDF_HAIR_PRINCIPLED":
                sock = n.inputs.get("Base Color") or n.inputs.get("Color")
                if sock is None:
                    continue
                mix = nt.nodes.new("ShaderNodeMix")
                mix.data_type = "RGBA"
                mix.blend_type = "MULTIPLY"
                mix.inputs[0].default_value = strength
                mix.inputs[7].default_value = (*rgb, 1)
                if sock.is_linked:
                    src = sock.links[0].from_socket
                    nt.links.new(src, mix.inputs[6])
                else:
                    mix.inputs[6].default_value = sock.default_value
                nt.links.new(mix.outputs[2], sock)


def first(path_dir, ext):
    for f in sorted(os.listdir(path_dir)):
        if f.endswith(ext):
            return os.path.join(path_dir, f)
    return None


bpy.ops.wm.read_factory_settings(use_empty=True)
import addon_utils
addon_utils.enable("io_anim_bvh", default_set=True)
for name, c in CHARS.items():
    base = HumanService.create_human(macro_detail_dict=c["macro"], scale=0.1)
    base.name = name + "_body"
    HumanService.set_character_skin(c["skin"], base, skin_type="ENHANCED_SSS")
    # le squelette DOIT exister avant les accessoires : MPFB ne lie (rigging) que les assets ajoutés après
    rig = HumanService.add_builtin_rig(base, "default", import_weights=True)
    rig.name = name + "_rig"
    # yeux haute définition, dents, langue
    eyes = first(p("eyes", "high-poly"), ".mhclo")
    HumanService.add_mhclo_asset(eyes, base, asset_type="Eyes", subdiv_levels=0, material_type="MAKESKIN")
    for part, kind in (("eyebrows", "Eyebrows"), ("eyelashes", "Eyelashes")):
        HumanService.add_mhclo_asset(c[part], base, asset_type=kind, subdiv_levels=0)
    teeth = first(p("teeth", "teeth_base"), ".mhclo")
    if teeth:
        HumanService.add_mhclo_asset(teeth, base, asset_type="Teeth", subdiv_levels=0)
    HumanService.add_mhclo_asset(c["hair"], base, asset_type="Hair", subdiv_levels=0)
    for cl in c["clothes"]:
        HumanService.add_mhclo_asset(cl, base, asset_type="Clothes", subdiv_levels=1)
    # visèmes + unités faciales (ARKit) en shape keys pour l'animation du visage
    for sub in ("visemes", "faceunits"):
        d = p("targets", sub)
        for f in sorted(os.listdir(d)):
            if f.endswith(".target"):
                TargetService.load_target(base, os.path.join(d, f), weight=0.0, name=f[:-7])
    AnimationService.import_bvh_file_as_pose(rig, c["pose"])
    # conversion Euler -> quaternion SANS perte de la pose
    for pb in rig.pose.bones:
        q = pb.rotation_euler.to_quaternion() if pb.rotation_mode not in ("QUATERNION", "AXIS_ANGLE") else pb.rotation_quaternion.copy()
        pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion = q
    for ob in bpy.data.objects:
        if ob.parent == rig or ob.parent == base:
            low = ob.name.lower()
            if "hair" in low or c["hair"].split(os.sep)[-2] in low:
                tint_object_materials(ob, c["hair_tint"])
            for key, rgb in c["tints"].items():
                if key in low:
                    tint_object_materials(ob, rgb)
            ob["973_owner"] = name
    if "skin_mix" in c:   # teint (bible personnages) via les entrées du groupe de peau MPFB
        for slot in base.material_slots:
            m = slot.material
            if m and m.use_nodes:
                for n in m.node_tree.nodes:
                    if n.type == "GROUP" and "colorMixIn" in n.inputs:
                        n.inputs["colorMixIn"].default_value = (*c["skin_mix"][0], 1)
                        n.inputs["colorMixInStrength"].default_value = c["skin_mix"][1]
                        n.inputs["Brightness"].default_value = c["skin_mix"][2]
    if c.get("lips_from_skin"):   # la texture de peau contient déjà la couleur des lèvres
        body_mat = next(sl.material for sl in base.material_slots if sl.material and sl.material.name.endswith(".body"))
        for sl in base.material_slots:
            if sl.material and sl.material.name.endswith(".lips"):
                sl.material = body_mat
    rig.location.x = c["x"]
    unrigged = [o.name for o in bpy.data.objects if o.parent == base and not any(m.type == "ARMATURE" for m in o.modifiers)]
    print("OK", name, len(base.data.shape_keys.key_blocks), "assets non liés:", unrigged)

bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SAVED", OUT)
