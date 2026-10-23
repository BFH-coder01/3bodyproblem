'use strict';
const assert = require('node:assert/strict');
const { spawnSync } = require('node:child_process');
const path = require('node:path');
const { createHash } = require('node:crypto');
const Reference = require('../workers/reference-cli.cjs');
const Physics = require('../baseline/dist/physics.js');
const Scan = require('../baseline/dist/scan.js');
const Orbit = require('../baseline/dist/orbit.js');
const Filter = require('../baseline/dist/replay-filter.js');

function rejects(fn, code) { assert.throws(fn, (e) => e.code === code); }
const description = Reference.describe();
assert.equal(description.total, '1794096784');
assert.equal(description.experiment_id, createHash('sha256').update(JSON.stringify(description.manifest)).digest('hex'));
assert.deepEqual(description, Reference.describe({ dt: .002, duration: 30, radius: .25, model: 'point-close-stop-v1', protocol: 'threebody.pipeline.v1' }));
assert.notEqual(description.experiment_id, Reference.describe({ duration: 29 }).experiment_id);
for (const value of [null, [], 3, 'manifest', { radius: '2' }, { radius: NaN }, { radius: Infinity }, { radius: .09 }, { radius: 2.1 }, { duration: 0 }, { duration: -1 }, { duration: 301 }, { dt: 0 }, { dt: .003 }, { dt: null }, { model: 'merge' }, { protocol: 'other' }, { extra: 1 }]) {
  rejects(() => Reference.describe(value), 'INVALID_MANIFEST');
}
for (const value of [0, -1, null, undefined, '', '00', '01', '+1', '1.0', '1e2', ' 1', '9007199254740992', '2300']) {
  rejects(() => Reference.simulate({ radius: 2 }, value), 'INVALID_ORDINAL');
}
rejects(() => Reference.simulate({ radius: 2 }, '0', 1), 'INVALID_REQUEST');

const manifest = Object.freeze({ radius: 2, duration: 6, dt: .002 });
function baseline(ordinal) {
  const sim = Physics.create(Scan.initial(manifest.radius, ordinal), { duration: manifest.duration, dt: manifest.dt });
  while (!sim.advance(20000)) {}
  return sim.result;
}
for (const ordinal of [0, 28, 57]) {
  const source = baseline(ordinal), result = Reference.simulate(manifest, String(ordinal));
  assert.equal(result.outcome, source.outcome);
  assert.equal(result.time, source.time);
  assert.equal(result.steps, source.steps);
  assert.equal(result.energyError, source.energyError);
  assert.equal(result.minSeparation, source.minSeparation);
  assert.deepEqual(result.initial, { p: source.initial.p, v: source.initial.v });
  assert(result.initial.v.every((v) => v === 0));
  assert.deepEqual(result.final, { p: source.frames.at(-1).slice(1), v: source.finalVelocity });
  assert.deepEqual(result.orbit, Orbit.analyze(source));
  assert.equal(result.replayEligible, Filter.qualifies(source));
  if (result.replayEligible) assert.deepEqual(result.replay, { frames: source.frames, velocityFrames: source.velocityFrames });
  else assert.equal(result.replay, null);
  assert.deepEqual(result, Reference.simulate(manifest, String(ordinal)));
  const noReplay = Reference.simulate(manifest, String(ordinal), false);
  assert.equal(noReplay.replay, null);
  assert.equal(noReplay.replayEligible, result.replayEligible);
  assert(!JSON.stringify(result).includes('NaN'));
}
const escaped = Reference.simulate(manifest, '57');
assert.equal(escaped.outcome, 'Escaped');
assert(escaped.time < 5 && escaped.replayEligible && escaped.replay);
const original = Reference.simulate(manifest, '28');
original.initial.p[0] = 100;
original.replay.frames[0][1] = 100;
assert.notEqual(Reference.simulate(manifest, '28').initial.p[0], 100);
assert.deepEqual(manifest, { radius: 2, duration: 6, dt: .002 });

function cli(input) {
  const run = spawnSync(process.execPath, [path.join(__dirname, '../workers/reference-cli.cjs')], { input, encoding: 'utf8', maxBuffer: 8 * 1024 * 1024 });
  assert.equal(run.status, 0, run.stderr);
  assert.equal(run.stderr, '');
  return run.stdout.trimEnd().split('\n').map((line) => JSON.parse(line));
}
const good = JSON.stringify({ op: 'describe', manifest: {} });
const invalidUTF8 = Buffer.from([0xc3, 0x28]);
const responses = cli(Buffer.concat([
  Buffer.from(`{bad}\nnull\n${JSON.stringify({ op: 'bad' })}\n${JSON.stringify({ op: 'describe', extra: 1 })}\n${' '.repeat(65537)}\n`),
  invalidUTF8, Buffer.from(`\n${good}\r\n${JSON.stringify({ op: 'simulate', manifest, ordinal: '57', replay: false })}`),
]));
assert.deepEqual(responses.slice(0, 6).map((r) => r.error.code), ['INVALID_JSON', 'INVALID_REQUEST', 'INVALID_REQUEST', 'INVALID_REQUEST', 'LINE_TOO_LARGE', 'INVALID_JSON']);
assert.deepEqual(responses[6], { ok: true, result: description });
assert.equal(responses[7].ok, true);
assert.equal(responses[7].result.replay, null);
assert.equal(responses[7].result.outcome, 'Escaped');
const boundaryLine = good + ' '.repeat(65536 - Buffer.byteLength(good));
assert.equal(cli(`${boundaryLine}\n`)[0].ok, true);
assert.equal(cli('x'.repeat(65537))[0].error.code, 'LINE_TOO_LARGE');
assert.equal(cli(`${good}\n\n${good}\n`)[1].error.code, 'INVALID_JSON');
console.log('PASS: canonical identity, strict input validation, baseline parity, stateless isolation, all-rest search, replay policy and bounded NDJSON error recovery.');
