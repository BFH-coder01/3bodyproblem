"""Transactional single-coordinator ledger. Workers never open this database."""
from __future__ import annotations
import hashlib
from contextlib import contextmanager
import json
import math
import re
import sqlite3
import threading
import time
from pathlib import Path

PROTOCOL = 'threebody.pipeline.v1'
OUTCOMES = {'Bounded', 'Escaped', 'Close encounter', 'Numerical error', 'Unresolved'}


class LedgerError(ValueError):
    def __init__(self, message, code='invalid_request', status=400):
        super().__init__(message)
        self.code, self.status = code, status


def decimal(value, name='ordinal'):
    if not isinstance(value, str) or len(value) > 16 or not re.fullmatch(r'0|[1-9][0-9]*', value):
        raise LedgerError(f'{name} must be a canonical unsigned decimal string')
    number = int(value)
    if number > 9007199254740991:
        raise LedgerError(f'{name} exceeds this reference backend integer limit')
    return number


def integer(value, name, minimum=0, maximum=9007199254740991):
    if type(value) is not int or not minimum <= value <= maximum:
        raise LedgerError(f'{name} must be an integer in [{minimum}, {maximum}]')
    return value


def finite(value, name, minimum=None):
    try:
        valid = type(value) in (float, int) and math.isfinite(value) and (minimum is None or value >= minimum)
    except OverflowError:
        valid = False
    if not valid:
        raise LedgerError(f'{name} must be finite' + (f' and >= {minimum}' if minimum is not None else ''))
    return value


def vector(value, name, size=6):
    if not isinstance(value, list) or len(value) != size:
        raise LedgerError(f'{name} must have {size} components')
    for part in value:
        finite(part, name)
    return value


def dumps(value):
    try:
        return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)
    except (TypeError, ValueError, RecursionError) as exc:
        raise LedgerError('Value must be finite JSON') from exc


def initial_positions(radius, ordinal):
    n = math.floor((12 - 2 * radius) / radius + 1e-8) + 1
    size = n * n
    choose2 = lambda x: x * (x - 1) // 2
    choose3 = lambda x: x * (x - 1) * (x - 2) // 6
    if not 0 <= ordinal < choose3(size):
        raise LedgerError('Result ordinal outside manifest grid')
    lo, hi = 0, size - 3
    while lo < hi:
        middle = (lo + hi + 1) // 2
        if choose3(size) - choose3(size - middle) <= ordinal:
            lo = middle
        else:
            hi = middle - 1
    a = lo
    rank = ordinal - (choose3(size) - choose3(size - a))
    lo, hi = a + 1, size - 2
    while lo < hi:
        middle = (lo + hi + 1) // 2
        if choose2(size - a - 1) - choose2(size - middle) <= rank:
            lo = middle
        else:
            hi = middle - 1
    b = lo
    rank -= choose2(size - a - 1) - choose2(size - b)
    return [coordinate for cell in (a, b, b + 1 + rank)
            for coordinate in (-6 + radius + (cell % n) * radius,
                               6 - radius - (cell // n) * radius)]


def validate_result(result, experiment_id, manifest, solver_digest):
    required = {'protocol', 'experiment_id', 'trial_id', 'ordinal', 'solver_digest', 'runtime', 'engine', 'precision', 'outcome', 'time', 'initial', 'final', 'steps', 'energyError', 'minSeparation', 'orbit', 'replayEligible', 'replay'}
    if not isinstance(result, dict) or set(result) != required:
        raise LedgerError('Result fields do not match pipeline v1')
    ordinal = decimal(result['ordinal'])
    if result['protocol'] != PROTOCOL or result['experiment_id'] != experiment_id or result['trial_id'] != f'{experiment_id}:{ordinal}':
        raise LedgerError('Result identity does not match experiment')
    if result['solver_digest'] != solver_digest:
        raise LedgerError('Result solver digest does not match experiment')
    runtime = result['runtime']
    if not isinstance(runtime, dict) or set(runtime) != {'node', 'platform', 'arch'}:
        raise LedgerError('Runtime provenance must contain node, platform and arch')
    if any(not isinstance(value, str) or not 1 <= len(value) <= 128 or not value.strip() or any(ord(char) < 32 or ord(char) == 127 for char in value) for value in runtime.values()):
        raise LedgerError('Runtime provenance values must be bounded nonempty printable strings')
    if result['engine'] != 'js-baseline-v2' or result['precision'] != 'fp64':
        raise LedgerError('Unsupported engine or precision')
    outcome = result['outcome']
    if not isinstance(outcome, str) or outcome not in OUTCOMES:
        raise LedgerError('Unsupported outcome')
    duration = finite(result['time'], 'time', 0)
    if duration > manifest['duration'] + 1e-8:
        raise LedgerError('Result exceeds requested duration')
    integer(result['steps'], 'steps', 0, 2000002)
    finite(result['energyError'], 'energyError', 0)
    if result['minSeparation'] is not None:
        finite(result['minSeparation'], 'minSeparation', 0)
    for key in ('initial', 'final'):
        state = result[key]
        if not isinstance(state, dict) or set(state) != {'p', 'v'}:
            raise LedgerError(f'Malformed {key} state')
        vector(state['p'], f'{key}.p')
        vector(state['v'], f'{key}.v')
    if any(result['initial']['v']) or any(abs(x) > 6 for x in result['initial']['p']):
        raise LedgerError('Search states must start at rest inside observation square')
    if result['initial']['p'] != initial_positions(manifest['radius'], ordinal):
        raise LedgerError('Initial positions do not match manifest and ordinal')
    outside = any(abs(x) > 6 for x in result['final']['p'])
    if outcome == 'Escaped' and not outside:
        raise LedgerError('Escaped result must finish outside observation square')
    if outcome == 'Close encounter':
        p = result['final']['p']
        separation = min(math.hypot(p[2*i]-p[2*j], p[2*i+1]-p[2*j+1]) for i in range(3) for j in range(i+1,3))
        if separation >= .015:
            raise LedgerError('Close encounter must finish below close threshold')
    if outcome == 'Bounded' and (outside or abs(duration - manifest['duration']) > 1e-8):
        raise LedgerError('Bounded result must complete its requested observation')
    eligible = outcome == 'Escaped' or duration > 5
    if type(result['replayEligible']) is not bool or result['replayEligible'] != eligible:
        raise LedgerError('Replay eligibility violates display policy')
    orbit = result['orbit']
    if not isinstance(orbit, dict) or type(orbit.get('detected')) is not bool or not isinstance(orbit.get('reason'), str):
        raise LedgerError('Malformed orbit screen')
    expected_orbit = {'detected', 'reason', 'cycles', 'tolerance'}
    if orbit['detected']:
        expected_orbit |= {'period', 'maxNormalizedError'}
    if set(orbit) != expected_orbit:
        raise LedgerError('Orbit screen fields do not match baseline')
    integer(orbit.get('cycles'), 'orbit.cycles')
    finite(orbit.get('tolerance'), 'orbit.tolerance', 0)
    if orbit['tolerance'] != .02:
        raise LedgerError('Orbit tolerance must preserve baseline value 0.02')
    if orbit['detected']:
        if outcome != 'Bounded' or result['energyError'] > .001 or orbit['cycles'] != 3:
            raise LedgerError('Orbit candidate violates baseline acceptance conditions')
        period = finite(orbit.get('period'), 'orbit.period', .1)
        error = finite(orbit.get('maxNormalizedError'), 'orbit.maxNormalizedError', 0)
        if 3 * period > duration + 1e-8 or error > .02:
            raise LedgerError('Orbit candidate exceeds observed duration or recurrence tolerance')
    elif orbit['cycles'] != 0:
        raise LedgerError('Undetected orbit must report zero observed cycles')
    replay = result['replay']
    if replay is not None:
        if not eligible or not isinstance(replay, dict) or set(replay) != {'frames', 'velocityFrames'}:
            raise LedgerError('Malformed or ineligible replay')
        frames, velocities = replay['frames'], replay['velocityFrames']
        if not isinstance(frames, list) or not 1 <= len(frames) <= 1201 or not isinstance(velocities, list) or len(frames) != len(velocities):
            raise LedgerError('Replay frame counts do not match')
        previous = -1
        for frame, velocity in zip(frames, velocities):
            vector(frame, 'frame', 7)
            vector(velocity, 'velocityFrame')
            if frame[0] < previous or frame[0] < 0 or frame[0] > duration + 1e-8:
                raise LedgerError('Replay times must be ordered inside result duration')
            previous = frame[0]
        if frames[0][0] != 0 or abs(frames[-1][0] - duration) > 1e-8:
            raise LedgerError('Replay endpoints do not match result time')
        if frames[0][1:] != result['initial']['p'] or velocities[0] != result['initial']['v'] or frames[-1][1:] != result['final']['p'] or velocities[-1] != result['final']['v']:
            raise LedgerError('Replay endpoints do not match result states')
    dumps(result)
    return ordinal


class Ledger:
    def __init__(self, db, clock=time.time, lease_seconds=60):
        self.path = str(Path(db).resolve())
        self.clock = clock
        self.lease_seconds = finite(lease_seconds, 'lease_seconds', 0.001)
        self.lock = threading.RLock()
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as con:
            con.executescript('''
              PRAGMA journal_mode=WAL;
              CREATE TABLE IF NOT EXISTS experiments(
                experiment_id TEXT PRIMARY KEY, manifest TEXT NOT NULL, start INTEGER NOT NULL,
                end INTEGER NOT NULL, grid_total TEXT NOT NULL, chunk_size INTEGER NOT NULL, solver_digest TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS tasks(
                task_id TEXT PRIMARY KEY, experiment_id TEXT NOT NULL, start INTEGER NOT NULL,
                end INTEGER NOT NULL, state TEXT NOT NULL DEFAULT 'pending', epoch INTEGER NOT NULL DEFAULT 0,
                worker_id TEXT, expires_at REAL, digest TEXT, error TEXT);
              CREATE TABLE IF NOT EXISTS results(
                trial_id TEXT PRIMARY KEY, experiment_id TEXT NOT NULL, ordinal INTEGER NOT NULL,
                result TEXT NOT NULL, UNIQUE(experiment_id, ordinal));
              CREATE INDEX IF NOT EXISTS tasks_pending ON tasks(state, experiment_id, start);
            ''')

    @contextmanager
    def _connection(self):
        con = sqlite3.connect(self.path, timeout=30)
        con.row_factory = sqlite3.Row
        con.execute('PRAGMA busy_timeout=30000')
        try:
            with con:
                yield con
        finally:
            con.close()

    def add_experiment(self, descriptor, start=0, count=60, chunk_size=5):
        if not isinstance(descriptor, dict) or set(descriptor) != {'manifest', 'experiment_id', 'total', 'solver_digest'}:
            raise LedgerError('Invalid describe response')
        expid, manifest = descriptor['experiment_id'], descriptor['manifest']
        solver_digest = descriptor['solver_digest']
        if not isinstance(solver_digest, str) or not re.fullmatch('[a-f0-9]{64}', solver_digest):
            raise LedgerError('Invalid solver digest')
        if not isinstance(expid, str) or not re.fullmatch('[a-f0-9]{64}', expid):
            raise LedgerError('Invalid experiment hash')
        if not isinstance(manifest, dict) or set(manifest) != {'protocol', 'model', 'radius', 'duration', 'dt'} or manifest['protocol'] != PROTOCOL or manifest['model'] != 'point-close-stop-v1':
            raise LedgerError('Unsupported manifest')
        if not .1 <= finite(manifest['radius'], 'radius') <= 2 or not 0 < finite(manifest['duration'], 'duration') <= 300 or not 0 < finite(manifest['dt'], 'dt') <= .002:
            raise LedgerError('Manifest parameter out of range')
        total = decimal(descriptor['total'], 'total')
        start, count, chunk_size = integer(start, 'start'), integer(count, 'count', 1), integer(chunk_size, 'chunk_size', 1, 32)
        if start + count > total:
            raise LedgerError('Requested campaign exceeds grid range')
        with self.lock, self._connection() as con:
            con.execute('BEGIN IMMEDIATE')
            old = con.execute('SELECT * FROM experiments WHERE experiment_id=?', (expid,)).fetchone()
            if old:
                if (old['manifest'], old['start'], old['end'], old['chunk_size'], old['solver_digest']) != (dumps(manifest), start, start + count, chunk_size, solver_digest):
                    raise LedgerError('Experiment already exists with a different campaign', 'conflict', 409)
            else:
                con.execute('INSERT INTO experiments VALUES(?,?,?,?,?,?,?)', (expid, dumps(manifest), start, start + count, str(total), chunk_size, solver_digest))
                for begin in range(start, start + count, chunk_size):
                    end = min(begin + chunk_size, start + count)
                    con.execute('INSERT INTO tasks(task_id,experiment_id,start,end) VALUES(?,?,?,?)', (f'{expid}:{begin}-{end}', expid, begin, end))
        return next(e for e in self.status()['experiments'] if e['experiment_id'] == expid)

    def _expire(self, con, now):
        con.execute("UPDATE tasks SET state='pending',worker_id=NULL,expires_at=NULL,error='lease expired' WHERE state='running' AND expires_at<=?", (now,))

    def acquire(self, worker_id):
        if not isinstance(worker_id, str) or not 1 <= len(worker_id) <= 128:
            raise LedgerError('worker_id must be a nonempty string up to 128 characters')
        with self.lock, self._connection() as con:
            con.execute('BEGIN IMMEDIATE')
            now = self.clock()
            self._expire(con, now)
            task = con.execute("SELECT * FROM tasks WHERE state='pending' ORDER BY experiment_id,start LIMIT 1").fetchone()
            if not task:
                return None
            epoch, expiry = task['epoch'] + 1, now + self.lease_seconds
            con.execute("UPDATE tasks SET state='running',epoch=?,worker_id=?,expires_at=?,error=NULL WHERE task_id=?", (epoch, worker_id, expiry, task['task_id']))
            experiment = con.execute('SELECT manifest,solver_digest FROM experiments WHERE experiment_id=?', (task['experiment_id'],)).fetchone()
            manifest = experiment['manifest']
            return {'task_id': task['task_id'], 'experiment_id': task['experiment_id'], 'manifest': json.loads(manifest), 'start': str(task['start']), 'end': str(task['end']), 'epoch': epoch, 'worker_id': worker_id, 'expires_at': expiry, 'solver_digest': experiment['solver_digest']}

    def _task(self, con, task_id, worker_id, epoch, allow_complete=False):
        integer(epoch, 'epoch', 1)
        if not isinstance(task_id, str) or not isinstance(worker_id, str):
            raise LedgerError('task_id and worker_id must be strings')
        task = con.execute('SELECT * FROM tasks WHERE task_id=?', (task_id,)).fetchone()
        if not task:
            raise LedgerError('Unknown task', 'not_found', 404)
        if task['epoch'] != epoch or task['worker_id'] != worker_id:
            raise LedgerError('Stale lease epoch or different worker', 'stale_lease', 409)
        if task['state'] == 'complete' and allow_complete:
            return task
        if task['state'] != 'running' or task['expires_at'] <= self.clock():
            raise LedgerError('Lease expired or no longer running', 'stale_lease', 409)
        return task

    def heartbeat(self, task_id, worker_id, epoch):
        with self.lock, self._connection() as con:
            con.execute('BEGIN IMMEDIATE')
            self._task(con, task_id, worker_id, epoch)
            con.execute('UPDATE tasks SET expires_at=? WHERE task_id=?', (self.clock() + self.lease_seconds, task_id))
        return {'ok': True}

    def release(self, task_id, worker_id, epoch, error):
        with self.lock, self._connection() as con:
            con.execute('BEGIN IMMEDIATE')
            self._task(con, task_id, worker_id, epoch)
            con.execute("UPDATE tasks SET state='pending',worker_id=NULL,expires_at=NULL,error=? WHERE task_id=?", (str(error)[:1000], task_id))

    def submit(self, task_id, worker_id, epoch, results):
        if not isinstance(results, list):
            raise LedgerError('results must be a list')
        if len(dumps(results).encode()) > 16 * 1024 * 1024:
            raise LedgerError('Result payload exceeds 16 MiB', 'payload_too_large', 413)
        with self.lock, self._connection() as con:
            con.execute('BEGIN IMMEDIATE')
            task = self._task(con, task_id, worker_id, epoch, allow_complete=True)
            if len(results) != task['end'] - task['start']:
                raise LedgerError('Result count does not cover the complete task')
            experiment = con.execute('SELECT manifest,solver_digest FROM experiments WHERE experiment_id=?', (task['experiment_id'],)).fetchone()
            manifest = json.loads(experiment['manifest'])
            checked = [(validate_result(r, task['experiment_id'], manifest, experiment['solver_digest']), r) for r in results]
            checked.sort(key=lambda pair: pair[0])
            if [n for n, _ in checked] != list(range(task['start'], task['end'])):
                raise LedgerError('Result ordinals contain gaps, duplicates or out-of-range values')
            digest = hashlib.sha256(dumps([r for _, r in checked]).encode()).hexdigest()
            if task['state'] == 'complete':
                if task['digest'] != digest:
                    raise LedgerError('Completed task retry conflicts with accepted results', 'conflict', 409)
                return {'accepted': len(results), 'idempotent': True}
            for ordinal, result in checked:
                con.execute('INSERT INTO results VALUES(?,?,?,?)', (result['trial_id'], task['experiment_id'], ordinal, dumps(result)))
            con.execute("UPDATE tasks SET state='complete',digest=?,error=NULL WHERE task_id=?", (digest, task_id))
            return {'accepted': len(results), 'idempotent': False}

    def status(self):
        with self.lock, self._connection() as con:
            self._expire(con, self.clock())
            experiments = []
            for exp in con.execute('SELECT * FROM experiments ORDER BY experiment_id'):
                counts = {r['state']: r['n'] for r in con.execute('SELECT state,SUM(end-start) n FROM tasks WHERE experiment_id=? GROUP BY state', (exp['experiment_id'],))}
                accepted = con.execute('SELECT COUNT(*) FROM results WHERE experiment_id=?', (exp['experiment_id'],)).fetchone()[0]
                errors = [dict(r) for r in con.execute('SELECT task_id,error FROM tasks WHERE experiment_id=? AND error IS NOT NULL', (exp['experiment_id'],))]
                experiments.append({'experiment_id': exp['experiment_id'], 'manifest': json.loads(exp['manifest']), 'start': str(exp['start']), 'end': str(exp['end']), 'total': exp['end'] - exp['start'], 'grid_total': exp['grid_total'], 'solver_digest': exp['solver_digest'], 'accepted': accepted, 'pending': counts.get('pending', 0), 'running': counts.get('running', 0), 'errors': errors})
            return {'experiments': experiments}

    def trials(self, experiment_id, after=None, limit=50):
        integer(limit, 'limit', 1, 200)
        cursor = -1 if after is None else decimal(after, 'after')
        with self.lock, self._connection() as con:
            if not con.execute('SELECT 1 FROM experiments WHERE experiment_id=?', (experiment_id,)).fetchone():
                raise LedgerError('Unknown experiment', 'not_found', 404)
            rows = con.execute('SELECT ordinal,result FROM results WHERE experiment_id=? AND ordinal>? ORDER BY ordinal LIMIT ?', (experiment_id, cursor, limit + 1)).fetchall()
            summaries = []
            for row in rows[:limit]:
                result = json.loads(row['result'])
                result.pop('replay')
                summaries.append(result)
            return {'trials': summaries, 'next_after': str(rows[limit - 1]['ordinal']) if len(rows) > limit else None}

    def replay(self, trial_id):
        with self.lock, self._connection() as con:
            row = con.execute('SELECT result FROM results WHERE trial_id=?', (trial_id,)).fetchone()
            if not row:
                raise LedgerError('Unknown trial', 'not_found', 404)
            result = json.loads(row[0])
            if result['replay'] is None:
                raise LedgerError('Replay unavailable for this trial', 'not_found', 404)
            return result
