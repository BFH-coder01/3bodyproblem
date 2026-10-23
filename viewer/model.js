(function (root) {
  'use strict';
  function eligible(trial) {
    return Number.isFinite(trial?.time) && trial.time >= 0 &&
      (trial.outcome === 'Escaped' || trial.time > 5);
  }
  function testNumber(ordinal) {
    return (BigInt(ordinal) + 1n).toString();
  }
  function positionAt(frames, time) {
    if (!frames.length) return null;
    if (time <= frames[0][0]) return frames[0].slice(1);
    if (time >= frames.at(-1)[0]) return frames.at(-1).slice(1);
    let low = 0, high = frames.length - 1;
    while (low + 1 < high) {
      const middle = (low + high) >>> 1;
      if (frames[middle][0] <= time) low = middle;
      else high = middle;
    }
    const fraction = (time - frames[low][0]) / (frames[high][0] - frames[low][0] || 1);
    return frames[low].slice(1).map((value, index) =>
      value + fraction * (frames[high][index + 1] - value));
  }
  function reconcileScan(cursor, complete, accepted, knownCount) {
    // Distributed workers may publish earlier ordinals after we reached the end.
    // A cursor-only tail poll cannot discover those results. Restart a completed
    // scan when coverage proves there are unknown rows, retaining the known map
    // so already observed replays stay available throughout the bounded rescan.
    if (complete && accepted > knownCount) return { cursor: null, complete: false };
    return { cursor, complete };
  }
  const api = { eligible, testNumber, positionAt, reconcileScan };
  if (typeof module !== 'undefined') module.exports = api;
  else root.ReplayModel = api;
})(typeof globalThis === 'undefined' ? this : globalThis);
