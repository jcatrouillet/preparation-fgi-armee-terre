#!/usr/bin/env python3
"""Integre les fiches et les questions des 3 livres (orange, vert, kaki) dans index.html.

Lit livres.json et remplace le bloc LIVRES de index.html (entre les marqueurs
/*LIVRES:BEGIN*/ et /*LIVRES:END*/). Les marqueurs sont crees au premier
lancement, juste avant le bloc STATE.

Usage :  python build_livres.py
Aucune dependance externe.
"""
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
BEGIN, END = "/*LIVRES:BEGIN*/", "/*LIVRES:END*/"
ANCHOR = "/* ---------- STATE ---------- */"


def main():
    data = json.load(open(os.path.join(BASE, "livres.json"), encoding="utf-8"))
    ids = {b["id"] for b in data["livres"]}
    for q in data["questions"]:
        if q["l"] not in ids:
            sys.exit("Livre inconnu dans une question : %r" % q["l"])
        if len(q["d"]) != 4 or len({q["a"], *q["d"]}) != 5:
            sys.exit("Question invalide (4 distracteurs distincts attendus) : %s" % q["q"])

    block = "%s\nconst LIVRES = %s;\n%s" % (
        BEGIN, json.dumps(data, ensure_ascii=False, separators=(",", ":")), END)

    index = os.path.join(BASE, "index.html")
    html = open(index, encoding="utf-8").read()
    if BEGIN in html:
        a, b = html.index(BEGIN), html.index(END) + len(END)
        html = html[:a] + block + html[b:]
    else:
        assert ANCHOR in html, "ancre STATE introuvable dans index.html"
        html = html.replace(ANCHOR, block + "\n\n" + ANCHOR, 1)
    open(index, "w", encoding="utf-8").write(html)

    par = {}
    for q in data["questions"]:
        par[q["l"]] = par.get(q["l"], 0) + 1
    print("%d livres, %d questions %s, index.html = %.0f Ko"
          % (len(data["livres"]), len(data["questions"]), par, os.path.getsize(index) / 1024))


if __name__ == "__main__":
    main()
