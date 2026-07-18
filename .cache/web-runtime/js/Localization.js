[...document.querySelectorAll('[data-i18n]')].forEach(e => {
    e.textContent = chrome.i18n.getMessage(e.dataset.i18n) || e.textContent;
});
[...document.querySelectorAll('[data-i18nt]')].forEach(e => {
    e.title = chrome.i18n.getMessage(e.dataset.i18nt) || e.title;
});
[...document.querySelectorAll('[data-i18na]')].forEach(e => {
    e.alt = chrome.i18n.getMessage(e.dataset.i18na) || e.alt;
});
[...document.querySelectorAll('[data-i18np]')].forEach(e => {
    e.placeholder = chrome.i18n.getMessage(e.dataset.i18na) || e.placeholder;
});
    
      
