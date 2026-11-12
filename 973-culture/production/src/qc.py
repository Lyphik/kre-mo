"""Étape 9 — Contrôle qualité automatisé des livrables (sortie : build/qc_report.json + résumé console)."""
import json
import re
import subprocess

from config import BUILD, DELIVER


def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "format=duration,size,bit_rate:stream=codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels",
                        "-of", "json", str(path)], capture_output=True, text=True)
    return json.loads(r.stdout)


def loudness(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path), "-af", "ebur128=peak=true", "-vn", "-f", "null", "-"],
                       capture_output=True, text=True)
    s = r.stderr[r.stderr.rfind("Summary:"):]
    i = re.search(r"I:\s+(-?[\d.]+) LUFS", s)
    tp = re.search(r"Peak:\s+(-?[\d.]+) dBFS", s)
    return float(i.group(1)) if i else None, float(tp.group(1)) if tp else None


def detect(path, vf, key):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path), "-vf", vf, "-an", "-f", "null", "-"],
                       capture_output=True, text=True)
    return re.findall(key + r": ([\d.]+)", r.stderr)


def srt_check(path):
    t = path.read_text(encoding="utf-8")
    ts = re.findall(r"(\d\d):(\d\d):(\d\d),(\d{3}) --> (\d\d):(\d\d):(\d\d),(\d{3})", t)
    f = lambda h, m, s, ms: int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000
    v = [(f(*x[:4]), f(*x[4:])) for x in ts]
    lines = [ln for blk in t.strip().split("\n\n") for ln in blk.split("\n")[2:]]
    return {"cues": len(v), "overlaps": sum(1 for a, b in zip(v, v[1:]) if a[1] > b[0]),
            "invalid": sum(1 for a, b in v if b <= a), "max_line": max(len(x) for x in lines) if lines else 0,
            "max_dur": round(max(b - a for a, b in v), 2) if v else 0}


def main():
    rep = {}
    vids = sorted(DELIVER.glob("*.mp4")) + sorted((DELIVER / "shorts").glob("*.mp4"))
    for p in vids:
        info = probe(p)
        v = [s for s in info["streams"] if s["codec_type"] == "video"][0]
        a = [s for s in info["streams"] if s["codec_type"] == "audio"]
        I, TP = loudness(p)
        freezes = detect(p, "freezedetect=n=0.002:d=2.5", "freeze_duration")
        blacks = detect(p, "blackdetect=d=0.3:pix_th=0.08", "black_duration")
        rep[p.name] = {
            "duration_s": round(float(info["format"]["duration"]), 2), "size_mb": round(int(info["format"]["size"]) / 1e6, 1),
            "video": f"{v['codec_name']} {v['width']}x{v['height']} @ {v['r_frame_rate']}",
            "audio": f"{a[0]['codec_name']} {a[0]['sample_rate']} Hz {a[0]['channels']} ch" if a else None,
            "loudness_lufs": I, "true_peak_dbfs": TP,
            "freezes_over_2_5s": [round(float(x), 2) for x in freezes], "black_segments": [round(float(x), 2) for x in blacks],
        }
        srt = p.with_suffix(".srt")
        if srt.exists():
            rep[p.name]["srt"] = srt_check(srt)
        print(p.name, json.dumps(rep[p.name], ensure_ascii=False))
    main_srt = DELIVER / "973culture_ep01_lyphik_fr.srt"
    rep["master_srt"] = srt_check(main_srt)
    print("SRT master", rep["master_srt"])
    (BUILD / "qc_report.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
