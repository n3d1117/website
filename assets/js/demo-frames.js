window.addEventListener('message', function (event) {
    if (event.origin !== window.location.origin) return;
    const data = event.data;
    if (!data || data.type !== 'demo-height' || !Number.isFinite(data.height)) return;
    if (data.height < 1 || data.height > 4000) return;
    document.querySelectorAll('iframe[data-animated-images-demo]').forEach(function (frame) {
        if (frame.contentWindow === event.source) {
            frame.style.height = Math.ceil(data.height) + 'px';
            frame.style.opacity = '1';
        }
    });
});
