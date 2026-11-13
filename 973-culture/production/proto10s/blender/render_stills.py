"""Images de contrôle : blender -b scene.blend --python render_stills.py -- outdir pct samples f1 f2 ..."""
import sys, time, bpy
a = sys.argv[sys.argv.index("--") + 1:]
out, pct, spp, frames = a[0], int(a[1]), int(a[2]), [int(x) for x in a[3:]]
sc = bpy.context.scene
sc.render.resolution_percentage = pct
sc.cycles.samples = spp
for f in frames:
    sc.frame_set(f)
    t = time.time()
    sc.render.filepath = f"{out}/f{f:04d}.png"
    bpy.ops.render.render(write_still=True)
    print("STILL", f, round(time.time() - t, 1), "s")
