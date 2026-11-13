"""Rendu d'animation : blender -b scene.blend --python render_anim.py -- outdir pct samples [f0 f1]"""
import sys, time, bpy
a = sys.argv[sys.argv.index("--") + 1:]
out, pct, spp = a[0], int(a[1]), int(a[2])
sc = bpy.context.scene
if len(a) > 4:
    sc.frame_start, sc.frame_end = int(a[3]), int(a[4])
sc.render.resolution_percentage = pct
sc.cycles.samples = spp
sc.render.filepath = out + "/f"
sc.render.use_overwrite = False
t = time.time()
bpy.ops.render.render(animation=True)
print("ANIM_DONE", sc.frame_start, sc.frame_end, round(time.time() - t, 1), "s")
