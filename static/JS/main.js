document.addEventListener("DOMContentLoaded", () => {
    animateProgressBars();
    wireStrengthSlider();
    wireDeleteLinks();
});

function animateProgressBars() {
    const bars = document.querySelectorAll(".progress-fill");
    if (!bars.length) return;

    // Set width on the next frame so the CSS transition actually plays
    // instead of the bar just appearing at its target width.
    requestAnimationFrame(() => {
        setTimeout(() => {
            bars.forEach((bar) => {
                const target = bar.dataset.target || 0;
                bar.style.width = `${target}%`;
            });
        }, 150);
    });
}

function wireStrengthSlider() {
    const slider = document.getElementById("strength-slider");
    const output = document.getElementById("strength-value");
    if (!slider || !output) return;

    const sync = () => {
        output.textContent = slider.value;
    };

    sync();
    slider.addEventListener("input", sync);
}

function wireDeleteLinks() {
    document.querySelectorAll(".delete-link").forEach((link) => {
        link.addEventListener("click", (event) => {
            const subject = link.getAttribute("aria-label") || "this topic";
            if (!window.confirm(`Remove ${subject.replace("Delete ", "")}?`)) {
                event.preventDefault();
            }
        });
    });
}
