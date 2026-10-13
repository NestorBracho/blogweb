const script = document.currentScript;
const apiUrl = script.getAttribute('data-api-url');
const lang = script.getAttribute('data-lang');

$(document).ready(function () {

    // =====================
    // Ajax Search
    // =====================

    function renderPost(post) {
        let post_template = $($('#search-result-post-template')[0].content).clone();

        post_template.find('.article__image').attr('href', post.href);
        post_template.find('.article__image__link').attr('src', post.cover_url).attr('alt', post.title);
        post_template.find('.article__tag').attr('href', post.category_href).text(post.category);
        post_template.find('.article__title__link').attr('href', post.href).text(post.title);
        post_template.find('.article__excerpt').text(post.description);
        post_template.find('.article__date').attr('datetime', post.timestamp).text(post.user_friendly_date);
        post_template.find('.article__minutes').text(post.read_time);

        return post_template;
    }

    const SEARCH_DEBOUNCE_MS = 300;
    const SEARCH_PAGE_SIZE = 10;
    let searchTimeout = null;
    let searchRequest = null;

    function search(query) {
        let results_container = $('#js-results-container');

        // A slow response for an older query must never overwrite a newer one
        if (searchRequest) {
            searchRequest.abort();
        }
        if (!query.trim()) {
            results_container.empty();
            return;
        }
        searchRequest = $.ajax({
            url: apiUrl,
            data: {search: query, page_size: SEARCH_PAGE_SIZE},
            headers: {
                'X-Language': lang
            },
            success: function (page) {
                results_container.empty();
                page.results.forEach(function (post) {
                    const rendered_post = renderPost(post);
                    results_container.append(rendered_post);
                });
            },
            statusCode: {
                404: function () {
                    results_container.empty();
                }
            },
            error: function (xhr) {
            },
        });
    }

    $('#js-search-input').on('input', function () {
        const query = $(this).val();
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(function () {
            search(query);
        }, SEARCH_DEBOUNCE_MS);
    })

})