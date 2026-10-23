'use strict';

// Stateless reference adapter. Scientific behavior remains in the pinned baseline.
const { createHash } = require('node:crypto');
const { readFileSync } = require('node:fs');
const { resolve } = require('node:path');
const Physics = require('../baseline/dist/physics.js');
const Scan = require('../baseline/dist/scan.js');
const Orbit = require('../baseline/dist/orbit.js');
const ReplayFilter = require('../baseline/dist/replay-filter.js');

const PROTOCOL = 'threebody.pipeline.v1';
const MODEL = 'point-close-stop-v1';
const MAX_LINE_BYTES = 64 * 1024;
// Normalize checkout line endings, then frame paths and bytes unambiguously.
const sourceHash = createHash('sha256');
for (const path of ['workers/reference-cli.cjs', 'baseline/dist/physics.js', 'baseline/dist/scan.js', 'baseline/dist/orbit.js', 'baseline/dist/replay-filter.js']) {
  const content = readFileSync(resolve(__dirname, '..', path), 'utf8').replace(/\r\n/g, '\n');
  sourceHash.update(`${path}\0${Buffer.byteLength(content)}\0`);
  sourceHash.update(content);
}
const SOLVER_DIGEST = sourceHash.digest('hex');

function fail(code, message) {
  const error = new Error(message);
  error.code = code;
  throw error;
}

function object(value, code, label) {
  if (value === null || typeof value !== 'object' || Array.isArray(value) ||
      ![Object.prototype, null].includes(Object.getPrototypeOf(value))) {
    fail(code, `${label} must be an object`);
  }
}

function keys(value, allowed, code, label) {
  for (const key of Object.keys(value)) {
    if (!allowed.includes(key)) fail(code, `Unknown ${label} field: ${key}`);
  }
}

function normalizeManifest(input = {}) {
  object(input, 'INVALID_MANIFEST', 'Manifest');
  keys(input, ['protocol', 'model', 'radius', 'duration', 'dt'], 'INVALID_MANIFEST', 'manifest');
  const manifest = {
    protocol: Object.hasOwn(input, 'protocol') ? input.protocol : PROTOCOL,
    model: Object.hasOwn(input, 'model') ? input.model : MODEL,
    radius: Object.hasOwn(input, 'radius') ? input.radius : 0.25,
    duration: Object.hasOwn(input, 'duration') ? input.duration : 30,
    dt: Object.hasOwn(input, 'dt') ? input.dt : 0.002,
  };
  if (manifest.protocol !== PROTOCOL || manifest.model !== MODEL) {
    fail('INVALID_MANIFEST', 'Unsupported protocol or physical model');
  }
  for (const key of ['radius', 'duration', 'dt']) {
    if (typeof manifest[key] !== 'number' || !Number.isFinite(manifest[key])) {
      fail('INVALID_MANIFEST', `${key} must be a finite number`);
    }
  }
  if (manifest.radius < 0.1 || manifest.radius > 2) fail('INVALID_MANIFEST', 'Radius must be between 0.1 and 2 metres');
  if (manifest.duration <= 0 || manifest.duration > 300) fail('INVALID_MANIFEST', 'Duration must be greater than zero and at most 300 seconds');
  if (manifest.dt <= 0 || manifest.dt > 0.002) fail('INVALID_MANIFEST', 'Timestep must be greater than zero and at most 0.002 seconds');
  return manifest;
}

function describe(input = {}) {
  const manifest = normalizeManifest(input);
  const experiment_id = createHash('sha256').update(JSON.stringify(manifest), 'utf8').digest('hex');
  return { manifest, experiment_id, solver_digest: SOLVER_DIGEST, total: String(Scan.spec(manifest.radius).total) };
}

function checkedOrdinal(value, total) {
  if (typeof value !== 'string' || !/^(0|[1-9][0-9]*)$/.test(value)) {
    fail('INVALID_ORDINAL', 'Ordinal must be a canonical unsigned decimal string');
  }
  const ordinal = Number(value);
  if (!Number.isSafeInteger(ordinal) || ordinal >= Number(total)) {
    fail('INVALID_ORDINAL', 'Ordinal is outside the configured grid');
  }
  return ordinal;
}

function finiteTree(value) {
  if (typeof value === 'number' && !Number.isFinite(value)) return false;
  if (Array.isArray(value)) return value.every(finiteTree);
  if (value !== null && typeof value === 'object') return Object.values(value).every(finiteTree);
  return true;
}

function simulate(input, ordinal, replay = true) {
  const { manifest, experiment_id, total } = describe(input);
  const index = checkedOrdinal(ordinal, total);
  if (typeof replay !== 'boolean') fail('INVALID_REQUEST', 'Replay must be boolean');
  const initial = Scan.initial(manifest.radius, index);
  const simulation = Physics.create(initial, { duration: manifest.duration, dt: manifest.dt });
  while (!simulation.advance(20000)) { /* Work budget does not change solver steps. */ }
  const record = simulation.result;
  const replayEligible = ReplayFilter.qualifies(record);
  const result = {
    protocol: PROTOCOL,
    experiment_id,
    trial_id: `${experiment_id}:${ordinal}`,
    ordinal,
    engine: 'js-baseline-v2',
    solver_digest: SOLVER_DIGEST,
    runtime: { node: process.version, platform: process.platform, arch: process.arch },
    precision: 'fp64',
    outcome: record.outcome,
    time: record.time,
    initial: { p: record.initial.p.slice(), v: record.initial.v.slice() },
    final: { p: record.frames.at(-1).slice(1), v: record.finalVelocity.slice() },
    steps: record.steps,
    energyError: record.energyError,
    minSeparation: Number.isFinite(record.minSeparation) ? record.minSeparation : null,
    orbit: Orbit.analyze(record),
    replayEligible,
    replay: replay && replayEligible ? {
      frames: record.frames,
      velocityFrames: record.velocityFrames,
    } : null,
  };
  if (!finiteTree(result)) fail('SIMULATION_ERROR', 'Reference solver produced a nonfinite value');
  return result;
}

function dispatch(request) {
  object(request, 'INVALID_REQUEST', 'Request');
  if (request.op === 'describe') {
    keys(request, ['op', 'manifest'], 'INVALID_REQUEST', 'request');
    return describe(request.manifest);
  }
  if (request.op === 'simulate') {
    keys(request, ['op', 'manifest', 'ordinal', 'replay'], 'INVALID_REQUEST', 'request');
    return simulate(request.manifest, request.ordinal, request.replay);
  }
  fail('INVALID_REQUEST', 'Unknown operation');
}

function main(input = process.stdin, output = process.stdout) {
  // Bound retained bytes even for a line much larger than the protocol limit.
  let chunks = [], length = 0, oversized = false;
  function write(response) { output.write(`${JSON.stringify(response)}\n`); }
  function finish() {
    if (oversized) {
      write({ ok: false, error: { code: 'LINE_TOO_LARGE', message: 'Input line exceeds 64 KiB' } });
    } else {
      let request;
      try {
        const bytes = Buffer.concat(chunks, length);
        const text = new TextDecoder('utf-8', { fatal: true }).decode(bytes);
        request = JSON.parse(text);
      } catch {
        write({ ok: false, error: { code: 'INVALID_JSON', message: 'Input line must contain valid UTF-8 JSON' } });
        chunks = []; length = 0; oversized = false;
        return;
      }
      try { write({ ok: true, result: dispatch(request) }); }
      catch (error) {
        const known = ['INVALID_MANIFEST', 'INVALID_ORDINAL', 'INVALID_REQUEST', 'SIMULATION_ERROR'].includes(error.code);
        write({ ok: false, error: { code: known ? error.code : 'SIMULATION_ERROR', message: known ? error.message : 'Reference operation failed' } });
      }
    }
    chunks = []; length = 0; oversized = false;
  }
  function append(bytes) {
    if (oversized) return;
    if (length + bytes.length > MAX_LINE_BYTES) { oversized = true; chunks = []; length = 0; }
    else { chunks.push(bytes); length += bytes.length; }
  }
  input.on('data', (chunk) => {
    const bytes = Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk);
    let start = 0, newline;
    while ((newline = bytes.indexOf(10, start)) !== -1) {
      append(bytes.subarray(start, newline)); finish(); start = newline + 1;
    }
    if (start < bytes.length) append(bytes.subarray(start));
  });
  input.on('end', () => { if (oversized || length > 0) finish(); });
}

module.exports = { describe, simulate };
if (require.main === module) main();
