#!/usr/bin/env python3
"""Genera modelos 3D con la API de Tripo (texto -> GLB).

Uso:
    export TRIPO_API_KEY="tsk_..."        # en bash: export / en cmd: set
    python tools/tripo_generate.py           # genera TITAN y VOLT
    python tools/tripo_generate.py --only titan

La key NUNCA va en el repo: solo se lee de la variable de entorno
TRIPO_API_KEY. Los .glb salen en models/ y se versionan.
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

BASE = "https://openapi.tripo3d.ai/v3"
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
}
NEGATIVE = "weapon, gun, blurry, low quality, extra limbs, deformed, text, watermark"


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
        raise RuntimeError(f"Tripo HTTP {e.code} en {path}: {body}") from e


def download(url: str, dest: Path) -> None:
    with urllib.request.urlopen(url, timeout=180) as res:
        dest.write_bytes(res.read())


def generate(name: str, spec: dict, key: str) -> dict:
    OUT_DIR.mkdir(exist_ok=True)
    print(f"[{name}] creando tarea en Tripo...")
    created = api(
        "POST",
        "/generation/text-to-model",
        key,
        {
            "prompt": spec["prompt"],
            "negative_prompt": NEGATIVE,
            "model": "v3.1-20260211",
            "face_limit": 30000,
            "texture": True,
            "pbr": True,
            "texture_quality": "standard",
            "geometry_quality": "standard",
            "auto_size": False,
        },
    )
    if created.get("code") != 0:
        raise RuntimeError(f"Tripo no creó la tarea: {created}")
    task_id = created["data"]["task_id"]
    print(f"[{name}] task_id={task_id} (las URLs expiran en 5 min: descargar al terminar)")

    for _ in range(100):
        task = api("GET", f"/tasks/{task_id}", key)["data"]
        status, progress = task.get("status"), task.get("progress", 0)
        print(f"[{name}] {status} {progress}%", flush=True)
        if status == "success":
            out = task.get("output") or {}
            model_url = out.get("model_url")
            if not model_url:
                raise RuntimeError(f"[{name}] success sin model_url: {task}")
            dest = OUT_DIR / spec["file"]
            download(model_url, dest)
            preview = out.get("rendered_image_url")
            if preview:
                download(preview, OUT_DIR / (dest.stem + ".png"))
            return {
                "name": name,
                "task_id": task_id,
                "file": spec["file"],
                "bytes": dest.stat().st_size,
                "prompt": spec["prompt"],
            }
        if status in ("failed", "cancelled", "banned", "expired"):
            raise RuntimeError(f"[{name}] tarea {status}: {task}")
        time.sleep(3)
    raise TimeoutError(f"[{name}] timeout esperando la tarea {task_id}")


def main() -> int:
    # Carga .env local si existe (nunca se commitea: está en .gitignore).
    # Las variables ya exportadas en el entorno tienen prioridad.
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", choices=sorted(MODELS), default=None)
    args = parser.parse_args()

    key = os.environ.get("TRIPO_API_KEY", "").strip()
    if not key:
        print("ERROR: falta TRIPO_API_KEY en el entorno.", file=sys.stderr)
        return 2
    if not key.startswith("tsk_"):
        print("ERROR: TRIPO_API_KEY no parece una key de Tripo (prefijo tsk_).", file=sys.stderr)
        return 2

    names = [args.only] if args.only else list(MODELS)
    results = []
    for name in names:
        results.append(generate(name, MODELS[name], key))
        # Si el primero falla, generate() lanza y no se gasta el segundo.

    manifest = OUT_DIR / "tripo-tasks.json"
    previous = []
    if manifest.exists():
        try:
            previous = json.loads(manifest.read_text(encoding="utf-8"))
        except ValueError:
            previous = []
    by_name = {r["name"]: r for r in previous}
    by_name.update({r["name"]: r for r in results})
    manifest.write_text(
        json.dumps(list(by_name.values()), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"\nOK: {len(results)} modelo(s) en {OUT_DIR} (manifiesto: {manifest.name})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
