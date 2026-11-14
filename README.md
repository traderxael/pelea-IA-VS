# PELEA IA VS — Combate 3D estilo Mortal Kombat

Juego 3D para celular y PC de pelea **IA vs IA** (con control opcional del jugador), estilo Mortal Kombat: rounds al mejor de 3, bloqueo, launcher, combos, **FINISH HIM** y fatality. Luchadores realistas riggeados con 22 animaciones cada uno.

## Jugar online
https://traderxael.github.io/pelea-IA-VS/ (GitHub Pages)

## Cómo jugar
Abre `index.html` en tu celular o computadora (también funciona con `file://`, sin servidor). Por defecto arranca en modo **AUTO** (las dos IAs pelean solas); pulsa `🤖 AUTO` para tomar el control de tu luchador.

- **PC:** `WASD` / flechas para moverte, `J` puño, `K` patada, `L` especial, `I` launcher, `Espacio` salto, `Shift` o `U` bloqueo (mantener).
- **Móvil:** joystick virtual + botones táctiles (👊 puño, 🦵 patada, ⚡ especial, 🚀 launcher, 🛡️ bloqueo, ⬆️ salto). **Doble toque en 👊 = launcher.**
- **FINISH HIM:** cuando ganas el match, pulsa `J`, `K`, `L` (o los botones 👊🦵⚡) para ejecutar la fatality.
- **🔊** silencia/activa sonido y voces.

Barras de vida y energía, daño flotante, partículas, cámara que sigue la acción, sacudida de cámara en golpes fuertes.

## Luchadores

### Realistas (HD) — roster principal
Modelos 3D realistas generados con Rodin, riggeados (esqueleto Mixamo de 52 huesos) y animados con 22 clips. Cada uno tiene un **especial propio**:

- 🥷 **NINJA HD** — 80 de vida, velocidad 1.35. Especial: dash con `Punch2`.
- 🪖 **SOLDADO HD** — 95 de vida, velocidad 1.12. Especial: proyectil `Special_Cast`.
- ⚔️ **RONIN HD** — 88 de vida, velocidad 1.22. Especial: onda de choque `SwordAttack` (alcance 4.0).

### Legacy — 13 peleadores low-poly seleccionables
🤖 Titán, 🪖 Soldado, 🥷 Ninja, ⚔️ Samurai, 🛡️ Gladiador, 🦣 Bruto, 🧛 Vampiro, 🥋 Ronin, 🦏 Rhino, 🐼 Panda, 👩‍🦰 Pelirroja, 👹 Ogro, 🔴 Volt.

Cambia tu personaje y el rival con los selectores de arriba (grupos **REALISTAS (HD)** y **LEGACY**). Si un `.glb` no carga, el juego usa el modelo procedural de respaldo (no se rompe).

## Combate (estilo Mortal Kombat)
- **Rounds al mejor de 3.** Contador de rondas y de victorias.
- **Ventanas de golpe activas:** cada ataque tiene su `hitAt` y alcance; el daño solo conecta dentro de la ventana y el cono de frente.
- **Bloqueo:** reduce el daño a un **chip determinista del 20%** (máx. 5). Mantén `Shift`/`U`/🛡️.
- **Launcher y juggle:** `I` o doble toque en 👊 lanza al rival al aire; remata con combos aéreos.
- **Combos y cancels:** `J`,`J` encadena `punch2`; 3+ golpes seguidos sin recibir daño → **+35%** de daño (🔥 contador xN). La IA tiene el mismo sistema con bonus limitado a **+15%**.
- **FINISH HIM:** al ganar el match aparece la ventana (3 s) para ejecutar la **fatality** con `J`,`K`,`L`.
- **KO:** el derrotado cae y se hunde; el ganador salta de celebración.

## Armas (elige con la barra superior)
6 armas con alcance/daño/recarga distintos (la IA también las usa), montadas en la mano derecha (`RightHand`) del esqueleto:

- 🥊 **Puños** — equilibrado.
- 🗡️ **Espada** — mayor alcance (4.7 m) y +30% daño.
- 🔨 **Martillo** — daño x2.0 pero lento (recarga 1.75x).
- 🥢 **Nunkus** — muy rápido (recarga 0.5x).
- 🪄 **Lanza** — alcance máximo (6.3 m).
- 🔫 **Plasma** — proyectil a distancia.

### Armas legendarias
🐉 **Espada de Fuego** y ⚡ **Mjölnir** caen en la arena con un haz de luz. Quien la toma primero hace daño x2.0/x2.6 durante 22 s (período de gracia de 1.5 s antes de recogerla).

## Personalidades de IA + voces gratis
Cada rival tiene una personalidad con frases y **voz propia** (Web Speech API del navegador, **gratis, sin API key**). Cambia la personalidad con el selector desplegable; cada una tiene timbre (pitch) y velocidad distintos:

- 🤖 **OpenAI** — estratégico, voz grave y pausada.
- ⚡ **Qwen** — rápido y agresivo, voz aguda y veloz.
- 🤪 **Grok** — caos total, esquiva por azar, voz muy aguda.
- 💎 **Gemini** — paciente y defensivo, voz grave y lenta.
- 🔍 **DeepSeek** — busca tu debilidad, voz muy grave.

Las voces se silencian con 🔊. Si el navegador no tiene voces en español, usa las disponibles del sistema.

## Animaciones (22 clips por luchador HD)
`Idle`, `Idle2`, `Walk`, `Run`, `KO`, `Punch1`, `Punch2`, `Kick`, `Uppercut`, `Hammer_Overhead`, `SwordAttack`, `Special_Cast`, `HitHigh`, `HitLow`, `Block`, `Knockdown`, `Getup`, `Victory`, `JumpStart`, `JumpLoop`, `JumpLand`, `Roll`.

Caminar, reacción al impacto, KO, victoria, bloqueo y salto importados/retargeteados desde Blender. Transiciones con crossfade (`AnimationMixer`).

## Rendimiento
- Presupuesto: **<120k triángulos / <150 draw calls** por frame.
- `pixelRatio` limitado (1.5 móvil / 2 PC), sombras 1024.
- **Degradación escalonada** si los FPS sostenidos bajan de 25: sombra 512 → pixelRatio 1 → sombras off.
- Carga HD lazy; los legacy usan 2 clips.

## Modelos 3D (pipeline)
Los `.glb` HD se generan con **Rodin** (text-to-3D), se riggean con esqueleto Mixamo y se animan retargeteando la librería **UAL** (CC0) + clips autorados en Blender. Ver **MODELOS.md** para el pipeline completo y **DISENO.md** para las decisiones.

## Verificación (tests)
Requiere `python -m http.server 8123` en la raíz y Chrome instalado. Usa Playwright + Chrome headless con swiftshader (todos los waits por condición de estado, no por tiempo):

```bash
node tools/smoke.mjs         # carga HD, render, arma en RightHand, layout
node tools/e2e.mjs           # desktop + móvil (táctil) + file://; rounds, FINISH, fatality, voces
node tools/verify_hd.mjs     # diagnóstico HD: clips, weapon parent, overflow
node tools/verify_voice.mjs  # voces por personalidad (pitch/rate distintos) + mute
```

## Estructura
- `index.html` — juego completo (HTML + CSS + JS + Three.js, módulo inline único para que `file://` funcione).
- `assets/models/hd_{ninja,soldier,ronin}.glb` — luchadores HD riggeados (22 clips, ≤50k tris).
- `assets/models/*.glb` — legacy low-poly.
- `MODELOS.md` — pipeline de modelos 3D (Rodin + retarget UAL).
- `DISENO.md` — diseño y decisiones.
- `tools/retarget_ual.py` — retarget Blender UAL→Mixamo + clips autorados.
- `tools/gltf/` — optimizador e inspector de GLB.
- `tools/{smoke,e2e,verify_hd,verify_voice}.mjs` — verificación en Chrome real.