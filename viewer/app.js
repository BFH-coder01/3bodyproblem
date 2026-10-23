/* Read-only replay client. Physical integration runs exclusively in workers. */
'use strict';
(() => {
  const $ = id => document.getElementById(id);
  const M = window.ReplayModel;
  const colors = ['#ff6577', '#8bea9c', '#67adff'];
  const state = {
    experiment: '', generation: 0, cursors: [null], page: 0, nextPage: null,
    known: new Map(), scanCursor: null, scanComplete: false,
    selected: null, replay: null, time: 0, playing: true, busy: false,
    loadingNext: false, selection: 0, pageRequest: 0, refreshBusy: false, nextAt: 0
  };

  function notice(message, error = false) {
    $('notice').textContent = message;
    $('notice').classList.toggle('error', error);
  }
  async function api(path) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 10000);
    try {
      const response = await fetch(path, { headers: { Accept: 'application/json' }, cache: 'no-store', signal: controller.signal });
      let body;
      try { body = await response.json(); }
      catch (_) { throw new Error(`Coordinator returned an invalid response (${response.status}).`); }
      if (!response.ok) throw new Error(body?.error?.message || `Request failed (${response.status}).`);
      return body;
    } catch (error) {
      if (error.name === 'AbortError') throw new Error('Coordinator request timed out.');
      throw error;
    } finally { clearTimeout(timeout); }
  }
  function format(value, digits = 2) { return Number.isFinite(value) ? value.toFixed(digits) : '—'; }
  function coordinates(p) {
    return p ? ['R', 'G', 'B'].map((name, i) => `${name} (${format(p[i * 2])}, ${format(p[i * 2 + 1])})`).join('\n') : '—';
  }
  function outcome(trial) {
    return trial?.orbit?.detected ? 'Orbit candidate' : trial?.outcome || 'Ready';
  }
  function outcomeClass(trial) {
    return trial?.orbit?.detected ? 'candidate' : trial?.outcome === 'Escaped' ? 'escaped' : '';
  }
  function remember(rows) {
    for (const row of rows) state.known.set(row.trial_id, row);
  }
  function orderedEligible() {
    return [...state.known.values()].filter(M.eligible).sort((a, b) =>
      BigInt(a.ordinal) < BigInt(b.ordinal) ? -1 : BigInt(a.ordinal) > BigInt(b.ordinal) ? 1 : 0);
  }
  function trialsURL(cursor, limit = 50) {
    const query = new URLSearchParams({ experiment_id: state.experiment, limit: String(limit) });
    if (cursor !== null && cursor !== undefined) query.set('after', cursor);
    return `/v1/trials?${query}`;
  }

  function updateMetrics(experiment) {
    const accepted = Number(experiment?.accepted || 0), total = Number(experiment?.total || 0);
    $('accepted').textContent = accepted.toLocaleString();
    $('total').textContent = total.toLocaleString();
    $('remaining').textContent = Math.max(0, total - accepted).toLocaleString();
    $('progress').style.width = `${total ? Math.min(100, accepted / total * 100) : 0}%`;
  }

  function drawState(canvas, positions, frames = null, time = Infinity, thumbnail = false) {
    const bounds = canvas.getBoundingClientRect();
    const ratio = Math.min(window.devicePixelRatio || 1, 2);
    const width = Math.max(1, bounds.width), height = Math.max(1, bounds.height);
    if (canvas.width !== Math.round(width * ratio) || canvas.height !== Math.round(height * ratio)) {
      canvas.width = Math.round(width * ratio); canvas.height = Math.round(height * ratio);
    }
    const context = canvas.getContext('2d');
    context.setTransform(ratio, 0, 0, ratio, 0, 0);
    context.clearRect(0, 0, width, height);
    const padding = thumbnail ? 5 : 25;
    const side = Math.min(width, height) - padding * 2;
    const extent = thumbnail && positions ? Math.max(6.5, ...positions.map(Math.abs)) * 1.04 : 6.65;
    const scale = side / (extent * 2);
    const point = (x, y) => [width / 2 + x * scale, height / 2 - y * scale];
    const corner = point(-6, 6);
    context.strokeStyle = thumbnail ? '#32464e' : '#293d45';
    context.lineWidth = 1;
    context.strokeRect(corner[0], corner[1], 12 * scale, 12 * scale);
    if (!thumbnail) {
      context.strokeStyle = '#1a2c34';
      for (let value = -4; value <= 4; value += 2) {
        let a = point(value, -6), b = point(value, 6);
        context.beginPath(); context.moveTo(...a); context.lineTo(...b); context.stroke();
        a = point(-6, value); b = point(6, value);
        context.beginPath(); context.moveTo(...a); context.lineTo(...b); context.stroke();
      }
      context.fillStyle = '#66808a'; context.font = '9px ui-monospace, monospace';
      context.fillText('−6', corner[0] - 7, corner[1] + 12 * scale + 16);
      context.fillText('+6 m', corner[0] + 12 * scale - 23, corner[1] + 12 * scale + 16);
    }
    if (!positions) return;
    for (let body = 0; body < 3; body++) {
      context.strokeStyle = colors[body]; context.lineWidth = 1.35; context.globalAlpha = .6;
      if (frames) {
        context.beginPath();
        for (let index = 0; index < frames.length && frames[index][0] <= time; index++) {
          const p = point(frames[index][body * 2 + 1], frames[index][body * 2 + 2]);
          if (!index) context.moveTo(...p); else context.lineTo(...p);
        }
        context.lineTo(...point(positions[body * 2], positions[body * 2 + 1])); context.stroke();
      }
      context.globalAlpha = 1;
      const p = point(positions[body * 2], positions[body * 2 + 1]);
      context.fillStyle = colors[body];
      if (!thumbnail) { context.shadowColor = colors[body]; context.shadowBlur = 12; }
      context.beginPath(); context.arc(...p, thumbnail ? 2.2 : 4.5, 0, Math.PI * 2); context.fill();
      context.shadowBlur = 0;
    }
  }

  function showInspector(trial) {
    $('trial-label').textContent = `TEST ${M.testNumber(trial.ordinal)} / RECORDED MOTION`;
    $('selected-title').textContent = `Test ${M.testNumber(trial.ordinal)}`;
    $('outcome').textContent = outcome(trial);
    $('outcome').className = `badge ${outcomeClass(trial)}`;
    $('selected-note').textContent = trial.orbit?.detected ?
      'A recurrence candidate. Further numerical verification is required.' :
      'Three equal point masses, initially at rest. Position and time are recorded by the worker.';
    $('duration').textContent = `${format(trial.time, 3)} s`;
    $('steps').textContent = Number(trial.steps).toLocaleString();
    $('energy').textContent = Number.isFinite(trial.energyError) ? `${(trial.energyError * 100).toPrecision(3)}%` : '—';
    $('retention').textContent = M.eligible(trial) ? 'Eligible' : 'Short interaction';
    $('initial-positions').textContent = coordinates(trial.initial?.p);
    $('final-positions').textContent = coordinates(trial.final?.p);
    $('stage-empty').hidden = true;
    for (const row of $('trials').rows) row.classList.toggle('selected', row.dataset.id === trial.trial_id);
  }

  async function selectTrial(trial) {
    const token = ++state.selection, generation = state.generation;
    state.selected = trial; state.replay = null; state.time = 0; state.nextAt = Infinity; state.busy = true;
    showInspector(trial); $('scrub').disabled = true;
    if (!M.eligible(trial)) {
      state.busy = false; state.time = trial.time; state.nextAt = performance.now() + 5000;
      $('trial-label').textContent = `TEST ${M.testNumber(trial.ordinal)} / FINAL RECORDED STATE`;
      $('selected-note').textContent = 'Final recorded state. This interaction lasted no more than five seconds and did not escape, so no automatic replay was retained.';
      $('retention').textContent = 'Final state only';
      return;
    }
    $('retention').textContent = 'Loading…';
    try {
      const full = await api(`/v1/trials/${encodeURIComponent(trial.trial_id)}/replay`);
      if (token !== state.selection || generation !== state.generation) return;
      if (!full.replay?.frames?.length) throw new Error('This trial has no retained replay.');
      state.replay = full.replay;
      state.nextAt = 0;
      $('scrub').max = String(trial.time || 1); $('scrub').value = '0'; $('scrub').disabled = false;
      $('retention').textContent = `${full.replay.frames.length.toLocaleString()} frames`;
    } catch (error) {
      if (token !== state.selection || generation !== state.generation) return;
      $('retention').textContent = 'Unavailable';
      $('selected-note').textContent = `${error.message} The final state remains visible.`;
      state.nextAt = performance.now() + 2000;
    } finally { if (token === state.selection) state.busy = false; }
  }

  function renderRows(rows) {
    const body = $('trials'); body.replaceChildren();
    if (!rows.length) {
      const row = body.insertRow(), cell = row.insertCell();
      cell.colSpan = 6; cell.className = 'table-empty';
      cell.textContent = 'No accepted trials on this page yet. Results appear when workers publish them.';
    }
    for (const trial of rows) {
      const row = body.insertRow(); row.dataset.id = trial.trial_id;
      row.classList.toggle('selected', state.selected?.trial_id === trial.trial_id);
      row.insertCell().textContent = `#${M.testNumber(trial.ordinal)}`;
      const initial = row.insertCell(); initial.className = 'positions'; initial.textContent = coordinates(trial.initial?.p);
      const result = document.createElement('span'); result.className = `outcome-name ${outcomeClass(trial)}`;
      result.textContent = outcome(trial); row.insertCell().append(result);
      row.insertCell().textContent = `${format(trial.time, 3)} s`;
      const canvas = document.createElement('canvas'); canvas.className = 'thumbnail';
      canvas.setAttribute('aria-label', `Final frame of test ${M.testNumber(trial.ordinal)}`);
      row.insertCell().append(canvas);
      const button = document.createElement('button'); button.type = 'button'; button.className = 'button row-button';
      button.textContent = M.eligible(trial) ? 'View replay' : 'Inspect state';
      button.setAttribute('aria-label', `${button.textContent} for test ${M.testNumber(trial.ordinal)}`);
      button.addEventListener('click', () => {
        if (!M.eligible(trial)) {
          state.playing = false; $('play').textContent = 'Play'; $('play').setAttribute('aria-pressed', 'false');
        }
        selectTrial(trial);
      }); row.insertCell().append(button);
      drawState(canvas, trial.final?.p, null, Infinity, true);
    }
    $('previous-page').disabled = state.page === 0;
    $('next-page').disabled = state.nextPage === null;
    $('page-label').textContent = `Page ${state.page + 1} · ${rows.length} accepted trials`;
  }

  async function loadPage() {
    if (!state.experiment) return;
    const generation = state.generation, page = state.page, request = ++state.pageRequest;
    $('previous-page').disabled = true; $('next-page').disabled = true;
    try {
      const data = await api(trialsURL(state.cursors[page]));
      if (generation !== state.generation || page !== state.page || request !== state.pageRequest) return;
      state.nextPage = data.next_after ?? null;
      remember(data.trials);
      renderRows(data.trials);
      if (!state.selected && orderedEligible().length) await selectTrial(orderedEligible()[0]);
    } finally {
      if (generation === state.generation && request === state.pageRequest) {
        $('previous-page').disabled = state.page === 0; $('next-page').disabled = state.nextPage === null;
      }
    }
  }

  async function nextReplay() {
    if (state.loadingNext || state.busy || !state.experiment) return;
    state.loadingNext = true;
    const generation = state.generation;
    try {
      let list = orderedEligible();
      let index = list.findIndex(row => row.trial_id === state.selected?.trial_id);
      if (index >= 0 && index + 1 < list.length) return await selectTrial(list[index + 1]);
      if (index === -1 && list.length) return await selectTrial(list[0]);
      // Bound each scan to three pages so a campaign of short trials cannot block the UI.
      for (let page = 0; page < 3 && !state.scanComplete; page++) {
        const data = await api(trialsURL(state.scanCursor, 200));
        if (generation !== state.generation) return;
        remember(data.trials);
        if (data.trials.length) state.scanCursor = data.trials.at(-1).ordinal;
        state.scanComplete = data.next_after === null || data.next_after === undefined;
        list = orderedEligible(); index = list.findIndex(row => row.trial_id === state.selected?.trial_id);
        if (index + 1 < list.length) return await selectTrial(list[index + 1]);
      }
      if (state.scanComplete && list.length) await selectTrial(list[0]);
      else state.nextAt = performance.now() + 1500;
    } catch (error) {
      if (generation === state.generation) { notice(`Replay playlist: ${error.message}`, true); state.nextAt = performance.now() + 5000; }
    } finally { state.loadingNext = false; }
  }

  async function refresh(quiet = false) {
    if (state.refreshBusy) return;
    state.refreshBusy = true; $('refresh').disabled = true;
    const startingGeneration = state.generation;
    if (!quiet) notice('Refreshing coordinator results…');
    try {
      const data = await api('/v1/experiments');
      if (startingGeneration !== state.generation) return;
      const experiments = data.experiments || [];
      const chosen = experiments.find(item => item.experiment_id === state.experiment) || experiments[0];
      $('experiment').replaceChildren();
      for (const experiment of experiments) {
        const option = document.createElement('option'); option.value = experiment.experiment_id;
        option.textContent = `r ${experiment.manifest.radius} m · ${experiment.manifest.duration} s · ${experiment.experiment_id.slice(0, 8)}`;
        $('experiment').append(option);
      }
      if (!chosen) {
        const option = document.createElement('option'); option.textContent = 'No experiments yet'; option.value = '';
        $('experiment').append(option); updateMetrics(null); renderRows([]);
        notice('No campaign configured. Initialize a campaign, then start local or remote CPU workers.');
        return;
      }
      if (chosen.experiment_id !== state.experiment) resetExperiment(chosen.experiment_id);
      const chosenGeneration = state.generation;
      $('experiment').value = state.experiment;
      updateMetrics(chosen); await loadPage();
      if (chosenGeneration !== state.generation) return;
      const scan = M.reconcileScan(state.scanCursor, state.scanComplete, Number(chosen.accepted), state.known.size);
      state.scanCursor = scan.cursor; state.scanComplete = scan.complete;
      notice(`${Number(chosen.accepted).toLocaleString()} accepted / ${Number(chosen.total).toLocaleString()} requested trials · Results refresh every 5 seconds. Computation continues independently.`);
    } catch (error) { notice(`Cannot load coordinator results: ${error.message} Use Refresh to retry.`, true); }
    finally { state.refreshBusy = false; $('refresh').disabled = false; }
  }

  function resetExperiment(id) {
    state.generation++; state.selection++; state.experiment = id;
    state.cursors = [null]; state.page = 0; state.nextPage = null;
    state.known.clear(); state.scanCursor = null; state.scanComplete = false;
    state.selected = null; state.replay = null; state.time = 0; state.nextAt = 0;
    state.busy = false;
    $('stage-empty').hidden = false; $('trial-label').textContent = 'AWAITING A REPLAY';
    $('outcome').textContent = 'READY'; $('outcome').className = 'badge';
    $('selected-title').textContent = 'No trial selected';
    $('selected-note').textContent = 'Select a row to inspect its final state and replay.';
    for (const id of ['duration', 'steps', 'energy', 'retention', 'initial-positions', 'final-positions']) $(id).textContent = '—';
    $('scrub').disabled = true;
  }

  $('experiment').addEventListener('change', () => { resetExperiment($('experiment').value); refresh(); });
  $('refresh').addEventListener('click', () => refresh());
  $('play').addEventListener('click', () => {
    state.playing = !state.playing;
    $('play').textContent = state.playing ? 'Pause' : 'Play';
    $('play').setAttribute('aria-pressed', String(state.playing));
    if (state.playing && state.selected && state.time >= state.selected.time) state.time = 0;
    if (state.playing && !state.replay) nextReplay();
  });
  $('next').addEventListener('click', nextReplay);
  $('previous-page').addEventListener('click', async () => {
    if (state.page === 0) return; state.page--;
    try { await loadPage(); } catch (error) { notice(error.message, true); }
  });
  $('next-page').addEventListener('click', async () => {
    if (state.nextPage === null) return;
    state.cursors[++state.page] = state.nextPage;
    try { await loadPage(); } catch (error) { notice(error.message, true); }
  });
  $('scrub').addEventListener('input', () => { state.time = Number($('scrub').value); state.nextAt = 0; });

  let last = performance.now();
  function animate(now) {
    const elapsed = Math.min((now - last) / 1000, .2); last = now;
    if (state.replay && state.selected) {
      if (state.playing) state.time = Math.min(state.selected.time, state.time + elapsed * Number($('speed').value));
      const positions = M.positionAt(state.replay.frames, state.time);
      drawState($('universe'), positions, state.replay.frames, state.time);
      $('scrub').value = String(state.time);
      if (state.playing && state.time >= state.selected.time && $('auto').checked) {
        if (!state.nextAt) state.nextAt = now + 1000;
        if (now >= state.nextAt) nextReplay();
      }
    } else {
      drawState($('universe'), state.selected?.final?.p || null);
      if (!state.busy && state.playing && $('auto').checked && now >= state.nextAt) {
        state.nextAt = now + 5000; nextReplay();
      }
    }
    $('clock').textContent = `${format(state.time)} / ${format(state.selected?.time || 0)} s`;
    requestAnimationFrame(animate);
  }
  refresh(); setInterval(() => refresh(true), 5000); requestAnimationFrame(animate);
})();
