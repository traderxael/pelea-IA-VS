# Juego Pelea IA vs IA 3D para Celular

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
