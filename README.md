# pelea IA VS

Juego 3D para celulares de pelea IA vs IA, estilo AI Fight.

## Características
- **Modo:** IA vs IA (con control opcional del jugador)
- **IA:** Adaptativa — aprende de ataques cercanos/lejanos, sube bloqueo y contraataque
- **Luchadores:** Robots 3D y soldado riggeados (modelos Blender GLB animados)
- **Plataforma:** Web con Three.js, sin instalar APK
- **Controles:** Joystick virtual + botones táctiles (Puño 👊, Patada 🦵, Especial ⚡)
- **Armas:** 6 armas con alcance/daño/recarga distintos (la IA también las usa)

## Cómo jugar
Abre `index.html` en tu celular o computadora. En PC: WASD para moverte, J=puño, K=patada, L=especial. En celular: usa el joystick y los botones en pantalla.

Barras de vida y energía, daño flotante, partículas, cámara que sigue la acción, rondas con contador y modo AUTO para ver pelear a ambas IAs.

## Armas (elige con la barra superior)
- 🥊 **Puños** — equilibrado, daño normal
- 🗡️ **Espada** — mucho mayor alcance (4.7m) y +30% daño
- 🔨 **Martillo** — daño brutal (x2.0) pero lento (recarga 1.75x)
- 🥢 **Nunkus** — muy rápido (recarga 0.5x)
- 🪄 **Lanza** — alcance máximo (6.3m)
- 🔫 **Plasma** — proyectil a distancia que viaja por el aire
- 🎲 VOLT ROJO elige un arma aleatoria en cada ronda (reto distinto cada vez)

Cambia de arma con un toque en la barra de armas.

## Combos
- **Tú:** 3+ golpes seguidos sin recibir daño → daño **+35%** (🔥 aparece el contador xN)
- **VOLT ROJO (IA):** el mismo sistema pero con bonus limitado a **+15%**, para que puedas ganarle
- El contador aparece a la izquierda si la IA lo logra (en modo AUTO)

## Armas legendarias
- 🐉 **Espada de Fuego** y ⚡ **Mjölnir** caen en la arena con un **haz de luz**
- Quien la toma primero hace daño x2.0/x2.6 durante 22 segundos
- Período de gracia de 1.5s antes de poder recogerla

## Sonidos
Cada golpe suena distinto según el arma: 🥊 golpe seco, 🗡️ clang metálico, 🔨 boom grave, 🥢 doble clip, 🔫 pew de plasma, 🛡️ ping de bloqueo, + fanfarria al obtener la legendaria

## Luchadores (elige tu personaje)
- 🤖 **Titán Azul** — robot clásico: 100 de vida, velocidad normal
- 🪖 **Soldado Verde** — humano con casco, chaleco táctico y rifle: 85 de vida pero **+18% de velocidad**

Cambia de personaje con el selector "🤖 Titán / 🪖 Soldado" arriba a la izquierda.

## Personalidades de IA
- 🧠 **Adaptativa** — aprende de tu patrón: si atacas mucho de cerca, sube bloqueo y contraataque
- 🔥 **Agresiva** — ataca sin parar, más rápida y daño +25%
- 🛡️ **Defensiva** — bloquea mucho (92%) y te contraataca
- 🎲 **Tramposa** — esquiva por completo a veces, te engaña y ataca con especial
- 🤪 **Grok** — caos total, giros locos sin patrón, esquiva por azar y dice "¡JA!"
- 💬 **ChatGPT** — estratégico, analiza distancia y usa especial cuando tiene energía (70+)
- 🧭 **Claude** — paciente, deja que te canses y contraataca con calma, más bloqueo (82%)
- 🔍 **DeepSeek** — busca tu debilidad: si atacas de cerca persigue y usa patada, si huyes carga especial

Cambia la personalidad con el selector desplegable arriba a la izquierda. Cada una tiene sus frases divertidas que aparecen.

## Jugar online
https://traderxael.github.io/pelea-IA-VS/ (GitHub Pages)

## Modelos 3D animados (Blender + Tripo AI)
El juego carga automáticamente modelos `.glb` (Idle + Attack) desde `assets/models/`. Titán, Volt y Soldado ya están hechos con Blender. Ver **MODELOS.md** para el pipeline y Tripo AI.

## Estructura
- `index.html` — juego completo (HTML + CSS + JS + Three.js)
- `MODELOS.md` — pipeline de modelos 3D
- `assets/models/` — GLB riggeados de Blender (titan, volt, soldier)
- `tools/blender_build.py` — generador de modelos animados
- `tools/tripo_generate.py` — generador Tripo API (requiere créditos)
- `DISENO.md` — diseño y decisiones tomadas
