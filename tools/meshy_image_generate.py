#!/usr/bin/env python3
"""blender-kiln style: FOTO -> modelo 3D (Meshy Image-to-3D).
Replica local del plugin blender-kiln del post de @dextune:
foto/descripcion -> modelo editable a tamano real, optimizado, validado, GLB.

Uso:
  python tools/meshy_image_generate.py --only vamp          # 1 foto de prueba
  python tools/meshy_image_generate.py --all                # las 6 fotos
  python tools/meshy_image_generate.py --only vamp --preview-only

Docs: POST /openapi/v1/image-to-3d (docs.meshy.ai/en/api/image-to-3d)
La foto se envia como data URI base64 (no necesita URL publica).
Requiere MESHY_API_KEY en .env (plan pago; si fondos insuficientes -> 402).
Salida: models/meshy-foto-<nombre>.glb + manifiesto. GLB estatico sin rig.
"""
from __future__ import annotations
import argparse, base64, json, os, sys, time, urllib.error, urllib.request
from pathlib import Path

BASE = "https://api.meshy.ai/openapi/v1"
ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "models"
REFS = {
    "vamp": "refs/01-vampiro.jpg", "ronin": "refs/02-ronin.jpg", "rhino": "refs/03-rhino.jpg",
    "panda": "refs/04-panda.jpg", "roja": "refs/05-roja.jpg", "ogro": "refs/06-ogro.jpg",
}

def load_env():
    p = ROOT / ".env"
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            line=line.strip()
            if line and not line.startswith("#") and "=" in line:
                k,v=line.split("=",1); os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

def api(method, path, key, payload=None):
    req = urllib.request.Request(BASE+path, method=method,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={"Content-Type":"application/json","Authorization":f"Bearer {key}"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r: return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body=e.read().decode("utf-8","replace")[:500]
        raise RuntimeError(f"Meshy HTTP {e.code} en {path}: {body}") from e

def download(url, dest):
    with urllib.request.urlopen(url, timeout=180) as r: dest.write_bytes(r.read())

def data_uri(img: Path) -> str:
    b64 = base64.b64encode(img.read_bytes()).decode()
    ext = img.suffix.lower().lstrip(".")
    mime = "image/jpeg" if ext in ("jpg","jpeg") else f"image/{ext}"
    return f"data:{mime};base64,{b64}"

def generate(name, key):
    img = ROOT / REFS[name]
    if not img.exists(): raise FileNotFoundError(img)
    OUT_DIR.mkdir(exist_ok=True)
    print(f"[{name}] foto {img.name} ({img.stat().st_size} bytes) -> Image-to-3D...")
    created = api("POST","/image-to-3d",key,{"image_url": data_uri(img), "should_texture": True, "target_formats":["glb"]})
    task_id = created.get("result")
    if not task_id: raise RuntimeError(f"sin task id: {created}")
    print(f"[{name}] task_id={task_id}")
    deadline=time.time()+900
    while time.time()<deadline:
        task=api("GET",f"/image-to-3d/{task_id}",key)
        st=task.get("status"); print(f"[{name}] {st} {task.get('progress',0)}%", flush=True)
        if st=="SUCCEEDED":
            url=(task.get("model_urls") or {}).get("glb")
            if not url: raise RuntimeError(f"sin glb: {task}")
            dest=OUT_DIR/f"meshy-foto-{name}.glb"; download(url,dest)
            thumb=task.get("thumbnail_url")
            if thumb: download(thumb, OUT_DIR/f"meshy-foto-{name}.png")
            return {"name":name,"task_id":task_id,"file":dest.name,"bytes":dest.stat().st_size,"source":REFS[name]}
        if st in ("FAILED","CANCELED"): raise RuntimeError(f"{st}: {task.get('task_error')}")
        time.sleep(5)
    raise TimeoutError(task_id)

def main():
    load_env()
    ap=argparse.ArgumentParser(); ap.add_argument("--only",choices=sorted(REFS)); ap.add_argument("--all",action="store_true"); a=ap.parse_args()
    key=os.environ.get("MESHY_API_KEY","").strip()
    if not key:
        print("ERROR: falta MESHY_API_KEY en .env", file=sys.stderr); return 2
    names=[a.only] if a.only else (list(REFS) if a.all else ["vamp"])
    results=[]
    for n in names:
        try: results.append(generate(n,key))
        except RuntimeError as e:
            print(f"ERROR en {n}: {e}", file=sys.stderr)
            if "402" in str(e) or "Insufficient" in str(e) or "funds" in str(e).lower():
                print("Fondos insuficientes Meshy. Recarga: https://www.meshy.ai/settings/subscription", file=sys.stderr); break
            raise
    if results:
        man=OUT_DIR/"meshy-photo-tasks.json"
        prev=json.loads(man.read_text()) if man.exists() else []
        by={r["name"]:r for r in prev}; by.update({r["name"]:r for r in results})
        man.write_text(json.dumps(list(by.values()),indent=2,ensure_ascii=False)+"\n")
        print(f"OK {len(results)} modelo(s) foto->GLB en {OUT_DIR}")
        return 0
    return 1

if __name__=="__main__": raise SystemExit(main())
