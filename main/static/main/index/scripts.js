// "Load more" in The Binary Journal (main/_lib/_bj_load_more.html). The posts come rendered from the server and htmx
// adds each next page; this shows that they are on their way, says so when they can't be loaded and takes the
// focus to the first new post, since the button it was on is replaced.

// The site uses neither htmx's loading indicators nor code in attributes: no <style> element to add, nothing to eval
htmx.config.includeIndicatorStyles = false;
htmx.config.allowEval = false;
// A request that hangs fails like any other, instead of leaving the button loading forever
htmx.config.timeout = 10000;

const bj_posts = document.getElementById('bj-results-container');
let bj_firstNewPost = null;

function isLoadMore(event) {
    return event.detail.elt.classList.contains('load-more-posts');
}

document.body.addEventListener('htmx:beforeRequest', function (event) {
    if (!isLoadMore(event)) {
        return;
    }
    const button = event.detail.elt;
    button.classList.add('button--loading');
    button.parentElement.querySelector('.load-more-error').hidden = true;
    bj_firstNewPost = bj_posts.children.length;
});

document.body.addEventListener('htmx:afterRequest', function (event) {
    // When it works the button is replaced by the next one; otherwise it stays for another try
    if (!isLoadMore(event) || event.detail.successful) {
        return;
    }
    const button = event.detail.elt;
    button.classList.remove('button--loading');
    button.parentElement.querySelector('.load-more-error').hidden = false;
});

bj_posts.addEventListener('htmx:afterSettle', function () {
    const post = bj_posts.children[bj_firstNewPost];
    if (post) {
        post.querySelector('.article__title a').focus();
    }
});
