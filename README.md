# pelea IA VS

Juego 3D para celulares de pelea IA vs IA, estilo AI Fight.

## Características
- **Modo:** IA vs IA (con control opcional del jugador)
- **IA:** Adaptativa — aprende de ataques cercanos/lejanos, sube bloqueo y contraataque
- **Luchadores:** Robots 3D (TITÁN AZUL vs VOLT ROJO)
- **Plataforma:** Web con Three.js, sin instalar APK
- **Controles:** Joystick virtual + botones táctiles (Puño 👊, Patada 🦵, Especial ⚡)

## Cómo jugar
Abre `index.html` en tu celular o computadora. En PC: WASD para moverte, J=puño, K=patada, L=especial. En celular: usa el joystick y los botones en pantalla.

Barras de vida y energía, daño flotante, partículas, cámara que sigue la acción, rondas con contador y modo AUTO para ver pelear a ambas IAs.

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

## Estructura
- `index.html` — juego completo (HTML + CSS + JS + Three.js)
- `DISENO.md` — diseño y decisiones tomadas
