// Brew day timers and checklist persistence

document.addEventListener('DOMContentLoaded', () => {
    const recipeId = window.location.pathname.split('/').pop();
    const storageKey = `brewday-${recipeId}`;

    // Restore checkbox state
    const saved = JSON.parse(localStorage.getItem(storageKey) || '{}');
    document.querySelectorAll('.step-check').forEach(cb => {
        const idx = cb.id.replace('step-', '');
        if (saved[idx]) {
            cb.checked = true;
            cb.closest('.brew-step').classList.add('opacity-50');
        }
        cb.addEventListener('change', () => {
            saved[idx] = cb.checked;
            localStorage.setItem(storageKey, JSON.stringify(saved));
            cb.closest('.brew-step').classList.toggle('opacity-50', cb.checked);
        });
    });

    // Timer buttons
    document.querySelectorAll('.timer-start').forEach(btn => {
        btn.addEventListener('click', () => {
            const display = btn.parentElement.querySelector('.timer-display');
            let remaining = parseInt(display.dataset.seconds);

            btn.disabled = true;
            btn.textContent = 'Running...';

            const interval = setInterval(() => {
                remaining--;
                if (remaining <= 0) {
                    clearInterval(interval);
                    display.textContent = '00:00';
                    display.classList.remove('bg-primary');
                    display.classList.add('bg-success');
                    btn.textContent = 'Done!';
                    btn.classList.remove('btn-outline-primary');
                    btn.classList.add('btn-outline-success');

                    // Try to play a notification sound or alert
                    if (Notification.permission === 'granted') {
                        new Notification('BrewCalc Timer', { body: 'Timer complete!' });
                    } else {
                        alert('Timer complete!');
                    }
                    return;
                }
                const min = Math.floor(remaining / 60);
                const sec = remaining % 60;
                display.textContent = `${String(min).padStart(2, '0')}:${String(sec).padStart(2, '0')}`;
                display.dataset.seconds = remaining;
            }, 1000);
        });
    });

    // Request notification permission
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
    }
});
