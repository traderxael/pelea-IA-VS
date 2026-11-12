#!/usr/bin/env python3
"""Pipeline de luchadores HD realistas con Hyper3D Rodin (generate -> rig -> optimize).

Uso (Git Bash, desde la raiz del repo):
    python tools/rodin_hd_pipeline.py generate --name ninja
    python tools/rodin_hd_pipeline.py rig      --name ninja
    python tools/rodin_hd_pipeline.py optimize --name ninja [--ratio 0.25 --tex 1024 --error 0.005]
    python tools/rodin_hd_pipeline.py all      --name ninja

La key NUNCA se imprime ni se commitea: se lee de HYPER3D_API_KEY (env) o de
C:/Users/USUARIO/.qoder/secrets/hyper3d.env. .gitignore ya cubre secrets/ y .env.

Requiere plan con creditos Rodin. Generacion Gen-2.5-Low = 0.5 creditos.
Si la API devuelve 402 (sin fondos) el script sale con codigo 2 y mensaje claro,
sin gastar de mas. El manifiesto tools/hd-tasks.json guarda uuid/subscription_key
de cada etapa para poder reanudar rigging/optimize sin regenerar.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "models" / "hd_raw"
RIGGED_DIR = ROOT / "models" / "hd_rigged"
OUT_DIR = ROOT / "assets" / "models"
MANIFEST = ROOT / "tools" / "hd-tasks.json"
GLTF_TOOLS = ROOT / "tools" / "gltf"

BASE = "https://api.hyper3d.com/api/v2"
TIER = "Gen-2.5-Low"  # cuenta Basic

PROMPTS = {
    "ninja": (
        "Realistic athletic male ninja fighter, full body, black tactical shinobi outfit "
        "with dark crimson accents, face mask covering nose and mouth, hood, split-toe tabi "
        "boots, lean muscular build, empty hands no weapons, standing upright, PBR materials, "
        "detailed fabric and skin, game-ready character, symmetrical"
    ),
    "soldier": (
        "Realistic male special forces soldier fighter, full body, olive drab tactical vest "
        "over combat shirt, cargo pants, combat boots, fingerless gloves, short cropped hair, "
        "dog tags, muscular build, empty hands no weapons, standing upright, PBR materials, "
        "game-ready character, symmetrical"
    ),
    "ronin": (
        "Realistic male ronin samurai fighter, full body, worn indigo kimono and hakama pants, "
        "straw hat, topknot hair, katana sheath at hip, waraji sandals, lean muscular build, "
        "empty hands no weapons, standing upright, PBR materials, game-ready character, symmetrical"
    ),
}

RIG_PRESETS = [
    "human_sp/offensive_idle",
    "human_sp/walking",
    "human_sp/jogging",
    "human_sp/dying",
]


def get_key() -> str:
    key = os.environ.get("HYPER3D_API_KEY", "").strip()
    if not key:
        env_file = Path("C:/Users/USUARIO/.qoder/secrets/hyper3d.env")
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("HYPER3D_API_KEY="):
                    key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    if not key:
        print("ERROR: falta HYPER3D_API_KEY (env o secrets/hyper3d.env).", file=sys.stderr)
        raise SystemExit(2)
    return key


def headers(key: str) -> dict:
    return {"Authorization": f"Bearer {key}"}


def load_manifest() -> dict:
    if MANIFEST.exists():
        try:
            return json.loads(MANIFEST.read_text(encoding="utf-8"))
        except ValueError:
            return {}
    return {}


def save_manifest(m: dict) -> None:
    MANIFEST.write_text(json.dumps(m, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def check_http(r: requests.Response, ctx: str) -> None:
    if r.status_code == 402:
        print(f"ERROR 402 ({ctx}): sin creditos Rodin. Recarga en "
              "https://hyper3d.ai/workspace/api-dashboard y reintenta, o usa el "
              "fallback gratis (Soldier.glb de three.js).", file=sys.stderr)
        raise SystemExit(2)
    if r.status_code >= 400:
        body = r.text[:400]
        print(f"ERROR HTTP {r.status_code} ({ctx}): {body}", file=sys.stderr)
        raise SystemExit(1)


def poll(subscription_key: str, key: str, label: str, timeout_s: int = 900) -> None:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        r = requests.post(f"{BASE}/status", headers=headers(key),
                          json={"subscription_key": subscription_key}, timeout=60)
        check_http(r, f"status {label}")
        jobs = r.json().get("jobs", [])
        if not jobs:
            raise SystemExit(f"status {label}: sin jobs en la respuesta")
        states = [j.get("status") for j in jobs]
        done = sum(1 for s in states if s == "Done")
        print(f"[{label}] {done}/{len(jobs)} done ({','.join(str(s) for s in states)})", flush=True)
        if all(s == "Done" for s in states):
            return
        if any(s == "Failed" for s in states):
            err = next((j.get("error") for j in jobs if j.get("status") == "Failed"), "?")
            raise SystemExit(f"tarea {label} FAILED: {err}")
        time.sleep(10)
    raise SystemExit(f"timeout esperando {label}")


def download_glb(task_uuid: str, key: str, dest: Path, label: str) -> Path:
    r = requests.post(f"{BASE}/download", headers=headers(key),
                      json={"task_uuid": task_uuid}, timeout=60)
    check_http(r, f"download {label}")
    files = r.json().get("list", [])
    glb = next((f for f in files if str(f.get("name", "")).lower().endswith(".glb")
                or str(f.get("url", "")).split("?")[0].lower().endswith(".glb")), None)
    if not glb:
        raise SystemExit(f"download {label}: no hay .glb en {files}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(glb["url"], stream=True, timeout=300) as dl:
        dl.raise_for_status()
        with open(dest, "wb") as fh:
            for chunk in dl.iter_content(1 << 16):
                fh.write(chunk)
    print(f"[{label}] GLB guardado: {dest} ({dest.stat().st_size} bytes)", flush=True)
    return dest


def cmd_generate(name: str, key: str) -> None:
    prompt = PROMPTS[name]
    data = {
        "prompt": prompt,
        "tier": TIER,
        "geometry_file_format": "glb",
        "material": "PBR",
        "quality": "medium",
        "mesh_mode": "Raw",
        "TAPose": "true",
        "use_original_alpha": "false",
        "preview_render": "false",
        "hd_texture": "false",
        "texture_delight": "false",
        "is_micro": "false",
        "geometry_instruct_mode": "faithful",
    }
    print(f"[{name}/gen] enviando a Rodin (tier {TIER}, TAPose)...", flush=True)
    r = requests.post(f"{BASE}/rodin", headers=headers(key), data=data, timeout=300)
    check_http(r, f"generate {name}")
    res = r.json()
    if "error" in res:
        raise SystemExit(f"generate {name}: {res['error']}")
    uuid = res.get("uuid")
    sub = (res.get("jobs") or {}).get("subscription_key")
    if not uuid or not sub:
        raise SystemExit(f"generate {name}: respuesta sin uuid/subscription_key: {res}")
    m = load_manifest()
    m.setdefault(name, {})["generate_uuid"] = uuid
    m[name]["generate_sub"] = sub
    save_manifest(m)
    print(f"[{name}/gen] uuid={uuid}", flush=True)
    poll(sub, key, f"{name}/gen")
    download_glb(uuid, key, RAW_DIR / f"{name}.glb", f"{name}/gen")
    m = load_manifest()
    m[name]["raw_glb"] = str(RAW_DIR / f"{name}.glb")
    save_manifest(m)


def cmd_rig(name: str, key: str) -> None:
    m = load_manifest()
    asset_id = m.get(name, {}).get("generate_uuid")
    if not asset_id:
        raise SystemExit(f"rig {name}: falta generate_uuid (corre generate primero)")
    data = [
        ("asset_id", asset_id),
        ("bone_template", "human"),
        ("skinning_method", "core"),
        ("geometry_file_format", "glb"),
        ("material", "PBR"),
    ]
    for p in RIG_PRESETS:
        data.append(("animation_preset", p))
    print(f"[{name}/rig] rigging human + {len(RIG_PRESETS)} presets...", flush=True)
    r = requests.post(f"{BASE}/rigging", headers=headers(key), data=data, timeout=300)
    check_http(r, f"rig {name}")
    res = r.json()
    if "error" in res:
        raise SystemExit(f"rig {name}: {res['error']}")
    uuid = res.get("uuid")
    sub = (res.get("jobs") or {}).get("subscription_key")
    if not uuid or not sub:
        raise SystemExit(f"rig {name}: respuesta sin uuid/subscription_key: {res}")
    m = load_manifest()
    m[name]["rig_uuid"] = uuid
    m[name]["rig_sub"] = sub
    save_manifest(m)
    print(f"[{name}/rig] uuid={uuid}", flush=True)
    poll(sub, key, f"{name}/rig")
    download_glb(uuid, key, RIGGED_DIR / f"{name}.glb", f"{name}/rig")
    m = load_manifest()
    m[name]["rigged_glb"] = str(RIGGED_DIR / f"{name}.glb")
    save_manifest(m)


def cmd_optimize(name: str, ratio: float, tex: int, error: float) -> None:
    src = RIGGED_DIR / f"{name}.glb"
    if not src.exists():
        raise SystemExit(f"optimize {name}: no existe {src} (corre rig primero)")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    dest = OUT_DIR / f"hd_{name}.glb"
    cmd = ["node", str(GLTF_TOOLS / "rig-optimize-lite.mjs"),
           str(src), str(dest), str(ratio), str(tex), str(error)]
    print(f"[{name}/opt] {' '.join(cmd)}", flush=True)
    res = subprocess.run(cmd, cwd=str(GLTF_TOOLS), capture_output=True, text=True, encoding="utf-8")
    sys.stdout.write(res.stdout or "")
    sys.stderr.write(res.stderr or "")
    if res.returncode != 0:
        raise SystemExit(f"optimize {name} fallo (exit {res.returncode})")
    insp = subprocess.run(["node", str(GLTF_TOOLS / "inspect.mjs"), str(dest)],
                          cwd=str(GLTF_TOOLS), capture_output=True, text=True, encoding="utf-8")
    sys.stdout.write(insp.stdout or "")
    m = load_manifest()
    m.setdefault(name, {})["hd_glb"] = str(dest)
    m[name]["hd_bytes"] = dest.stat().st_size
    save_manifest(m)
    print(f"[{name}/opt] listo: {dest} ({dest.stat().st_size} bytes)", flush=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("cmd", choices=["generate", "rig", "optimize", "all"])
    ap.add_argument("--name", choices=sorted(PROMPTS), required=True)
    ap.add_argument("--ratio", type=float, default=0.25)
    ap.add_argument("--tex", type=int, default=1024)
    ap.add_argument("--error", type=float, default=0.005)
    args = ap.parse_args()
    key = get_key()
    if args.cmd in ("generate", "all"):
        cmd_generate(args.name, key)
    if args.cmd in ("rig", "all"):
        cmd_rig(args.name, key)
    if args.cmd in ("optimize", "all"):
        cmd_optimize(args.name, args.ratio, args.tex, args.error)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())