const newsContainer = document.getElementById('news-container');

// 🌀 Show loading shimmer while fetching
function showLoading() {
  newsContainer.innerHTML = `
    <div class="loader">
      <div class="shimmer"></div>
      <p>Loading latest articles...</p>
    </div>
  `;
}

// ✨ Animate cards appearing
function animateCards() {
  const cards = document.querySelectorAll('.card');
  cards.forEach((card, index) => {
    card.style.opacity = '0';
    setTimeout(() => {
      card.style.transition = 'opacity 0.5s ease';
      card.style.opacity = '1';
    }, 100 * index);
  });
}

// 🚀 Fetch Feed from backend
async function fetchFeed() {
  try {
    showLoading();

    const response = await fetch('/get_feed');
    const articles = await response.json();

    newsContainer.innerHTML = '';

    if (!Array.isArray(articles) || articles.length === 0) {
      newsContainer.innerHTML = "<p>No articles available right now.</p>";
      return;
    }

    // 📰 Create article cards
    articles.forEach(article => {
      const card = document.createElement('div');
      card.classList.add('card');
      card.innerHTML = `
        <div class="card-header">
          <a href="${article.url}" target="_blank">${article.title}</a>
        </div>
        <div class="card-meta">
          <span class="category">${article.category}</span>
          <span class="source">${article.source}</span>
          <span class="score">⭐ ${article.score}</span>
        </div>
        <div class="card-desc">${article.desc || "No description available."}</div>
      `;
      newsContainer.appendChild(card);
    });

    // 🎬 Animate cards in
    animateCards();

  } catch (error) {
    newsContainer.innerHTML = `
      <p style="color:red;">⚠️ Error loading news. Please try again later.</p>
    `;
    console.error("Error fetching feed:", error);
  }
}

// 🔄 Initial fetch + auto-refresh
fetchFeed();
setInterval(fetchFeed, 30000);
