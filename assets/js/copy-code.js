document.querySelectorAll('.copy-code-button').forEach(function (button) {
    const originalContent = button.innerHTML;
    let resetTimer;
    button.addEventListener('click', async function () {
        const code = button.parentElement.querySelector('code');
        const lines = code.querySelectorAll('.line');
        const text = lines.length > 0 ? Array.from(lines, function (line) {
            const clone = line.cloneNode(true);
            clone.querySelectorAll('.ln, .lnt, .line-number').forEach(number => number.remove());
            return clone.textContent;
        }).join('\n') : code.textContent;
        try {
            await navigator.clipboard.writeText(text);
            button.textContent = 'Copied!';
        } catch {
            button.textContent = 'Copy failed';
        }
        clearTimeout(resetTimer);
        resetTimer = setTimeout(() => { button.innerHTML = originalContent; }, 2000);
    });
});
