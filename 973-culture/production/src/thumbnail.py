"""Miniature YouTube 1280×720 (rendu 1920×1080 puis réduction).

N'utilise aucune photo ni pochette de l'artiste (droits) : présentateurs expressifs +
typographie. Accroche factuelle (chiffre vérifié et sourcé dans l'épisode).
"""
import cairo

import characters as ch
import setdesign as sd
from compositor import apply_cam, draw_background
from config import DELIVER, H, W
from draw import P, lin, rrect, set_src, text, text_width


def draw(ctx):
    tod = 0.55
    cam = (1050, 455, 1.9)
    draw_background(ctx, cam, tod, 3.0, 3)
    ctx.save()
    apply_cam(ctx, cam, 1.0)
    sd.draw_stage(ctx, tod, 3.0)
    for who in ("K", "M"):
        st = ch.default_state()
        if who == "K":
            st.update(open=0.85, shape="round", brow=1.0, yaw=0.35, gaze_x=-0.2, smile=0.3, arm_r=0.0, arm_l=0.9, arm_phase=0.4)
        else:
            st.update(open=0.55, shape="wide", brow=0.6, yaw=-0.25, gaze_x=-0.5, smile=0.95, arm_r=1.0, arm_phase=2.3)
        ctx.save()
        ctx.translate(1180 if who == "K" else 1395, sd.SEAT_Y)
        ctx.scale(sd.CHAR_SCALE, sd.CHAR_SCALE)
        ch.draw_character(ctx, who, st, 3.0)
        ctx.restore()
    ctx.restore()
    # voile gauche pour la lisibilité du texte
    ctx.rectangle(0, 0, W, H)
    ctx.set_source(lin(0, 0, W, 0, [(0, (0.02, 0.05, 0.05, 0.96)), (0.42, (0.02, 0.05, 0.05, 0.8)), (0.56, (0, 0, 0, 0))]))
    ctx.fill()
    # badge épisode
    rrect(ctx, 70, 64, 250, 64, 10)
    set_src(ctx, P("red"))
    ctx.fill()
    text(ctx, "973 · ÉP. 01", 195, 110, 34, P("white"), "black", "center")
    # titre
    text(ctx, "QUI EST", 74, 290, 96, P("gold"), "black")
    for dx, dy in ((6, 8),):
        text(ctx, "LYPHIK ?", 70 + dx, 470 + dy, 210, (0, 0, 0, 0.6), "black")
    text(ctx, "LYPHIK ?", 70, 470, 210, P("white"), "black")
    ctx.rectangle(76, 505, 760, 12)
    set_src(ctx, P("gold"))
    ctx.fill()
    # accroche chiffrée
    rrect(ctx, 70, 560, 800, 120, 14)
    set_src(ctx, P("blue"))
    ctx.fill()
    text(ctx, "+1,6 M DE VUES", 100, 645, 76, P("white"), "black")
    text(ctx, "LE RAP GUYANAIS À DÉCOUVRIR", 74, 760, 46, P("white"), "black", tracking=0.02)
    # liseré tricolore discret
    for i, c in enumerate(("green2", "gold", "red")):
        ctx.rectangle(0, H - 18 + i * 6, W, 6)
        set_src(ctx, P(c))
        ctx.fill()


def main():
    DELIVER.mkdir(parents=True, exist_ok=True)
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(s)
    draw(ctx)
    big = DELIVER / "thumbnail_1920x1080.png"
    s.write_to_png(str(big))
    import subprocess
    subprocess.run(["convert", str(big), "-resize", "1280x720", "-strip", "-quality", "92",
                    str(DELIVER / "973culture_ep01_miniature_1280x720.jpg")], check=True)
    big.unlink()
    print("miniature :", DELIVER / "973culture_ep01_miniature_1280x720.jpg")


if __name__ == "__main__":
    main()
