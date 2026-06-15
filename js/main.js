// 主要功能逻辑

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 初始化首页
    if (document.getElementById('breakingNews')) {
        loadBreakingNews();
        loadFeaturedNews();
        loadLatestNews(1);
    }
    
    // 初始化搜索功能
    initSearch();
    
    // 初始化返回顶部按钮
    initBackToTop();
});

// 加载最新动态
function loadBreakingNews() {
    const container = document.getElementById('breakingNews');
    if (!container || !articles.length) return;
    
    // 获取最新的一篇文章
    const latest = articles[0];
    container.innerHTML = `
        <strong>【最新】</strong>
        <a href="article.html?id=${latest.id}">${latest.title}</a>
        <span class="meta">${latest.date} | ${latest.category}</span>
    `;
}

// 加载头条新闻
function loadFeaturedNews() {
    const container = document.getElementById('featuredNews');
    if (!container || !articles.length) return;
    
    // 获取前两篇作为头条
    const featured = articles.slice(0, 2);
    
    container.innerHTML = featured.map((article, index) => `
        <div class="featured-item">
            <div class="content">
                <h3><a href="article.html?id=${article.id}">${article.title}</a></h3>
                <div class="meta">
                    <span class="category-badge">${article.category}</span>
                    <span>${article.date}</span>
                    <span>${article.author}</span>
                </div>
                <p class="summary">${article.summary}</p>
            </div>
        </div>
    `).join('');
}

// 加载最新新闻列表（按日期排序）
function loadLatestNews(page) {
    const container = document.getElementById('latestNews');
    if (!container || !articles.length) return;
    
    // 按日期从新到旧排序
    const sortedArticles = [...articles].sort((a, b) => {
        return new Date(b.date) - new Date(a.date);
    });
    
    const perPage = 6;
    const start = (page - 1) * perPage;
    const end = start + perPage;
    const pageArticles = sortedArticles.slice(start, end);
    
    container.innerHTML = pageArticles.map((article, index) => `
        <div class="news-item">
            <div class="content">
                <h3><a href="article.html?id=${article.id}">${article.title}</a></h3>
                <div class="meta">
                    <span class="category-badge">${article.category}</span>
                    <span>${article.date}</span>
                    <span>${article.author}</span>
                </div>
                <p class="summary">${article.summary}</p>
            </div>
        </div>
    `).join('');
    
    // 加载分页
    loadPagination(page, Math.ceil(sortedArticles.length / perPage));
}

// 加载分页控件（最多显示6页）
function loadPagination(currentPage, totalPages) {
    const container = document.getElementById('pagination');
    if (!container) return;
    
    const maxVisible = 3;
    let html = '';
    
    // 上一页
    if (currentPage > 1) {
        html += `<button class="pagination-btn" onclick="loadLatestNews(${currentPage - 1})">‹ 上一页</button>`;
    }
    
    // 计算起始和结束页码
    let startPage = Math.max(1, currentPage - Math.floor(maxVisible / 2));
    let endPage = Math.min(totalPages, startPage + maxVisible - 1);
    
    // 调整起始页码
    if (endPage - startPage + 1 < maxVisible) {
        startPage = Math.max(1, endPage - maxVisible + 1);
    }
    
    // 第一页
    if (startPage > 1) {
        html += `<button class="pagination-btn" onclick="loadLatestNews(1)">1</button>`;
        if (startPage > 2) {
            html += `<span class="pagination-ellipsis">...</span>`;
        }
    }
    
    // 页码按钮
    for (let i = startPage; i <= endPage; i++) {
        html += `<button class="pagination-btn ${i === currentPage ? 'active' : ''}" onclick="loadLatestNews(${i})">${i}</button>`;
    }
    
    // 最后一页
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            html += `<span class="pagination-ellipsis">...</span>`;
        }
        html += `<button class="pagination-btn" onclick="loadLatestNews(${totalPages})">${totalPages}</button>`;
    }
    
    // 下一页
    if (currentPage < totalPages) {
        html += `<button class="pagination-btn" onclick="loadLatestNews(${currentPage + 1})">下一页 ›</button>`;
    }
    
    container.innerHTML = html;
}

// 加载文章详情
function loadArticleDetail(articleId) {
    const container = document.getElementById('articleDetail');
    if (!container) return;
    
    const article = articles.find(a => a.id === articleId);
    
    if (!article) {
        container.innerHTML = '<div class="error">文章不存在</div>';
        return;
    }
    
    // 更新页面标题
    document.title = `${article.title} - 国内物流新闻`;
    
    // 更新meta description
    const metaDesc = document.querySelector('meta[name="description"]');
    if (metaDesc) {
        metaDesc.content = article.summary;
    }
    
    container.innerHTML = `
        <h1>${article.title}</h1>
        <div class="article-meta">
            <span class="category-badge">${article.category}</span>
            <span>发布时间：${article.date}</span>
            <span>作者：${article.author}</span>
        </div>
        <div class="article-content">
            ${article.content}
        </div>
        <div class="article-tags">
            <strong>标签：</strong>
            ${article.tags.map(tag => `<a href="category.html?tag=${tag}" class="tag">${tag}</a>`).join('')}
        </div>
    `;
}

// 加载相关文章
function loadRelatedArticles(articleId) {
    const container = document.getElementById('relatedArticles');
    if (!container) return;
    
    const article = articles.find(a => a.id === articleId);
    if (!article) return;
    
    // 查找同分类的其他文章
    const related = articles
        .filter(a => a.id !== articleId && a.category === article.category)
        .slice(0, 5);
    
    // 如果同分类文章不足，补充其他分类
    if (related.length < 5) {
        const others = articles
            .filter(a => a.id !== articleId && a.category !== article.category)
            .slice(0, 5 - related.length);
        related.push(...others);
    }
    
    container.innerHTML = related.map(item => `
        <div class="related-item">
            <h4><a href="article.html?id=${item.id}">${item.title}</a></h4>
            <div class="meta">${item.date} | ${item.category}</div>
        </div>
    `).join('');
}

// 加载分类新闻
function loadCategoryNews(category) {
    const container = document.getElementById('categoryNews');
    if (!container) return;
    
    const categoryArticles = articles.filter(a => a.category === category);
    
    if (categoryArticles.length === 0) {
        container.innerHTML = '<div class="error">该分类暂无文章</div>';
        return;
    }
    
    // 更新分类描述
    const meta = document.getElementById('categoryMeta');
    if (meta) {
        meta.textContent = `共 ${categoryArticles.length} 篇文章`;
    }
    
    renderArticleList(container, categoryArticles);
}

// 加载标签新闻
function loadTagNews(tag) {
    const container = document.getElementById('categoryNews');
    if (!container) return;
    
    const tagArticles = articles.filter(a => a.tags.includes(tag));
    
    if (tagArticles.length === 0) {
        container.innerHTML = '<div class="error">该标签暂无文章</div>';
        return;
    }
    
    // 更新描述
    const meta = document.getElementById('categoryMeta');
    if (meta) {
        meta.textContent = `共 ${tagArticles.length} 篇文章`;
    }
    
    renderArticleList(container, tagArticles);
}

// 加载所有新闻
function loadAllNews() {
    const container = document.getElementById('categoryNews');
    if (!container) return;
    
    const meta = document.getElementById('categoryMeta');
    if (meta) {
        meta.textContent = `共 ${articles.length} 篇文章`;
    }
    
    renderArticleList(container, articles);
}

// 渲染文章列表
function renderArticleList(container, articleList) {
    container.innerHTML = articleList.map((article, index) => `
        <div class="news-item">
            <div class="content">
                <h3><a href="article.html?id=${article.id}">${article.title}</a></h3>
                <div class="meta">
                    <span class="category-badge">${article.category}</span>
                    <span>${article.date}</span>
                    <span>${article.author}</span>
                </div>
                <p class="summary">${article.summary}</p>
            </div>
        </div>
    `).join('');
}

// 初始化搜索功能
function initSearch() {
    const searchBtn = document.getElementById('searchBtn');
    const searchInput = document.getElementById('searchInput');
    
    if (searchBtn && searchInput) {
        searchBtn.addEventListener('click', performSearch);
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                performSearch();
            }
        });
    }
}

// 执行搜索
function performSearch() {
    const searchInput = document.getElementById('searchInput');
    if (!searchInput) return;
    
    const query = searchInput.value.trim();
    if (!query) return;
    
    // 跳转到搜索结果页面（这里简单跳转到分类页面）
    window.location.href = `category.html?tag=${encodeURIComponent(query)}`;
}

// 格式化日期
function formatDate(dateString) {
    const date = new Date(dateString);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

// 截断文本
function truncateText(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

// 初始化返回顶部按钮
function initBackToTop() {
    // 创建返回顶部按钮
    const backToTopBtn = document.createElement('button');
    backToTopBtn.className = 'back-to-top';
    backToTopBtn.title = '返回顶部';
    document.body.appendChild(backToTopBtn);
    
    // 监听滚动事件
    window.addEventListener('scroll', function() {
        if (window.pageYOffset > 300) {
            backToTopBtn.classList.add('visible');
        } else {
            backToTopBtn.classList.remove('visible');
        }
    });
    
    // 点击返回顶部
    backToTopBtn.addEventListener('click', function() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
}

// 获取文章图片（不显示图片）
function getArticleImage(article, index) {
    return '';
}