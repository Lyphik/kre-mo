"""Exporte le scénario final minuté (Markdown) depuis la source unique script/ep01.json + timeline."""
import json

from config import BUILD, PROJECT, SCRIPT

SCENE_LABEL = {
    "cold_open": "Ouverture — plan grue sur la Place des Palmistes", "logo": "Logo 3D 973 CULTURE",
    "name_reveal": "Révélation animée du nom LYPHIK", "stat": "Compteur animé (chiffre vérifié)",
    "map": "Carte animée de la Guyane", "quote": "Citation (biographie officielle)", "pml": "Typographie P·M·L",
    "timeline": "Frise chronologique animée", "clip_slot": "Emplacement d'extrait de clip (sous autorisation)",
    "cards": "Pochettes typographiques animées", "ep": "EP FA7 — liste des titres", "network": "Graphe des collaborations",
    "press": "Coupure de presse animée", "persona": "Écran partagé personnage / personne", "factcheck": "Fact-check",
    "badlife": "Mise en scène BAD LIFE", "paradox": "Le paradoxe (vues vs auditeurs)", "playlist": "Playlist découverte",
    "cta": "Appel à l'action", "end_logo": "Logo de fin + mentions", "disclaimer": "Plan à deux + carton transparence",
    "single": "Gros plan sur l'orateur", "two_shot": "Plan à deux", "set_wide": "Plan large du plateau",
}
SEQ_TITLE = {0: "Séquence 0 — Accroche (cold open)", 1: "Séquence 1 — Introduction", 2: "Séquence 2 — Qui est Lyphik ?",
             3: "Séquence 3 — Les clips et l'univers musical", 4: "Séquence 4 — Featurings et collaborations",
             5: "Séquence 5 — L'humain derrière l'artiste", 6: "Séquence 6 — BAD LIFE et l'actualité",
             7: "Séquence 7 — Conclusion et appel à l'action"}


def mmss(t):
    m, s = divmod(t, 60)
    return f"{int(m)}:{s:04.1f}"


def main():
    script = json.loads(SCRIPT.read_text(encoding="utf-8"))
    tl = json.loads((BUILD / "timeline.json").read_text(encoding="utf-8"))
    ep = script["episode"]
    out = [f"# Scénario final — {ep['show']}", "",
           f"**Épisode {ep['id'][2:]} : {ep['title']}**  ", f"Version {ep['version']} · durée réelle : **{mmss(tl['duration'])}** · "
           f"{sum(1 for b in tl['beats'] if b['type'] == 'line')} répliques", "",
           "> Source unique : `production/script/ep01.json` (ce document est généré par `production/src/export_script.py`).",
           "> Les personnages KENZO et MAËVA sont fictifs. Chaque fait cité renvoie au dossier `docs/01-recherche/dossier-lyphik.md`.", "",
           "## Personnages", "", "| Code | Personnage | Rôle éditorial |", "|---|---|---|",
           "| K | **Kenzo** | Passionné de rap, direct, drôle, provoque gentiment le débat |",
           "| M | **Maëva** | Fine observatrice, avis tranché, recadre et relance |", ""]
    seq = None
    for b in tl["beats"]:
        if b["seq"] != seq:
            seq = b["seq"]
            out += ["", f"## {SEQ_TITLE[seq]}", "", "| TC | Qui | Dialogue | Image |", "|---|---|---|---|"]
        scene = SCENE_LABEL.get(b.get("scene"), b.get("scene"))
        if b.get("data", {}).get("slot"):
            scene += f" — **{b['data']['slot']}**"
        if b["type"] == "visual":
            out.append(f"| {mmss(b['start'])} | — | *(musique)* | {scene} |")
        else:
            who = "**KENZO**" if b["who"] == "K" else "**MAËVA**"
            emo = f" *({b['emotion']})*" if b.get("emotion") else ""
            out.append(f"| {mmss(b['start'])} | {who} | {b['text']}{emo} | {scene} |")
    out += ["", "## Lexique de prononciation (synthèse vocale)", "",
            "Affichage → prononciation. Les prononciations marquées ⚠ sont des hypothèses à valider avec l'artiste.", "",
            "| Affiché | Prononcé |", "|---|---|"]
    doubtful = {"1K 5K", "Kyenn Cho", "Allnice", "Rawniii", "Manhimselff", "Three7", "Jahsik", "Lyphik", "LYPHIK"}
    for k, v in script["pronunciation"].items():
        out.append(f"| {k} | {v}{' ⚠' if k in doubtful else ''} |")
    path = PROJECT / "docs" / "02-scenario" / "scenario-ep01.md"
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    print("scénario :", path)


if __name__ == "__main__":
    main()
