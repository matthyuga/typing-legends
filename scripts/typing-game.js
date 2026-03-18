import { getWordsByDifficulty } from "./word-bank.js";
import {
  calculateAccuracy,
  calculateScore,
  calculateWPM,
} from "./scoring.js";

/**
 * Motor base del minijuego de tipeo.
 * Está desacoplado del UI para poder conectarlo con web, canvas o terminal.
 */
export class TypingMinigame {
  constructor({
    difficulty = "normal",
    timeLimitMs = 60000,
    random = Math.random,
  } = {}) {
    this.random = random;
    this.difficulty = difficulty;
    this.timeLimitMs = timeLimitMs;
    this.words = getWordsByDifficulty(difficulty);

    this.reset();
  }

  reset() {
    this.startedAt = null;
    this.finishedAt = null;
    this.currentWord = this.#pickWord();
    this.input = "";
    this.correctChars = 0;
    this.totalCharsTyped = 0;
    this.basePoints = 0;
    this.combo = 0;
    this.maxCombo = 0;
    this.wordsCompleted = 0;
    this.finished = false;
  }

  start(now = Date.now()) {
    if (this.startedAt !== null) return;
    this.startedAt = now;
  }

  /**
   * Recibe una tecla y actualiza el estado.
   * Soporta letras y Backspace.
   */
  handleKey(key, now = Date.now()) {
    if (this.finished) return this.getSnapshot(now);
    if (this.startedAt === null) this.start(now);

    if (this.#isTimeOver(now)) {
      this.#finish(now);
      return this.getSnapshot(now);
    }

    if (key === "Backspace") {
      this.input = this.input.slice(0, -1);
      return this.getSnapshot(now);
    }

    if (key.length !== 1) return this.getSnapshot(now);

    this.totalCharsTyped += 1;
    const expectedChar = this.currentWord[this.input.length];
    if (key === expectedChar) {
      this.correctChars += 1;
    } else {
      this.combo = 0;
    }

    this.input += key;

    if (this.input === this.currentWord) {
      this.wordsCompleted += 1;
      this.combo += 1;
      this.maxCombo = Math.max(this.maxCombo, this.combo);
      this.basePoints += this.currentWord.length * 10;
      this.currentWord = this.#pickWord();
      this.input = "";
    }

    if (this.#isTimeOver(now)) this.#finish(now);

    return this.getSnapshot(now);
  }

  getSnapshot(now = Date.now()) {
    const elapsedMs = this.#elapsed(now);
    const accuracy = calculateAccuracy(this.correctChars, this.totalCharsTyped);
    const wpm = calculateWPM(this.correctChars, elapsedMs || 1);

    return {
      startedAt: this.startedAt,
      finishedAt: this.finishedAt,
      finished: this.finished,
      difficulty: this.difficulty,
      timeLimitMs: this.timeLimitMs,
      elapsedMs,
      timeLeftMs: Math.max(0, this.timeLimitMs - elapsedMs),
      currentWord: this.currentWord,
      input: this.input,
      wordsCompleted: this.wordsCompleted,
      combo: this.combo,
      maxCombo: this.maxCombo,
      correctChars: this.correctChars,
      totalCharsTyped: this.totalCharsTyped,
      accuracy,
      wpm,
      score: calculateScore({
        basePoints: this.basePoints,
        accuracy,
        combo: this.maxCombo,
        elapsedMs,
        maxTimeMs: this.timeLimitMs,
      }),
    };
  }

  #pickWord() {
    const index = Math.floor(this.random() * this.words.length);
    return this.words[index];
  }

  #elapsed(now) {
    if (this.startedAt === null) return 0;
    const end = this.finishedAt ?? now;
    return Math.max(0, end - this.startedAt);
  }

  #isTimeOver(now) {
    if (this.startedAt === null) return false;
    return this.#elapsed(now) >= this.timeLimitMs;
  }

  #finish(now) {
    this.finished = true;
    this.finishedAt = now;
  }
}
