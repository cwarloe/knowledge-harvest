// PostgreSQL INTERVAL treats a two-field `8:42` as 8 hours 42 minutes,
// not the 8 minutes 42 seconds shown by the recording clock. Use explicit
// units when sending new values; do not guess how old rows were entered.
export function durationForUpload(seconds) {
  if (!Number.isInteger(seconds) || seconds < 0 || seconds > 900) return null;
  return `${seconds} seconds`;
}

// The pg driver returns INTERVAL values as objects, not necessarily strings.
// Display the *stored* duration without silently rewriting legacy records.
export function durationLabel(duration) {
  if (typeof duration === 'string') return duration || 'Unknown';
  if (!duration || typeof duration !== 'object') return 'Unknown';
  if (duration.years || duration.months) return 'Unknown';

  const fields = ['days', 'hours', 'minutes', 'seconds'];
  if (!fields.some((key) => Object.prototype.hasOwnProperty.call(duration, key))) {
    return 'Unknown';
  }
  const parts = fields.map((key) => duration[key] ?? 0);
  if (parts.some((part) => typeof part !== 'number' || !Number.isFinite(part) || part < 0)) {
    return 'Unknown';
  }
  const [days, hours, minutes, seconds] = parts;
  const totalSeconds = Math.round(days * 86400 + hours * 3600 + minutes * 60 + seconds);
  return `${Math.floor(totalSeconds / 60)}:${String(totalSeconds % 60).padStart(2, '0')}`;
}
