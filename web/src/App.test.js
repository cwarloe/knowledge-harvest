import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import KnowledgeHarvestApp from './App';

global.IS_REACT_ACT_ENVIRONMENT = true;

describe('screen recording duration and cleanup', () => {
  let root;
  let container;
  let recorder;
  let track;

  const button = (label) => Array.from(container.querySelectorAll('button'))
    .find((candidate) => candidate.textContent.trim() === label);

  const click = async (label) => {
    const target = button(label);
    expect(target).toBeDefined();
    await act(async () => {
      target.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    });
  };

  beforeEach(async () => {
    jest.useFakeTimers();
    global.fetch = jest.fn().mockResolvedValue({ ok: true, json: async () => [] });
    track = { stop: jest.fn() };
    Object.defineProperty(navigator, 'mediaDevices', {
      configurable: true,
      value: { getDisplayMedia: jest.fn().mockResolvedValue({ getTracks: () => [track] }) }
    });

    recorder = {
      state: 'inactive',
      start: jest.fn(() => { recorder.state = 'recording'; }),
      stop: jest.fn(() => {
        recorder.state = 'inactive';
        recorder.onstop();
      }),
      pause: jest.fn(() => { recorder.state = 'paused'; }),
      resume: jest.fn(() => { recorder.state = 'recording'; })
    };
    global.MediaRecorder = jest.fn(() => recorder);

    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);
    await act(async () => { root.render(<KnowledgeHarvestApp />); });
    await click('Record');
    await click('Start Recording');
  });

  afterEach(async () => {
    await act(async () => { root.unmount(); });
    container.remove();
    jest.useRealTimers();
    jest.restoreAllMocks();
  });

  it('stops automatically at 15 minutes and opens recording details', async () => {
    await act(async () => { jest.advanceTimersByTime(899000); });
    expect(recorder.stop).not.toHaveBeenCalled();
    expect(container.textContent).toContain('14:59');

    await act(async () => { jest.advanceTimersByTime(1000); });
    expect(recorder.stop).toHaveBeenCalledTimes(1);
    expect(track.stop).toHaveBeenCalled();
    expect(container.textContent).toContain('Add Recording Details');
  });

  it('does not charge paused time against the 15-minute limit', async () => {
    await act(async () => { jest.advanceTimersByTime(30000); });
    await click('Pause');
    await act(async () => { jest.advanceTimersByTime(3600000); });
    expect(recorder.stop).not.toHaveBeenCalled();
    expect(container.textContent).toContain('0:30');

    await click('Resume');
    await act(async () => { jest.advanceTimersByTime(869000); });
    expect(recorder.stop).not.toHaveBeenCalled();
    await act(async () => { jest.advanceTimersByTime(1000); });
    expect(recorder.stop).toHaveBeenCalledTimes(1);
  });

  it('reliably stops immediately when requested, without stale state', async () => {
    await click('Stop Recording');
    expect(recorder.stop).toHaveBeenCalledTimes(1);
    expect(track.stop).toHaveBeenCalled();
    await act(async () => { jest.advanceTimersByTime(901000); });
    expect(recorder.stop).toHaveBeenCalledTimes(1);
  });

  it('uses elapsed active time even if background timers were throttled', async () => {
    // Jump the system clock without delivering 900 interval callbacks.
    jest.setSystemTime(Date.now() + 900000);
    await act(async () => { jest.advanceTimersByTime(1000); });
    expect(recorder.stop).toHaveBeenCalledTimes(1);
  });

  it('cleans up when the browser ends recording itself', async () => {
    await act(async () => {
      recorder.state = 'inactive';
      recorder.onstop();
    });
    expect(track.stop).toHaveBeenCalled();
    expect(container.textContent).toContain('Add Recording Details');
    await act(async () => { jest.advanceTimersByTime(901000); });
    expect(recorder.stop).not.toHaveBeenCalled();
  });
});
