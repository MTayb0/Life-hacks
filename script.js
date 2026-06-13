// Loads data/articles.json and renders the article list on the homepage
const CATEGORY_BADGES = {
  trending: '🔥 Trending',
  sports: '⚽ Sports',
  film: '🎬 Film & TV',
  news: '📰 News',
  money: '💰 Money',
  tech: '💻 Tech',
  howto: '💡 How-To'
};

let allArticles = [];
let currentFilter = 'all';

function renderArticles() {
  const list = document.getElementById('article-list');
  list.innerHTML = '';

  const filtered = currentFilter === 'all'
    ? allArticles
    : allArticles.filter(a => (a.category || 'howto') === currentFilter);

  if (!filtered || filtered.length === 0) {
    list.innerHTML = '<li>No articles in this category yet. Check back soon!</li>';
    return;
  }

  filtered
    .slice()
    .reverse()
    .forEach(article => {
      const badge = CATEGORY_BADGES[article.category] || '💡 How-To';
      const li = document.createElement('li');
      li.innerHTML = `
        <a href="articles/${article.filename}">${article.title}</a>
        <span class="date">${badge} &middot; ${article.date}</span>
      `;
      list.appendChild(li);
    });
}

document.querySelectorAll('.filter-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentFilter = btn.dataset.cat;
    renderArticles();
  });
});

fetch('data/articles.json')
  .then(res => res.json())
  .then(articles => {
    allArticles = articles || [];
    renderArticles();
  })
  .catch(err => {
    document.getElementById('article-list').innerHTML =
      '<li>Could not load articles.</li>';
    console.error(err);
  });
