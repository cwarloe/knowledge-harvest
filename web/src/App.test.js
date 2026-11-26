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

  it('keeps the previous session active until delayed onstop finalizes its chunks', async () => {
    // In real browsers stop() returns before the final dataavailable/onstop.
    recorder.stop.mockImplementation(() => { recorder.state = 'inactive'; });
    await click('Stop Recording');

    expect(button('Start Recording')).toBeUndefined();
    expect(button('Stop Recording')).toBeDefined();
    await click('Stop Recording');
    expect(recorder.stop).toHaveBeenCalledTimes(1);

    await act(async () => {
      recorder.ondataavailable({ data: new Blob(['synthetic-final-chunk']) });
      recorder.onstop();
    });
    expect(container.textContent).toContain('Add Recording Details');
  });

  it('does not request screen access twice while permission is pending', async () => {
    await click('Stop Recording');
    await click('Cancel');
    let releaseCapture;
    const capturePending = new Promise((resolve) => { releaseCapture = resolve; });
    navigator.mediaDevices.getDisplayMedia.mockImplementation(() => capturePending);

    await click('Start Recording');
    await click('Start Recording');
    // One initial capture, one new capture; no second browser permission prompt.
    expect(navigator.mediaDevices.getDisplayMedia).toHaveBeenCalledTimes(2);
    await act(async () => { releaseCapture({ getTracks: () => [track] }); });
    expect(container.textContent).toContain('Stop Recording');
  });

  it('ignores a stale stop callback after the next session has started', async () => {
    const firstOnStop = recorder.onstop;
    await click('Stop Recording');
    await click('Cancel');

    const nextTrack = { stop: jest.fn() };
    navigator.mediaDevices.getDisplayMedia.mockResolvedValue({ getTracks: () => [nextTrack] });
    const nextRecorder = {
      state: 'inactive',
      start: jest.fn(function () { this.state = 'recording'; }),
      stop: jest.fn(function () { this.state = 'inactive'; this.onstop(); }),
      pause: jest.fn(function () { this.state = 'paused'; }),
      resume: jest.fn(function () { this.state = 'recording'; })
    };
    global.MediaRecorder.mockImplementation(() => nextRecorder);
    await click('Start Recording');

    await act(async () => { firstOnStop(); });
    expect(button('Stop Recording')).toBeDefined();
    expect(container.textContent).not.toContain('Add Recording Details');
    expect(nextTrack.stop).not.toHaveBeenCalled();

    await click('Stop Recording');
    expect(nextRecorder.stop).toHaveBeenCalledTimes(1);
    expect(nextTrack.stop).toHaveBeenCalled();
  });
});
