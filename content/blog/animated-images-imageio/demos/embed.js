(() => {
  if (parent === window) return;
  let previousHeight = 0;
  function reportHeight() {
    const height = Math.ceil(document.body.getBoundingClientRect().height) + 4;
    if (height === previousHeight) return;
    previousHeight = height;
    parent.postMessage({ type: 'demo-height', height }, location.origin);
  }
  new ResizeObserver(reportHeight).observe(document.body);
  window.addEventListener('load', reportHeight);
})();
