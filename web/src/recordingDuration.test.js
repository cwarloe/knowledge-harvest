import { durationForUpload, durationLabel } from './recordingDuration';

describe('PostgreSQL recording duration contract', () => {
  it('encodes 8:42 as 522 seconds rather than ambiguous 8:42', () => {
    expect(durationForUpload(8 * 60 + 42)).toBe('522 seconds');
    expect(durationForUpload(900)).toBe('900 seconds');
  });

  it('does not invent a duration from invalid elapsed time', () => {
    [-1, 901, 20.3, NaN, undefined, '32'].forEach((value) => {
      expect(durationForUpload(value)).toBeNull();
    });
  });

  it('renders parsed interval objects accurately', () => {
    expect(durationLabel({ minutes: 8, seconds: 42 })).toBe('8:42');
    expect(durationLabel({ hours: 1, minutes: 2, seconds: 3 })).toBe('62:03');
    expect(durationLabel({ seconds: 0 })).toBe('0:00');
  });

  it('retains existing string representations without retroactive reinterpretation', () => {
    expect(durationLabel('8:42')).toBe('8:42');
    expect(durationLabel(null)).toBe('Unknown');
    expect(durationLabel({})).toBe('Unknown');
    expect(durationLabel({ unexpected: 'x' })).toBe('Unknown');
    expect(durationLabel({ months: 1 })).toBe('Unknown');
    expect(durationLabel({ seconds: -1 })).toBe('Unknown');
  });
});
