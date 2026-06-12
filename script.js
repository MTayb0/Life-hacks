// Loads data/articles.json and renders the article list on the homepage
fetch('data/articles.json')
  .then(res => res.json())
  .then(articles => {
    const list = document.getElementById('article-list');
    list.innerHTML = '';

    if (!articles || articles.length === 0) {
      list.innerHTML = '<li>No articles yet. Check back soon!</li>';
      return;
    }

    // Show newest first
    articles
      .slice()
      .reverse()
      .forEach(article => {
        const li = document.createElement('li');
        const badge = article.category === 'trending' ? '🔥 Trending' : '💡 How-To';
        li.innerHTML = `
          <a href="articles/${article.filename}">${article.title}</a>
          <span class="date">${badge} &middot; ${article.date}</span>
        `;
        list.appendChild(li);
      });
  })
  .catch(err => {
    document.getElementById('article-list').innerHTML =
      '<li>Could not load articles.</li>';
    console.error(err);
  });
