# Modelos 3D animados

El juego carga `.glb` desde `assets/models/`. Si un `.glb` no existe o no carga (p. ej. `file://`), usa el modelo procedural de respaldo: nada se rompe.

## Roster HD realista (principal)

| Archivo | Personaje | Vida | Velocidad | Especial |
|---|---|---|---|---|
| `assets/models/hd_ninja.glb` | 🥷 NINJA HD | 80 | 1.35 | dash `Punch2` |
| `assets/models/hd_soldier.glb` | 🪖 SOLDADO HD | 95 | 1.12 | proyectil `Special_Cast` |
| `assets/models/hd_ronin.glb` | ⚔️ RONIN HD | 88 | 1.22 | onda `SwordAttack` |

Requisitos de cada `.glb` HD:
- Esqueleto **Mixamo** de 52 huesos (`Hips`, `Spine`, `LeftArm`, `RightHand`, …). El arma se monta en `RightHand`.
- **22 clips** con nombres canónicos (ver abajo).
- **≤50k triángulos**, 1 material, texturas ≤1024, peso ≤6 MB.

### Clips canónicos (22)
`Idle`, `Idle2`, `Walk`, `Run`, `KO`, `Punch1`, `Punch2`, `Kick`, `Uppercut`, `Hammer_Overhead`, `SwordAttack`, `Special_Cast`, `HitHigh`, `HitLow`, `Block`, `Knockdown`, `Getup`, `Victory`, `JumpStart`, `JumpLoop`, `JumpLand`, `Roll`.

El juego resuelve clips por nombre; los legacy solo necesitan `Idle` + un ataque. `resolveHDClips` mapea los canónicos a la máquina de estados de combate.

## Pipeline HD (Rodin → rig → retarget → optimize)

1. **Generar + riggear (Rodin).** Text-to-3D con Hyper3D Rodin, salida con esqueleto Mixamo. Los `.glb` crudos de alta resolución quedan en `models/hd_rigged/{ninja,soldier,ronin}.glb` (git-ignored, ~28-34 MB, ~380-450k tris). Requiere `RODIN_API_KEY`/`HYPER3D_API_KEY` en el entorno (nunca se commitean).

2. **Retarget de animaciones (Blender 5.2, headless).** `tools/retarget_ual.py` importa el rig HD y la librería **UAL** (Rigify, CC0, `tools/ual/AnimationLibrary_Godot_Standard.gltf`), y re-bakea a 30 fps sobre el rig Mixamo:
   - 4 clips de Rodin (`Idle`, `Walk`, `Run`, `KO`) re-bakeados; `Walk`/`Run` se vuelven *in-place* (se resta el drift horizontal).
   - 11 clips UAL retargeteados por **copia de orientación mundo** (verificado empíricamente: la fórmula delta-desde-rest producía golpes laterales porque las rest poses difieren, HD=A vs UAL=T).
   - 7 clips autorados proceduralmente (`Kick`, `Uppercut`, `Hammer_Overhead`, `Block`, `Knockdown`, `Getup`, `Victory`).
   - Hips: traslación escalada por `altura_tgt/altura_src`. Normaliza a altura 2.0. Exporta NLA_TRACKS a `tools/_work_<name>.glb` + previews Workbench en `tools/shots/`.

   ```bash
   "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" --background \
       --factory-startup --offline-mode --python tools/retarget_ual.py -- --name all
   ```
   (`--name ninja|soldier|ronin|all`). Redirige stdout a un fichero, **no lo pipees por `grep`**: el pipe bloquea el stdout de Blender y el proceso se queda colgado.

3. **Optimizar a presupuesto.** `tools/gltf/rig-optimize-lite.mjs` simplifica (meshoptimizer), fusiona a 4 influencias por vértice (Three.js), comprime texturas (sharp) y cuantiza:

   ```bash
   node tools/gltf/rig-optimize-lite.mjs tools/_work_ninja.glb   assets/models/hd_ninja.glb   0.12  1024 0.005
   node tools/gltf/rig-optimize-lite.mjs tools/_work_soldier.glb assets/models/hd_soldier.glb 0.102 1024 0.005
   node tools/gltf/rig-optimize-lite.mjs tools/_work_ronin.glb   assets/models/hd_ronin.glb   0.106 1024 0.005
   ```
   `ratio` ≈ 46000 / tris_originales. Resultado: ~46k tris, 22 clips, 52 huesos, ~3 MB.

4. **Inspeccionar / verificar.**
   ```bash
   node tools/gltf/inspect.mjs assets/models/hd_ninja.glb   # tris, clips, joints, materiales
   node tools/verify_hd.mjs                                 # clips resueltos + arma en RightHand
   ```

## Legacy (low-poly, 13 peleadores)

Generados con Blender (`tools/blender_build.py`) o Tripo AI. Solo necesitan `Idle` + un clip de ataque; el cuerpo debe tener huesos con nombres que contengan `arm`, `leg`/`thigh`, `head`. Archivos en `assets/models/*.glb` (titan, volt, soldier, ninja, samurai, …).

```bash
& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --background --factory-startup --python "tools/blender_build.py"
```

## Estado
- ✅ 3 luchadores HD riggeados con 22 clips, ≤50k tris, arma en RightHand.
- ✅ Pipeline Rodin → retarget UAL → optimize reproducible.
- ✅ 13 legacy con respaldo procedural.
- ✅ Verificación en Chrome real (`tools/e2e.mjs`, `verify_hd.mjs`).