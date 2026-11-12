"""Configuration centrale du pipeline 973 CULTURE.

Toutes les constantes de production (formats, chemins, palette) sont définies ici
pour garantir la cohérence entre le master, les Shorts et la miniature.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]          # 973-culture/production
PROJECT = ROOT.parent                                 # 973-culture
SCRIPT = ROOT / "script" / "ep01.json"
BUILD = ROOT / "build"                                # artefacts intermédiaires (non versionnés)
CACHE = ROOT / ".cache"                               # modèles de voix (non versionnés)
VOICES_DIR = CACHE / "voices"
DELIVER = PROJECT / "deliverables" / "ep01"

FPS = 25
W, H = 1920, 1080
SR = 48000                                            # fréquence audio du master

# Palette officielle (voir docs/06-branding/branding-chaine.md)
PALETTE = {
    "night":   (0.039, 0.063, 0.071),   # #0A1012 noir profond
    "green":   (0.031, 0.302, 0.208),   # #084D35 vert forêt
    "green2":  (0.090, 0.478, 0.329),   # #177A54 vert feuille
    "gold":    (0.976, 0.749, 0.231),   # #F9BF3B jaune doré
    "red":     (0.851, 0.204, 0.204),   # #D93434 rouge
    "white":   (0.973, 0.965, 0.941),   # #F8F6F0 blanc cassé
    "blue":    (0.180, 0.553, 1.000),   # #2E8DFF bleu électrique
    "ink":     (0.071, 0.098, 0.110),   # #12191C
}

VOICE_URLS = {
    "fr_FR-tom-medium": "fr/fr_FR/tom/medium/fr_FR-tom-medium",
    "fr_FR-siwis-medium": "fr/fr_FR/siwis/medium/fr_FR-siwis-medium",
}
VOICE_BASE = "https://huggingface.co/rhasspy/piper-voices/resolve/main/"

FONT_DISPLAY = "Inter Display"
FONT_TEXT = "Inter"
FONT_MONO = "JetBrains Mono"
