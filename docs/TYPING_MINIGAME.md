# Minijuego de tipeo - Documentación base

## Objetivo
Este repo queda dedicado exclusivamente a la mecánica de tipeo. Se añadió una base modular para avanzar rápido en próximas iteraciones.

## Estructura inicial

- `scripts/word-bank.js`: palabras por dificultad.
- `scripts/scoring.js`: cálculo de WPM, accuracy y score final.
- `scripts/typing-game.js`: motor principal del minijuego, desacoplado de UI.

## Flujo de la mecánica

1. Crear instancia de `TypingMinigame`.
2. Llamar `start()` al iniciar partida (o automáticamente en primera tecla).
3. Enviar cada tecla a `handleKey(key)`.
4. Renderizar el estado con `getSnapshot()`.

## Ejemplo de uso

```js
import { TypingMinigame } from "./scripts/typing-game.js";

const game = new TypingMinigame({ difficulty: "normal", timeLimitMs: 45000 });

window.addEventListener("keydown", (event) => {
  const snapshot = game.handleKey(event.key);

  // Aquí actualizas UI con snapshot.currentWord, snapshot.input,
  // snapshot.score, snapshot.wpm, snapshot.accuracy, etc.
  if (snapshot.finished) {
    console.log("Partida terminada", snapshot);
  }
});
```

## Próximos pasos recomendados

- Agregar un adaptador UI (DOM/Canvas).
- Añadir tests unitarios de score y flujo del juego.
- Guardar récords por dificultad.
- Añadir pools de palabras por idioma.
