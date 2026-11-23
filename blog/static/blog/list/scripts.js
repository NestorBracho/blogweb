// "Load more" on the blog's list of posts (blog/_lib/_load_more.html). The posts come rendered from the server and htmx
// adds each next page; this shows that they are on their way, says so when they can't be loaded and takes the
// focus to the first new post, since the button it was on is replaced.

// The site uses neither htmx's loading indicators nor code in attributes: no <style> element to add, nothing to eval
htmx.config.includeIndicatorStyles = false;
htmx.config.allowEval = false;
// A request that hangs fails like any other, instead of leaving the button loading forever
htmx.config.timeout = 10000;

const posts = document.getElementById('posts-container');
let firstNewPost = null;

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
    firstNewPost = posts.children.length;
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

posts.addEventListener('htmx:afterSettle', function () {
    const post = posts.children[firstNewPost];
    if (post) {
        post.querySelector('.article__title a').focus();
    }
});
