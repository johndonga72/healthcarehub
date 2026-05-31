document.addEventListener('DOMContentLoaded', () => {
    const refreshNewsBtn = document.getElementById('refresh-news');
    if (refreshNewsBtn) {
        refreshNewsBtn.addEventListener('click', () => {
            fetch('/news')
                .then(response => response.text())
                .then(html => {
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(html, 'text/html');
                    document.getElementById('news-feed').innerHTML = doc.getElementById('news-feed').innerHTML;
                });
        });
    }
});