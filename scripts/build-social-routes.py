#!/usr/bin/env python3
"""Create HTML social cards for pretty album URLs on GitHub Pages.

GitHub Pages responds with HTTP 404 to unknown SPA routes. Social apps
don't execute JavaScript redirects; they need a real 200 HTML page.
The real album is still displayed by the existing SPA after loading.
"""
from __future__ import annotations

import html
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "scripts" / "gallery-source-manifest.json"
IMAGE = "https://lucasabrahamph.com/social-preview-la.png?v=106"
MARKER = "<!-- GENERATED SOCIAL ROUTE; scripts/build-social-routes.py -->"
RESERVED = {
    "inicio", "galeria", "admin", "club", "album", "assets", "docs",
    "tests", "scripts", "cloudflare", "contrataciones", "como-comprar",
    "como-pedir", "index", "404", "checkout", "compras",
}


def ascii_text(value: str) -> str:
    plain = unicodedata.normalize("NFD", str(value or "")).lower()
    return "".join(ch for ch in plain if unicodedata.category(ch) != "Mn")


def token(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", ascii_text(value))


TEAM_CODES = {
    "allboys":"ALB", "unionmalvinas":"MAL", "malvinas":"MAL",
    "unionflorida":"UFL", "unionsanvicente":"USV", "usv":"USV",
    "caleracentral":"CAL", "defensorescentralcordoba":"DCC",
    "defensoresjuveniles":"DJU", "centralcordoba":"CCO",
    "atleticocarlospaz":"ACP", "elcarmen":"CAR",
    "dief":"DIE", "medea":"MED", "cibi":"CIB",
    "deportivoalberdi":"DAL", "villasiburu":"VSI",
    "barrioparque":"BPA", "parquevelez":"PVE",
    "lasallano":"LAS", "racing":"RAC", "talleres":"TAL",
    "sanlorenzo":"SLO", "comercial":"COM", "universitario":"UNI",
}


def team_code(value: str) -> str:
    text=ascii_text(value).strip()
    key=token(text)
    if key in TEAM_CODES:
        return TEAM_CODES[key]
    words=[w for w in re.sub(r"[^a-z0-9]+"," ",text).split()
           if w not in {"club","de","del","la","las","los","el","fc","ca"}]
    if not words:
        return "EQP"
    code=(words[0][:3] if len(words)==1 else
          words[0][:2]+words[1][:1] if len(words)==2 else
          "".join(w[0] for w in words[:3]))
    return code.upper().ljust(3,"X")[:3]


def album_slug(name: str) -> str:
    title=str(name or "").split(":")[0].strip()
    parts=[part.strip() for part in re.split(
        r"\s+(?:vs\.?|versus|contra)\s+|\s+[-–—]\s+", title, flags=re.I) if part.strip()]
    while len(parts)>2 and ascii_text(parts[-1]) in {
        "primera","reserva","cebollitas","festejos","escuelita",
        "galeria","participando","cuarta","quinta","sexta",
        "septima","octava","inferiores",
    }:
        parts.pop()
    if len(parts)==2:
        return team_code(parts[0])+team_code(parts[1])
    return team_code(title)


def category_segment(value: str) -> str:
    words=re.sub(r"[^a-z0-9]+"," ",ascii_text(value)).split()
    labels={
        "primera":"Primera", "reserva":"Reserva",
        "cebollitas":"Cebollitas", "escuelita":"Escuelita",
        "festejos":"Festejos", "cuarta":"Cuarta", "4ta":"Cuarta",
        "4to":"Cuarta", "quinta":"Quinta", "5ta":"Quinta",
        "5to":"Quinta", "sexta":"Sexta", "6ta":"Sexta",
        "6to":"Sexta", "septima":"Septima", "7ma":"Septima",
        "octava":"Octava", "8va":"Octava",
        "inferiores":"Inferiores", "participando":"Participando",
        "galeria":"Galeria",
    }
    return "-".join(labels.get(w,w.capitalize()) for w in words) or "Galeria"


def category(value: str) -> str:
    text = token(value)
    if "primera" in text:
        return "primera"
    if "reserva" in text:
        return "reserva"
    if "cebollitas" in text:
        return "cebollitas"
    return text or "categoria"


def priority(value: str):
    return {"primera": 1, "reserva": 2, "cebollitas": 3}.get(category(value), 99)


def split_album(sheet_name: str):
    parts = sheet_name.split(":")
    if len(parts) > 1:
        return parts[0].strip(), ":".join(parts[1:]).strip()
    match = re.match(r"^(.+?)\s[-–—]\s(Escuelita|Participando)$", sheet_name, re.I)
    if match:
        return match.group(1).strip(), "Escuelita"
    return sheet_name.strip(), "Galería"


def page(slug: str, title: str, subtitle: str):
    canonical = f"https://lucasabrahamph.com/{slug}"
    text_title = html.escape(f"{title} · {subtitle} | lucasabraham.ph", quote=True)
    description = html.escape(
        f"Fotos de {title} · {subtitle}. Mirá la galería en lucasabraham.ph.",
        quote=True
    )
    return f'''<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <base href="/">
  <title>{text_title}</title>
  <meta name="description" content="{description}">
  <link rel="canonical" href="{canonical}">
  <meta property="og:locale" content="es_AR">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="lucasabraham.ph">
  <meta property="og:title" content="{text_title}">
  <meta property="og:description" content="{description}">
  <meta property="og:url" content="{canonical}">
  <meta property="og:image" content="{IMAGE}">
  <meta property="og:image:secure_url" content="{IMAGE}">
  <meta property="og:image:type" content="image/png">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="lucasabraham.ph - Fotografía deportiva">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{text_title}">
  <meta name="twitter:description" content="{description}">
  <meta name="twitter:image" content="{IMAGE}">
  <style>html,body{{min-height:100%;margin:0;background:#050505;color:#fff;font-family:-apple-system,BlinkMacSystemFont,Arial,sans-serif}}main{{max-width:480px;margin:18vh auto;padding:24px;text-align:center}}a{{color:#7dd3fc}}</style>
</head>
<body>
  {MARKER}
  <main id="status"><h1>lucasabraham.ph</h1><p>Abriendo galería...</p></main>
  <script>
  (async function () {{
    try {{
      const response = await fetch('/index.html', {{ cache: 'no-cache' }});
      if (!response.ok) throw new Error('No se pudo abrir la galería');
      let site = await response.text();
      site = site.replace(/<head([^>]*)>/i, '<head$1><base href="/">');
      document.open();
      document.write(site);
      document.close();
    }} catch (e) {{
      document.getElementById('status').innerHTML =
        '<h1>No se pudo abrir la galería</h1><p><a href="/">Volver al inicio</a></p>';
    }}
  }})();
  </script>
</body>
</html>
'''


def build():
    sheets = json.loads(MANIFEST.read_text(encoding="utf-8"))
    albums = defaultdict(dict)
    for sheet in sheets:
        name = str(sheet.get("name") or "").strip()
        if not name:
            continue
        base, sub = split_album(name)
        albums[base][category(sub)] = sub

    slugs = set(RESERVED)
    written = skipped = 0
    for base in sorted(albums, key=lambda value: (album_slug(value), value)):
        seed = album_slug(base)
        primary = seed
        number = 2
        while primary in slugs:
            primary = f"{seed}-{number}"
            number += 1
        slugs.add(primary)
        subs = sorted(albums[base].values(), key=lambda sub: (priority(sub), ascii_text(sub)))
        for index, sub in enumerate(subs):
            category_name = category_segment(sub)
            slug = f"{primary}/{category_name}"
            number = 2
            candidate = slug
            while slug.lower() in {x.lower() for x in slugs}:
                slug = f"{candidate}{number}"
                number += 1
            slugs.add(slug)
            # The short base URL opens Primera (or the first existing
            # category); explicit /Primera and /Cebollitas also work.
            for address in ([primary, slug] if index == 0 else [slug]):
                target = ROOT / address / "index.html"
                if target.exists() and MARKER not in target.read_text(encoding="utf-8"):
                    skipped += 1  # Preserve explicitly authored pages.
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                content = page(address, base, sub)
                if not target.exists() or target.read_text(encoding="utf-8") != content:
                    target.write_text(content, encoding="utf-8")
                    written += 1
    print(f"Social album pages updated: {written}; existing custom pages: {skipped}")


if __name__ == "__main__":
    build()
