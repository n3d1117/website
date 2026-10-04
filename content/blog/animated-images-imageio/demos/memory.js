(() => {
  const $ = id => document.getElementById(id);
  const ids = ['width', 'height', 'frames', 'views'];
  function render() {
    if (ids.some(id => !$(id).validity.valid || $(id).value === '')) {
      $('formula').textContent = 'Enter whole numbers within the allowed ranges.';
      $('all-value').textContent = $('buffer-value').textContent = '—';
      $('all-bar').style.width = $('buffer-bar').style.width = '0%';
      return;
    }
    const [width, height, frames, views] = ids.map(id => Number($(id).value));
    const bitmap = width * height * 4;
    const mib = bytes => (bytes / (1024 * 1024)).toFixed(2) + ' MiB';
    $('all-value').textContent = mib(bitmap * frames * views);
    $('buffer-value').textContent = mib(bitmap * 2 * views);
    $('all-bar').style.width = '100%';
    $('buffer-bar').style.width = (2 / frames * 100) + '%';
    $('formula').textContent = width + ' × ' + height + ' × 4 = ' + mib(bitmap) + ' per bitmap';
  }
  ids.forEach(id => $(id).addEventListener('input', render));
  render();
})();
