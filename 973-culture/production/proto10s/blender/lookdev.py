"""Rendu de test (lookdev) des personnages : blender -b chars.blend --python lookdev.py -- out.png samples"""
import math
import sys
import time

import bpy
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:]
OUT, SAMPLES = args[0], int(args[1])
sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = SAMPLES
sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
sc.render.film_transparent = False
sc.view_settings.view_transform = "AgX"
sc.view_settings.look = "AgX - Medium High Contrast"

world = bpy.data.worlds.new("w")
sc.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs[0].default_value = (0.25, 0.32, 0.45, 1)
bg.inputs[1].default_value = 0.6


def light(name, kind, loc, energy, color, size=1.0):
    ld = bpy.data.lights.new(name, kind)
    ld.energy = energy
    ld.color = color
    if kind == "AREA":
        ld.size = size
    ob = bpy.data.objects.new(name, ld)
    sc.collection.objects.link(ob)
    ob.location = loc
    d = Vector((0, 0, 1.3)) - Vector(loc)
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    return ob


light("key", "AREA", (-1.8, -2.2, 2.2), 260, (1.0, 0.78, 0.55), 1.2)
light("fill", "AREA", (2.0, -2.0, 1.6), 60, (0.7, 0.8, 1.0), 2.0)
light("rim", "AREA", (0.5, 2.0, 2.4), 220, (0.55, 0.7, 1.0), 0.8)
cam_d = bpy.data.cameras.new("cam")
cam_d.lens = 50
cam = bpy.data.objects.new("cam", cam_d)
sc.collection.objects.link(cam)
cam.location = (0, -2.6, 1.55)
cam.rotation_euler = (math.radians(88), 0, 0)
sc.camera = cam
t = time.time()
sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("RENDER_TIME", round(time.time() - t, 1))
