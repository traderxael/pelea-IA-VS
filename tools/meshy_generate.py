#!/usr/bin/env python3
"""Genera modelos 3D con la API de Meshy AI (texto -> GLB estatico).

Uso:
    export MESHY_API_KEY="..."       # bash
    python tools/meshy_generate.py             # TITAN + VOLT (preview+refine)
    python tools/meshy_generate.py --only titan
    python tools/meshy_generate.py --preview-only

IMPORTANTE (verificado en docs.meshy.ai 2026-11-07):
- La API key de Meshy REQUIERE plan de pago. En plan Free NO puedes
  crear API keys propias (la web usa una key interna del Playground).
  Free en la web: genera manual en https://www.meshy.ai y descarga el
  .glb, luego copialo a models/ o assets/models/.
- Text-to-3D es 2 pasos: preview (geometria) -> refine (textura).
  Endpoint: POST /openapi/v2/text-to-3d  (ver docs.meshy.ai/en/api/text-to-3d)
- El GLB de Meshy es MALLA ESTATICA sin rig/animacion. Para que pelee
  con Idle+Attack necesitas rigging (API de rigging de Meshy, paga) o
  usar el pipeline Blender riggeado (tools/blender_build.py, gratis).

La key NUNCA va en el repo: solo MESHY_API_KEY del entorno o .env local.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE = "https://api.meshy.ai/openapi/v2"
ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "models"

MODELS = {
    "titan": {
        "file": "titan-azul.glb",
        "prompt": (
            "Full body humanoid robot fighter character, bulky blue metallic "
            "armor with cyan glowing accents, standing in neutral fighting "
            "stance with arms slightly raised, game character model, "
            "clean topology, PBR materials, symmetrical design"
        ),
    },
    "volt": {
        "file": "volt-rojo.glb",
        "prompt": (
            "Full body humanoid robot fighter character, lean red and orange "
            "metallic armor with yellow electric energy accents, standing in "
            "neutral fighting stance with arms slightly raised, game "
            "character model, clean topology, PBR materials, symmetrical design"
        ),
    },
    "soldier": {
        "file": "soldier-verde.glb",
        "prompt": (
            "Full body military soldier game character, green tactical armor, "
            "helmet and vest, standing in neutral fighting stance with arms "
            "slightly raised, low-poly game model, clean topology"
        ),
    },
    "ninja": {
        "file": "ninja-negro.glb",
        "prompt": (
            "Full body ninja game character, black outfit with gold trim, "
            "standing in neutral fighting stance with arms slightly raised, "
            "low-poly game model, clean topology"
        ),
    },
    "brute": {
        "file": "bruto-azul.glb",
        "prompt": (
            "Full body bulky brute monster game character, blue skin with "
            "horns, standing in neutral fighting stance with arms slightly "
            "raised, low-poly game model, clean topology"
        ),
    },
    "vamp": {"file": "vampiro.glb", "prompt": "Full body vampire agent game character, pale skin, black suit with red trim, slick hair, holding blaster, standing in neutral fighting stance, low-poly game model, clean topology"},
    "ronin": {"file": "ronin.glb", "prompt": "Full body ronin samurai game character, topknot hairstyle, dark outfit with gold trim and arm plates, holding blade, standing in neutral fighting stance, low-poly game model, clean topology"},
    "rhino": {"file": "rhino-azul.glb", "prompt": "Full body blue rhino warrior game character, muscular, horn helmet, black vest with orange star, metal arm pad, standing in neutral fighting stance, low-poly game model, clean topology"},
    "panda": {"file": "panda.glb", "prompt": "Full body round panda warrior game character, striped blue and white shirt, orange scarf, holding big blaster, standing in neutral fighting stance, low-poly game model, clean topology"},
    "roja": {"file": "pelirroja.glb", "prompt": "Full body red-haired girl game character, red ponytail, green top and grey pants, holding blaster, standing in neutral fighting stance, low-poly game model, clean topology"},
    "ogro": {"file": "ogro-verde.glb", "prompt": "Full body green ogre brute game character, mohawk, red vest, big fists, standing in neutral fighting stance, low-poly game model, clean topology"},
}


def api(method: str, path: str, key: str, payload: dict | None = None):
    req = urllib.request.Request(
        BASE + path,
        method=method,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as res:
            return json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:500]
        # 401 = key invalida, 402 = sin creditos / plan free (Meshy exige pago para API)
        raise RuntimeError(f"Meshy HTTP {e.code} en {path}: {body}") from e


def download(url: str, dest: Path) -> None:
    with urllib.request.urlopen(url, timeout=180) as res:
        dest.write_bytes(res.read())


def wait_task(task_id: str, key: str, label: str, timeout_s: int = 600) -> dict:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        task = api("GET", f"/text-to-3d/{task_id}", key)
        status = task.get("status")
        print(f"[{label}] {status} {task.get('progress', 0)}%", flush=True)
        if status == "SUCCEEDED":
            return task
        if status in ("FAILED", "CANCELED"):
            raise RuntimeError(f"[{label}] tarea {status}: {task.get('task_error')}")
        time.sleep(5)
    raise TimeoutError(f"[{label}] timeout esperando tarea {task_id}")


def generate(name: str, spec: dict, key: str, preview_only: bool = False) -> dict:
    OUT_DIR.mkdir(exist_ok=True)
    print(f"[{name}] creando preview en Meshy...")
    created = api("POST", "/text-to-3d", key, {
        "mode": "preview",
        "prompt": spec["prompt"][:800],
        "ai_model": "meshy-7.1",
        "pose_mode": "a-pose",
        "target_formats": ["glb"],
    })
    preview_id = created.get("result")
    if not preview_id:
        raise RuntimeError(f"Meshy no devolvio task id: {created}")
    print(f"[{name}] preview_id={preview_id}")
    preview = wait_task(preview_id, key, f"{name}/preview")

    # Las URLs firmadas expiran: descargar preview de inmediato
    model_url = (preview.get("model_urls") or {}).get("glb")
    if not model_url:
        raise RuntimeError(f"[{name}] preview sin model_url.glb: {preview}")
    dest = OUT_DIR / spec["file"]
    download(model_url, dest)

    if preview_only:
        return {"name": name, "task_id": preview_id, "file": spec["file"],
                "bytes": dest.stat().st_size, "mode": "preview"}

    print(f"[{name}] creando refine (textura)...")
    refined = api("POST", "/text-to-3d", key, {
        "mode": "refine",
        "preview_task_id": preview_id,
        "enable_pbr": True,
        "target_formats": ["glb"],
    })
    refine_id = refined.get("result")
    if not refine_id:
        raise RuntimeError(f"Meshy refine sin task id: {refined}")
    final = wait_task(refine_id, key, f"{name}/refine")
    model_url = (final.get("model_urls") or {}).get("glb")
    if model_url:
        download(model_url, dest)
    thumb = final.get("thumbnail_url")
    if thumb:
        download(thumb, OUT_DIR / (dest.stem + ".png"))
    return {"name": name, "task_id": refine_id, "preview_task_id": preview_id,
            "file": spec["file"], "bytes": dest.stat().st_size, "mode": "refine"}


def main() -> int:
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", choices=sorted(MODELS), default=None)
    parser.add_argument("--preview-only", action="store_true",
                        help="solo preview sin textura (mas barato)")
    args = parser.parse_args()

    key = os.environ.get("MESHY_API_KEY", "").strip()
    if not key:
        print("ERROR: falta MESHY_API_KEY en el entorno.", file=sys.stderr)
        print("Meshy exige plan de pago para API keys. Alternativa gratis:",
              file=sys.stderr)
        print("  1) Web manual: https://www.meshy.ai -> Text to 3D -> descargar .glb -> models/",
              file=sys.stderr)
        print("  2) Blender riggeado: ver MODELOS.md (gratis, con animacion Idle/Attack)",
              file=sys.stderr)
        return 2

    names = [args.only] if args.only else ["titan", "volt"]
    results = []
    manifest = OUT_DIR / "meshy-tasks.json"
    for name in names:
        try:
            r = generate(name, MODELS[name], key, args.preview_only)
        except RuntimeError as e:
            print(f"ERROR en {name}: {e}", file=sys.stderr)
            # 402 / fondos insuficientes: no seguir gastando, guardar lo hecho
            if "402" in str(e) or "Insufficient" in str(e):
                print("Fondos insuficientes en Meshy. Recarga en https://www.meshy.ai/settings/subscription", file=sys.stderr)
                break
            raise
        results.append(r)
        # Guardar manifiesto tras CADA modelo (si el siguiente falla, no se pierde este)
        previous = []
        if manifest.exists():
            try:
                previous = json.loads(manifest.read_text(encoding="utf-8"))
            except ValueError:
                previous = []
        by_name = {x["name"]: x for x in previous}
        by_name.update({x["name"]: x for x in results})
        manifest.write_text(json.dumps(list(by_name.values()), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if not results:
        return 1
    print(f"\nOK: {len(results)} modelo(s) en {OUT_DIR} (manifiesto: {manifest.name})")
    print("Nota: GLB estatico sin rig. Para animarlo usa Blender o rigging de Meshy.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
