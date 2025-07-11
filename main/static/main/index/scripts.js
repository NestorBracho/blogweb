const bj_script = document.currentScript;
const bj_apiUrl = bj_script.getAttribute('data-binary-journal-api-url');
const hh_apiUrl = bj_script.getAttribute('data-hackers-haven-api-url');
const st_lang = bj_script.getAttribute('data-lang');
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

function render_hackers_heaven_category(category) {
    let category_template = $($('#hh-category-template')[0].content).clone();
    let section_tags_content_html = "";

    category_template.find('.section-tags__image').attr('href', category.href).attr('style', 'outline-color: ' + category.color + ';');
    category_template.find('.section-tags__name').attr('style', 'background: ' + category.color + ';').text(category.name);
    category_template.find('.category-cover').attr('src', category.first_5_posts[0].cover_url).attr('alt', category.name);

    category.first_5_posts.forEach(post => {
        section_tags_content_html += '<h3 class="section-tags__title">' +
            '                <a href="' + post.href + '">' + post.title + '</a>' +
            '            </h3>'
    });

    category_template.find('.section-tags__content').html(section_tags_content_html);

    return category_template;
}

function load_posts_page() {
    let next_page = LoadMoreButton.data('next-page');
    let next_page_url = bj_apiUrl + '?page=' + next_page;
    let button_text = LoadMoreButton.text();
    let bj_result_container = $('#bj-results-container');

    LoadMoreButton.addClass('button--loading');
    LoadMoreButton.text("Loading");

    $.ajax({
        url: next_page_url,
        headers: {
            'X-Language': st_lang
        },
        success: function (response) {
            response.results.forEach(function (post) {
                const rendered_post = renderBinaryJournalPost(post);
                bj_result_container.append(rendered_post);
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

function load_relevant_categories(){
    let hh_result_container = $('#category__section__body__id');

    $.ajax({
        url: hh_apiUrl,
        headers: {
            'X-Language': st_lang
        },
        success: function (response){
            response.results.forEach(function (category) {
                const rendered_category = render_hackers_heaven_category(category);
                hh_result_container.append(rendered_category);
            });
        },
    });
}

$( document ).ready(function() {

    load_posts_page();
    load_relevant_categories();

    LoadMoreButton.on('click', load_posts_page);

})