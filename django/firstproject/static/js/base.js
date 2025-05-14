const toggleButton = document.querySelector('#dark-light button');
const body = document.body;

toggleButton.addEventListener('click', () => {
    body.classList.toggle('light-theme');
});

