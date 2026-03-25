// ============================
// HOME.JS — Interactividad
// ============================

document.addEventListener("DOMContentLoaded", () => {
    // Scroll suave
    document.querySelectorAll('[data-scroll]').forEach(btn => {
        btn.addEventListener("click", e => {
            e.preventDefault();
            const target = document.querySelector(btn.dataset.scroll);
            if (target) {
                target.scrollIntoView({ behavior: "smooth", block: "start" });
            }
        });
    });

    // Cards animations por scroll
    const animatedCards = document.querySelectorAll('.service-card, .card-hover');
    const cardObserver = new IntersectionObserver((entries, obs) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('in-view');
                obs.unobserve(entry.target);
            }
        });
    }, { threshold: 0.2 });

    animatedCards.forEach(card => cardObserver.observe(card));
});
