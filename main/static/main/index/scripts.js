const bj_script = document.currentScript;
const bj_apiUrl = bj_script.getAttribute('data-api-url');
const bj_lang = bj_script.getAttribute('data-lang');
const LoadMoreButton = $('.load-more-posts');

function renderBinaryJournalPost(post) {
    let post_template = $($('#bj-post-template')[0].content).clone();

    post_template.find('.article__image').attr('href', post.href);
    post_template.find('.bj_img').attr('src', post.cover_url).attr('alt', post.title);
    post_template.find('.article__tag').attr('href', post.category_href).text(post.category).attr('style', 'background:'.concat(post.category_color, ';'));
    post_template.find('.bj_article__title__link').attr('href', post.href).text(post.title);
    post_template.find('.article__excerpt').text(post.description);
    post_template.find('.article__date').attr('datetime', post.timestamp).text(post.user_friendly_date);
    post_template.find('.article__minutes').text(post.read_time);

    return post_template;
}

function load_posts_page() {
    let next_page = LoadMoreButton.data('next-page');
    let next_page_url = bj_apiUrl + '?page=' + next_page;
    let button_text = LoadMoreButton.text();
    let bi_result_container = $('#bj-results-container');

    LoadMoreButton.addClass('button--loading');
    LoadMoreButton.text("Loading");

    $.ajax({
        url: next_page_url,
        headers: {
            'X-Language': bj_lang
        },
        success: function (response) {
            response.results.forEach(function (post) {
                const rendered_post = renderBinaryJournalPost(post);
                bi_result_container.append(rendered_post);
            });

            LoadMoreButton.removeClass('button--loading');
            LoadMoreButton.text(button_text);

            if (response.next === null) {
                LoadMoreButton.fadeOut();
            }else{
                LoadMoreButton.data('next-page', next_page + 1);
            }
        },
    });
}

$( document ).ready(function() {

    load_posts_page();

    LoadMoreButton.on('click', load_posts_page);

})