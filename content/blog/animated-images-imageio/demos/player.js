(() => {
  const FRAMES = 100, DURATION = 50;
  const $ = id => document.getElementById(id);
  const cells = Array.from({ length: FRAMES }, () => {
    const cell = document.createElement('div');
    cell.className = 'cell';
    $('strip').appendChild(cell);
    return cell;
  });
  let current = 0, acc = 0, lastTarget = null, virtualTime = 0, untilTick = 0;
  let pass = 1, held = false, finished = false, paused = matchMedia('(prefers-reduced-motion: reduce)').matches;
  let decoding = false, decodeElapsed = 0, decodeDuration = 0, pendingReady = false;
  let decision = '', visibleInPage = true;
  const nextIndex = () => (current + 1) % FRAMES;
  const tickDuration = () => 1000 / Number($('refresh').value);

  function prefetch() {
    if (decoding || pendingReady) return;
    decoding = true;
    decodeElapsed = 0;
    decodeDuration = Number($('decode').value);
  }

  function seek(frame) {
    // Seeking is a demo control: cancel the old simulated job and prepare this frame's successor.
    current = frame;
    acc = 0;
    lastTarget = null;
    untilTick = tickDuration();
    pass = 1;
    held = finished = decoding = pendingReady = false;
    prefetch();
    decision = 'Frame ' + current + ' is on screen; preparing frame ' + nextIndex() + '.';
    render();
  }

  function tick() {
    if ($('hidden').checked) {
      lastTarget = null;
      held = false;
      decision = 'Offscreen: reset lastTargetTimestamp and return before requesting another decode.';
      return;
    }
    if (lastTarget !== null) acc += virtualTime - lastTarget;
    lastTarget = virtualTime;
    if (acc + 1e-7 < DURATION) {
      held = false;
      prefetch();
      decision = 'Keep frame ' + current + ': its 50 ms display time has not elapsed.';
      return;
    }
    if (!pendingReady) {
      acc = DURATION;
      held = true;
      prefetch();
      decision = 'Next frame is not ready: cap accumulatedTime at 50 ms and hold frame ' + current + '.';
      return;
    }
    held = false;
    if (nextIndex() === 0) {
      const limit = Number($('loop-count').value);
      if (limit > 0 && pass >= limit) {
        finished = true;
        lastTarget = null;
        decision = 'Loop count reached: stop on frame 99 before displaying frame 0 again.';
        return;
      }
      pass++;
    }
    current = nextIndex();
    acc = Math.min(Math.max(0, acc - DURATION), DURATION);
    pendingReady = false;
    prefetch();
    decision = 'Display frame ' + current + ', subtract 50 ms, then prepare frame ' + nextIndex() + '.';
  }

  function advance(dt) {
    // Process worker completion before each display tick, independent of view visibility.
    while (dt > 1e-7 && !finished) {
      const slice = Math.min(dt, untilTick);
      if (decoding) {
        decodeElapsed = Math.min(decodeElapsed + slice, decodeDuration);
        if (decodeElapsed >= decodeDuration) {
          decoding = false;
          pendingReady = true;
        }
      }
      virtualTime += slice;
      untilTick -= slice;
      dt -= slice;
      if (untilTick < 1e-7) {
        tick();
        untilTick = tickDuration();
      }
    }
  }

  function render() {
    cells.forEach((cell, i) => {
      cell.className = 'cell' + (i === current ? ' current' : i === nextIndex() ? pendingReady ? ' ready' : decoding ? ' decoding' : '' : '');
    });
    $('sample').style.backgroundPosition = (current % 10) * 100 / 9 + '% ' + Math.floor(current / 10) * 100 / 9 + '%';
    $('sample').classList.toggle('offscreen', $('hidden').checked);
    $('sample').setAttribute('aria-label', 'Timer animation, frame ' + current);
    $('scrub').value = current;
    $('scrub').setAttribute('aria-valuetext', 'Frame ' + current + ' of 100');
    $('frame-number').textContent = 'Frame ' + current + ' / 99';
    $('passes').textContent = 'Pass ' + pass + ' · ' + tickDuration().toFixed(1) + ' ms per tick';
    $('accfill').style.width = Math.min(acc / DURATION * 100, 100) + '%';
    $('accfill').classList.toggle('held', held);
    $('acctext').textContent = acc.toFixed(1) + ' / 50 ms';
    $('decfill').style.width = (pendingReady ? 100 : decodeDuration ? decodeElapsed / decodeDuration * 100 : 0) + '%';
    $('dectext').textContent = 'Frame ' + nextIndex() + (pendingReady ? ' ready' : ' · ' + Math.round(decodeElapsed) + '/' + decodeDuration + ' ms');
    $('decision').textContent = decision;
    $('status').textContent = finished ? 'Finished on the last frame.' : paused ? 'Demo paused. Step one tick to inspect the player.' : $('hidden').checked ? 'Offscreen. Playback clock frozen.' : held ? 'Holding: waiting for the next frame.' : 'Playing.';
    $('status').classList.toggle('held', held && !paused && !$('hidden').checked);
    $('playpause').textContent = finished ? 'Play again' : paused ? 'Play' : 'Pause';
    $('step').disabled = !paused || finished;
    $('decode-label').textContent = $('decode').value + ' ms';
  }

  $('playpause').addEventListener('click', () => {
    if (finished) { seek(0); paused = false; }
    else paused = !paused;
    render();
  });
  $('step').addEventListener('click', () => { advance(untilTick); render(); });
  $('restart').addEventListener('click', () => seek(0));
  $('scrub').addEventListener('input', () => { paused = true; seek(Number($('scrub').value)); });
  $('hidden').addEventListener('change', () => { lastTarget = null; tick(); render(); });
  $('decode').addEventListener('input', render);
  $('loop-count').addEventListener('change', () => seek(0));
  $('refresh').addEventListener('change', () => { untilTick = tickDuration(); render(); });
  document.addEventListener('visibilitychange', () => { lastReal = null; });
  new IntersectionObserver(entries => { visibleInPage = entries[0].isIntersecting; lastReal = null; }).observe(document.querySelector('.demo'));
  matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change', event => { if (event.matches) { paused = true; render(); } });

  let lastReal = null;
  function frame(now) {
    if (lastReal !== null && !paused && !finished && visibleInPage && !document.hidden) {
      advance(Math.min(now - lastReal, 100) * Number($('speed').value));
      render();
    }
    lastReal = now;
    requestAnimationFrame(frame);
  }
  seek(0);
  requestAnimationFrame(frame);
})();
