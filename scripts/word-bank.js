/**
 * Banco de palabras por dificultad para el minijuego de tipeo.
 * Puedes extender fácilmente este archivo con más categorías.
 */
export const WORD_BANK = {
  easy: [
    "casa",
    "gato",
    "sol",
    "luna",
    "juego",
    "nube",
    "silla",
    "mesa",
    "teclado",
    "pantalla",
  ],
  normal: [
    "velocidad",
    "reaccion",
    "precision",
    "desarrollo",
    "aventura",
    "desafio",
    "mecanica",
    "estrategia",
    "interfaz",
    "configuracion",
  ],
  hard: [
    "sincronizacion",
    "electromagnetismo",
    "desoxirribonucleico",
    "hiperconectividad",
    "interoperabilidad",
    "responsabilidad",
    "transformaciones",
    "multidimensional",
    "retroalimentacion",
    "internacionalizacion",
  ],
};

export function getWordsByDifficulty(difficulty = "normal") {
  return WORD_BANK[difficulty] ?? WORD_BANK.normal;
}
