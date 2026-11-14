# Juego Pelea IA vs IA 3D para Celular

> **Nota:** este documento recoge el diseño del prototipo original. El juego evolucionó a combate estilo Mortal Kombat con luchadores HD realistas; ver `README.md` (estado actual) y `MODELOS.md` (pipeline).

## Evolución a Mortal Kombat (decisiones vigentes)
- **Roster:** 3 luchadores HD realistas (Ninja/Soldado/Ronin; Rodin + rig Mixamo + 22 clips) como principales, más 13 legacy low-poly seleccionables.
- **Combate MK:** rounds al mejor de 3, ventanas de golpe activas, bloqueo con chip 20%, launcher/juggle, combos y cancels, FINISH HIM + fatality.
- **Arena y cámara:** se mantiene la arena 3D libre y la cámara que sigue la acción (no vista lateral).
- **Armas:** se mantienen las 6 + legendarias, adaptadas con clips propios y montadas en `RightHand`.
- **Voces:** gratis (Web Speech API), timbre/velocidad distintos por personalidad de IA (OpenAI/Qwen/Grok/Gemini/DeepSeek).
- **Rendimiento:** <120k tris / <150 calls, degradación escalonada si FPS<25.

## Idea
Juego 3D de peleas estilo AI Fight en el que 2 robots luchan. El jugador observa (modo espectador IA vs IA) o toma control con joystick + botones.

## Selecciones del usuario
- **Modo:** IA vs IA (con control opcional del jugador)
- **IA enemiga:** Adaptativa (aprende de tu patrón: si atacas mucho de cerca, bloquea y contraataca)
- **Luchadores:** Robots metálicos
- **Plataforma:** Web Three.js (funciona en navegador del celular, sin instalar APK)
- **Controles:** Joystick virtual + botones grandes táctiles (Puño, Patada, Especial)

## Qué incluye el prototipo
- Arena 3D con suelo, luces y bordes
- Robot jugador (azul) y Robot rival (rojo) hechos con formas 3D
- IA adaptativa: registra golpes, distancia y velocidad, ajusta bloqueo/contraataque
- Modo automático: ambos pelean solos sin tocar nada
- Botones: Puño, Patada, Especial de energía (requiere energía)
- Barras de vida, daño flotante, partículas de impacto
- Cámara que sigue la acción, soporte táctil y teclado (WASD + J/K/L)

## Mejoras posibles siguientes
1. Personalidades de IA: Agresiva / Defensiva / Tramposa
2. Selección de robots y colores
3. Torneo / Supervivencia
4. Escenarios destructibles
5. Modo online

## Cómo probar
Abre `ai-robot-fight/index.html` en tu celular o computadora. En PC: WASD para moverte, J=puño, K=patada, L=especial. En celular: usa el joystick y los botones en pantalla.
