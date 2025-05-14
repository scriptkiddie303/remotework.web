document.addEventListener('DOMContentLoaded', function () {
    // Scroll team cards left/right
    const leftBtn = document.querySelector('.carousel-left');
    const rightBtn = document.querySelector('.carousel-right');
    const carousel = document.querySelector('.team-carousel');

    if (leftBtn && rightBtn && carousel) {
        leftBtn.addEventListener('click', function () {
            carousel.scrollBy({ left: -200, behavior: 'smooth' });
        });

        rightBtn.addEventListener('click', function () {
            carousel.scrollBy({ left: 200, behavior: 'smooth' });
        });
    }

    // Show modal on card click
    const cards = document.querySelectorAll('.team-card');
    const modal = document.querySelector('.modal');
    const modalName = document.querySelector('.modal-name');
    const modalInfo = document.querySelector('.modal-info');
    const closeBtn = document.querySelector('.modal-close');

    cards.forEach(card => {
        card.addEventListener('click', function () {
            modalName.textContent = card.dataset.name;
            modalInfo.textContent = card.dataset.info;
            modal.style.display = 'block';
        });
    });

    // Close modal
    closeBtn.addEventListener('click', function () {
        modal.style.display = 'none';
    });

    window.addEventListener('click', function (e) {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });
});
