(function () {
  var onReady = function onReady(fn) {
    if (document.addEventListener) {
      document.addEventListener("DOMContentLoaded", fn);
    } else {
      document.attachEvent("onreadystatechange", function () {
        if (document.readyState === "interactive") {
          fn();
        }
      });
    }
  };

  onReady(function () {
    let currentPage = 1;
    let loading = false;

    function formatDate(isoDate) {
        const date = new Date(isoDate);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    }

    function createPostCard(post) {
        return `
        <article class="post-card">
            <h3><a href="/posts/${post.slug}">${post.title}</a></h3>
            <time datetime="${post.date}">${formatDate(post.date)}</time>
            ${post.description ? `<p>${post.description}</p>` : ''}
        </article>
    `;
    }

    async function loadMorePosts() {
        if (loading) return;

        const loadMoreBtn = document.getElementById('load-more');
        const loadingSpinner = document.getElementById('loading');
        const postsContainer = document.getElementById('posts-container');

        try {
            loading = true;
            loadMoreBtn.style.display = 'none';
            loadingSpinner.style.display = 'block';

            const response = await fetch(`/api/posts?page=${currentPage + 1}`);
            const data = await response.json();

            if (data.posts.length > 0) {
                const postsHtml = data.posts.map(createPostCard).join('');
                postsContainer.insertAdjacentHTML('beforeend', postsHtml);
                currentPage = data.pagination.current_page;
            }

            // Show/hide load more button based on pagination
            if (!data.pagination.has_next) {
                loadMoreBtn.style.display = 'none';
            } else {
                loadMoreBtn.style.display = 'block';
            }

        } catch (error) {
            console.error('Error loading posts:', error);
        } finally {
            loading = false;
            loadingSpinner.style.display = 'none';
        }
    }

    // Event listeners
    document.getElementById('load-more').addEventListener('click', loadMorePosts);

    // // Optional: Infinite scroll
    // const observerOptions = {
    //     root: null,
    //     rootMargin: '100px',
    //     threshold: 0.1
    // };
    //
    // const observer = new IntersectionObserver((entries) => {
    //     entries.forEach(entry => {
    //         if (entry.isIntersecting && !loading) {
    //             loadMorePosts();
    //         }
    //     });
    // }, observerOptions);
    //
    // observer.observe(document.getElementById('pagination'));

  });
})();
