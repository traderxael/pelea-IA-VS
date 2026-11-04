# Modelos 3D animados con Blender y Tripo AI

El juego carga automáticamente modelos `.glb` de la carpeta `assets/models/`.
Si un `.glb` no existe, usa los modelos procedurales (no se rompe nada).

## Archivos que busca el juego

| Archivo | Personaje | Origen sugerido |
|---|---|---|
| `assets/models/titan.glb` | Titán Azul (jugador/robot) | Blender (ya generado con `blender_build.py`) o Tripo AI |
| `assets/models/volt.glb` | Volt Rojo (IA rival) | Blender / Tripo AI |
| `assets/models/soldier.glb` | Soldado Verde | Tripo AI (recomendado) o Blender |

Requisitos de los `.glb`:
- Una animación llamada **`Idle`** (o cualquier nombre con "idle"/"stand")
- Una animación de ataque llamada **`Attack`** (nombre que contenga attack/punch/jab/hit)
- Cuerpo con **Armature** (huesos) con nombres que contengan `arm`, `leg`/`thigh`, `head` para que el juego pueda moverlos

## Opción A — Blender (automático, incluido en este repo)

1. Instala Blender (este proyecto ya lo instaló con `winget` si aceptaste).
2. Ejecuta:

```powershell
& "C:\Program Files\Blender Foundation\Blender X.X\blender.exe" --background --factory-startup --python "tools/blender_build.py"
```

Genera `titan.glb`, `volt.glb` y `soldier.glb` en `assets/models/` (si parametrizas el script).

## Opción B — Tripo AI (manual, la hace el usuario)

1. Entra a https://www.tripo3d.ai/ (x requiere cuenta gratuita).
2. Escribe un prompt, por ejemplo:
   - Robot: `"low-poly blue fighting robot, boxer, muscular, glowing core, android, best quality"`
   - Soldado: `"low-poly military soldier, combat armor, helmet, rifle"`
3. Descarga el modelo en formato **.glb**.
4. Importa a Blender si quieres animarlo, o descárgalo ya riggeado/animado.
5. Guarda el archivo en `assets/models/titan.glb` (o `soldier.glb`).
6. `git add assets/models` → `git commit` → `git push` — el juego lo detectará solo.

## Estado

- ✅ Código del juego listo para cargar modelos glTF animados (Idle + Attack)
- ✅ Script de Blender para generar robots con huesos y animaciones
- ⏳ Instalación de Blender en curso
- ⏳ Tripo AI: requiere tu cuenta en tripo3d.ai (yo no puedo crearla por ti)
