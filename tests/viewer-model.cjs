'use strict';
const assert = require('node:assert/strict');
const { eligible, testNumber, positionAt, reconcileScan } = require('../viewer/model.js');

// Physical-time policy includes short escapes, but excludes the exact 5 s boundary.
for (const time of [0, .2, 5, 20]) assert(eligible({outcome: 'Escaped', time}));
for (const outcome of ['Bounded', 'Close encounter', 'Numerical error', 'Unresolved']) {
  assert.equal(eligible({outcome, time: 5}), false);
  assert.equal(eligible({outcome, time: 5.000001}), true);
}
for (const time of [-1, NaN, Infinity, undefined]) assert.equal(eligible({outcome: 'Escaped', time}), false);
assert.equal(testNumber('9007199254740992'), '9007199254740993');

// Recorded irregular sampling is interpolated, never integrated or extrapolated.
const frames = [[0, 0, 1, 2, 3, 4, 5], [.3, 3, 4, 5, 6, 7, 8], [2, 20, 21, 22, 23, 24, 25]];
assert.deepEqual(positionAt(frames, -.1), [0, 1, 2, 3, 4, 5]);
assert.deepEqual(positionAt(frames, .15), [1.5, 2.5, 3.5, 4.5, 5.5, 6.5]);
assert.deepEqual(positionAt(frames, .3), [3, 4, 5, 6, 7, 8]);
assert.deepEqual(positionAt(frames, 20), [20, 21, 22, 23, 24, 25]);
assert.equal(positionAt([], 1), null);
assert.deepEqual(frames[0], [0, 0, 1, 2, 3, 4, 5]);
console.log('PASS: replay eligibility boundaries, large ordinal labels, irregular frame interpolation and endpoint clamping.');

// A distributed worker publishes ordinal 100 after the scanner reached 999.
// It is outside the visible first page and below the old scan cursor. Exercise
// the exclusive-cursor pagination shape used by the API, not only a state flag.
const published = Array.from({length: 1000}, (_, ordinal) => ({
  ordinal: String(ordinal), trial_id: `experiment:${ordinal}`,
  outcome: ordinal === 100 ? 'Escaped' : 'Close encounter', time: .2
}));
const known = new Map(published.filter(row => row.ordinal !== '100').map(row => [row.trial_id, row]));
let scan = reconcileScan('999', true, published.length, known.size);
assert.deepEqual(scan, {cursor: null, complete: false});
let pages = 0;
while (!scan.complete) {
  const rows = published.filter(row => scan.cursor === null || BigInt(row.ordinal) > BigInt(scan.cursor)).slice(0, 200);
  for (const row of rows) known.set(row.trial_id, row);
  scan = {cursor: rows.at(-1)?.ordinal ?? scan.cursor, complete: rows.length < 200 || rows.at(-1)?.ordinal === '999'};
  assert(++pages <= 6, 'the rescan must remain finite');
}
assert(eligible(known.get('experiment:100')), 'late earlier escape must enter the replay playlist');
assert.deepEqual(reconcileScan(scan.cursor, true, published.length, known.size), scan,
  'complete coverage must not repeatedly restart the scan');
assert.deepEqual(reconcileScan('199', false, 1001, 200), {cursor:'199', complete:false},
  'coverage growth must not continually reset an ongoing bounded scan');
console.log('PASS: late out-of-order arrival below a completed cursor is discovered without endless or mid-scan resets.');
