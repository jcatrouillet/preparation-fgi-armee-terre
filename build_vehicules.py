#!/usr/bin/env python3
"""Integre les photos de vehicules dans index.html (page autonome).

Lit vehicules.json + Vehicules/*.jpg, reduit les images (largeur max 560 px,
JPEG q74) et remplace le bloc VEHICLES de index.html (entre les marqueurs
/*VEHICLES:BEGIN*/ et /*VEHICLES:END*/). Les marqueurs sont crees au premier
lancement.

Usage :  python build_vehicules.py
Necessite Pillow (pip install pillow) -- uniquement pour ce script de build.
"""
import base64
import io
import json
import os
import sys

from PIL import Image

BASE = os.path.dirname(os.path.abspath(__file__))
MAX_W = 560
QUALITY = 74
BEGIN, END = "/*VEHICLES:BEGIN*/", "/*VEHICLES:END*/"
ANCHOR = "/* ---------- STATE ---------- */"


def encode(path):
    im = Image.open(path).convert("RGB")
    if im.width > MAX_W:
        im = im.resize((MAX_W, round(im.height * MAX_W / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=QUALITY, optimize=True, progressive=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def main():
    meta = json.load(open(os.path.join(BASE, "vehicules.json"), encoding="utf-8"))
    items = []
    for v in meta:
        path = os.path.join(BASE, "Vehicules", v["file"])
        if not os.path.exists(path):
            sys.exit("Image manquante : " + path)
        items.append({
            "name": v["name"], "cat": v["cat"], "full": v["full"],
            "img": encode(path),
            "credit": "%s — %s" % (v["author"], v["license"]),
            "source": v["source"],
        })

    block = "%s\nconst VEHICLES = %s;\n%s" % (
        BEGIN, json.dumps(items, ensure_ascii=False), END)

    index = os.path.join(BASE, "index.html")
    html = open(index, encoding="utf-8").read()
    if BEGIN in html:
        a, b = html.index(BEGIN), html.index(END) + len(END)
        html = html[:a] + block + html[b:]
    else:
        assert ANCHOR in html, "ancre STATE introuvable dans index.html"
        html = html.replace(ANCHOR, block + "\n\n" + ANCHOR, 1)
    open(index, "w", encoding="utf-8").write(html)

    kb = sum(len(i["img"]) for i in items) / 1024
    print("%d vehicules integres (+%.0f Ko), index.html = %.0f Ko"
          % (len(items), kb, os.path.getsize(index) / 1024))


if __name__ == "__main__":
    main()
