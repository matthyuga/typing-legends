/**
 * Utilidades de score para el minijuego de tipeo.
 */

export function calculateWPM(correctChars, elapsedMs) {
  if (elapsedMs <= 0) return 0;
  const words = correctChars / 5;
  const minutes = elapsedMs / 60000;
  return Math.round(words / minutes);
}

export function calculateAccuracy(correctChars, totalCharsTyped) {
  if (totalCharsTyped <= 0) return 100;
  const ratio = (correctChars / totalCharsTyped) * 100;
  return Math.max(0, Math.min(100, Math.round(ratio)));
}

export function calculateComboBonus(currentCombo) {
  if (currentCombo < 3) return 0;
  return Math.floor(currentCombo / 3);
}

export function calculateScore({
  basePoints,
  accuracy,
  combo,
  elapsedMs,
  maxTimeMs,
}) {
  const timeBonus = Math.max(0, Math.round(((maxTimeMs - elapsedMs) / maxTimeMs) * 50));
  const accuracyMultiplier = 1 + accuracy / 100;
  const comboBonus = calculateComboBonus(combo) * 10;

  const total = Math.round(basePoints * accuracyMultiplier + comboBonus + timeBonus);
  return Math.max(0, total);
}
