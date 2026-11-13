"""Sous-titres du prototype : SRT (16:9, fichier séparé) + ASS stylé (vertical, incrusté)."""
import json
import os

D = os.path.dirname(os.path.abspath(__file__))
tl = json.load(open(os.path.join(D, "timing.json"), encoding="utf-8"))
KEY = {"Cinq cent quatre-vingt-quinze mille": "595 000", "Lyphik": "Lyphik", "Pa mélé": "Pa mélé"}


def tc_srt(t):
    h, r = divmod(t, 3600)
    m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s % 1) * 1000)):03d}"


def tc_ass(t):
    m, s = divmod(t, 60)
    return f"0:{int(m):02d}:{s:05.2f}"


srt, ass_ev = [], []
for i, l in enumerate(tl, 1):
    a, e = l["t0"], l["t1"] + 0.15
    if i < len(tl):
        e = min(e, tl[i]["t0"] - 0.02) if tl[i]["t0"] > a + 0.6 else e
    txt = l["text"]
    srt.append(f"{i}\n{tc_srt(a)} --> {tc_srt(e)}\n{txt}\n")
    styled = txt
    for k in ("Lyphik", "Pa mélé", "Cinq cent quatre-vingt-quinze mille vues"):
        styled = styled.replace(k, "{\\c&H3BBFF9&}" + k + "{\\c&HFFFFFF&}")
    who = "KENZO" if l["who"] == "K" else "MAËVA"
    col = "&H354D08&" if l["who"] == "K" else "&H3434D9&"
    ass_ev.append(f"Dialogue: 0,{tc_ass(a)},{tc_ass(e)},Sub,,0,0,0,,{{\\fad(80,80)}}{{\\c{col}\\fs34}}{who}\\N{{\\c&HFFFFFF&\\fs58}}{styled}")

open(os.path.join(D, "proto10s_fr.srt"), "w", encoding="utf-8").write("\n".join(srt))
ass = """[Script Info]
ScriptType: v4.00+
PlayResX: 720
PlayResY: 1280
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Inter Display,58,&H00FFFFFF,&H00FFFFFF,&H00101010,&H90000000,-1,0,0,0,100,100,0,0,1,4,2,2,50,50,250,1
Style: Brand,Inter Display,30,&H003BBFF9,&H00FFFFFF,&H00101010,&H80000000,-1,0,0,0,100,100,3,0,1,3,0,8,40,40,70,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:00:10.00,Brand,,0,0,0,,973 CULTURE{\\c&HFFFFFF&} · LE PODCAST
""" + "\n".join(ass_ev) + "\n"
open(os.path.join(D, "proto10s_vertical.ass"), "w", encoding="utf-8").write(ass)
print("ok", len(srt))
