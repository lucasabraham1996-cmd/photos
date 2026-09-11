from __future__ import annotations

from pathlib import Path
import re
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "lcf-v2"
OUT.mkdir(parents=True, exist_ok=True)

SHIELDS = {
    "all-boys": "https://i.postimg.cc/Vkvy6VmY/All-Boys.png",
    "almirante-brown": "https://i.postimg.cc/K8jXzHxR/Almirante-Brown.png",
    "amsurbac": "https://i.postimg.cc/cLCqHb0v/Amsurbac.png",
    "argentino-penarol": "https://i.postimg.cc/8zc850Ns/Argentino-Penarol.png",
    "atalaya": "https://i.postimg.cc/BnbW6V48/Atalaya.png",
    "atletico-carlos-paz": "https://i.postimg.cc/wjMKvGgN/Atletico-Carlos-Paz.png",
    "avellaneda": "https://i.postimg.cc/pLrNT6R8/Avellaneda.png",
    "banfield": "https://i.postimg.cc/jS2V5FtP/Banfield.png",
    "barrio-parque": "https://i.postimg.cc/rws6mPMC/Barrio-Parque.png",
    "belgrano": "https://i.postimg.cc/RZhrFD4R/Belgrano.png",
    "bella-vista": "https://i.postimg.cc/HknGxhdz/Bella-Vista.png",
    "calera-central": "https://i.postimg.cc/dV3M1xw4/Calera-Central.png",
    "camioneros": "https://i.postimg.cc/K8H6gD8n/Cambioneros.png",
    "cibi": "https://i.postimg.cc/T34zWJ3J/CIBI.png",
    "club-coronel-olmedo": "https://i.postimg.cc/Jz2fB5zq/Club-Coronel-Olmedo.png",
    "defensores-central-cordoba": "https://i.postimg.cc/bwB729wL/Defensores-Central-Cordoba.png",
    "deportivo-alberdi": "https://i.postimg.cc/kgp0tvgf/Deportivo-Alberdi.png",
    "deportivo-defensores-juveniles": "https://i.postimg.cc/Njz3rkjn/Deportivo-Defensores-Junveniles.png",
    "deportivo-norte": "https://i.postimg.cc/7ZWFTnZc/Deportivo-Norte.png",
    "dief": "https://i.postimg.cc/mg5vFyrf/DIEF.png",
    "el-carmen": "https://i.postimg.cc/W1HBJw4c/El-Carmen.png",
    "escuela-presidente-roca": "https://i.postimg.cc/SxvBzfKq/Escuela-Presidente-Roca.png",
    "general-paz-junior": "https://i.postimg.cc/jjnG6nD1/General-Paz-Junior.png",
    "huracan": "https://i.postimg.cc/VN0390JT/Huracan.png",
    "independiente": "https://i.postimg.cc/VN0390Jp/Independiente.png",
    "instituto": "https://i.postimg.cc/N02W82K3/Instituto.png",
    "juvenil-barrio-comercial": "https://i.postimg.cc/q769c6tf/Juvenil-Barrio-Comercial.png",
    "la-union-malvinas": "https://i.postimg.cc/Zqv1Pv9z/La-Union-Malvinas.png",
    "las-flores": "https://i.postimg.cc/Zqv1Pv9m/Las-Flores.png",
    "las-palmas": "https://i.postimg.cc/0NKLGK6P/Las-Palmas.png",
    "lasallano": "https://i.postimg.cc/d0ZzRZ7q/Lasallano.png",
    "libertad": "https://i.postimg.cc/25LPdLqk/Libertad.png",
    "lobos-del-sur": "https://i.postimg.cc/CKnWCnZx/Lobos-del-Sur.png",
    "los-andes": "https://i.postimg.cc/W4qQmqD4/Los-Andes.png",
    "medea": "https://i.postimg.cc/5tQZ5QHy/Medea.png",
    "quilmes": "https://i.postimg.cc/Lsgrkgqh/Quilmes.png",
    "racing": "https://i.postimg.cc/Lsgrkgqg/Racing.png",
    "rancagua": "https://i.postimg.cc/QMKRgKBT/Rancagua.png",
    "recreativo-municipalidad": "https://i.postimg.cc/LsgrkgqZ/Recreativo-Municipalidad.png",
    "san-lorenzo": "https://i.postimg.cc/76vjKP7Z/San-Lorenzo.png",
    "san-nicolas": "https://i.postimg.cc/3RMztrpw/San-Nicolas.png",
    "talleres": "https://i.postimg.cc/G206X3YH/Talleres.png",
    "union-florida": "https://i.postimg.cc/cHqPF1Yv/Union-Florida.png",
    "union-san-vicente": "https://i.postimg.cc/3RMztrp0/Union-San-Vicente.png",
    "union-serrana": "https://i.postimg.cc/26pg0jvW/Union-Serrana.png",
    "universitario": "https://i.postimg.cc/76vjKP77/Universitario.png",
    "valores": "https://i.postimg.cc/sXFbTfS7/Valores.png",
    "villa-azalaiz": "https://i.postimg.cc/hjFN24xV/Villa-Azalaiz.png",
    "villa-siburu": "https://i.postimg.cc/j5VBMqNH/Villa-Siburu.png",
}


def download(url: str) -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; lucasabraham.ph shield mirror/1.0)",
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            "Referer": "https://postimages.org/",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read()
    if len(data) < 100:
        raise RuntimeError(f"Respuesta demasiado pequeña: {url} ({len(data)} bytes)")
    # PNG, JPEG or WEBP are acceptable even if the URL ends in .png.
    if not (data.startswith(b"\x89PNG\r\n\x1a\n") or data.startswith(b"\xff\xd8\xff") or data.startswith(b"RIFF")):
        raise RuntimeError(f"La URL no devolvió una imagen válida: {url}; cabecera={data[:16]!r}")
    return data


print(f"Mirroring {len(SHIELDS)} team shields...")
failures = []
for slug, url in SHIELDS.items():
    try:
        data = download(url)
        target = OUT / f"{slug}.png"
        target.write_bytes(data)
        print(f"OK {slug}: {len(data)} bytes")
    except Exception as exc:
        failures.append((slug, url, str(exc)))
        print(f"ERROR {slug}: {exc}")

if failures:
    details = "\n".join(f"- {slug}: {url} -> {err}" for slug, url, err in failures)
    raise SystemExit(f"No se pudieron espejar {len(failures)} escudos:\n{details}")

# Replace runtime Postimg URLs with local, same-origin assets in both apps.
for rel in ("contrataciones.html", "index.html"):
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    original = text
    for slug, url in SHIELDS.items():
        text = text.replace(url, f"assets/lcf-v2/{slug}.png?v=108")
    if rel == "contrataciones.html":
        text = text.replace("/* v107: lista LCF actualizada con 49 escudos APP */", "/* v108: 49 escudos APP servidos localmente para evitar fallos de hotlink */")
    if text != original:
        path.write_text(text, encoding="utf-8")
        print(f"Updated {rel} to local shield assets")
    else:
        print(f"No URL replacements needed in {rel}")

# Hard verification: no supplied Postimg shield URL should remain in runtime files.
for rel in ("contrataciones.html", "index.html"):
    text = (ROOT / rel).read_text(encoding="utf-8")
    remaining = [url for url in SHIELDS.values() if url in text]
    if remaining:
        raise SystemExit(f"Quedaron URLs Postimg sin reemplazar en {rel}: {remaining}")

print("All shield files and runtime references validated.")
