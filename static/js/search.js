const script = document.currentScript;
const apiUrl = script.getAttribute('data-api-url');
const lang = script.getAttribute('data-lang');

$(document).ready(function () {

    // =====================
    // Ajax Search
    // =====================

    // The API sends dates as ISO 8601: show them like the server does (localized_date, "dd MMM, yyyy", in UTC)
    const dateFormat = new Intl.DateTimeFormat(lang, {day: '2-digit', month: 'short', year: 'numeric', timeZone: 'UTC'});

    function formatDate(isoDate) {
        const parts = {};
        dateFormat.formatToParts(new Date(isoDate)).forEach(function (part) {
            parts[part.type] = part.value;
        });
        return parts.day + ' ' + parts.month + ', ' + parts.year;
    }

    function renderPost(post) {
        let post_template = $($('#search-result-post-template')[0].content).clone();

        // Posts without a cover have no image to show (its URLs are empty), like their cards on the server
        if (post.cover_urls.card) {
            post_template.find('.article__image').attr('href', post.url);
            post_template.find('.article__image__link').attr('src', post.cover_urls.card).attr('alt', post.title);
        } else {
            post_template.find('.article__head').remove();
        }
        if (post.category) {
            post_template.find('.article__tag').attr('href', post.category.url).text(post.category.name);
        } else {
            post_template.find('.article__tags').remove();
        }
        post_template.find('.article__title__link').attr('href', post.url).text(post.title);
        post_template.find('.article__excerpt').text(post.description);
        post_template.find('.article__date').attr('datetime', post.published_at).text(formatDate(post.published_at));
        post_template.find('.article__read-time').text(post.read_time);

        return post_template;
    }

    // The messages are templates in the page (lib/_search_result_template.html), so they come translated
    function showMessage(results_container, template_id) {
        results_container.empty().append($($('#' + template_id)[0].content).clone());
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
                if (!page.results.length) {
                    showMessage(results_container, 'search-no-results-template');
                    return;
                }
                results_container.empty();
                page.results.forEach(function (post) {
                    const rendered_post = renderPost(post);
                    results_container.append(rendered_post);
                });
            },
            error: function (xhr, status) {
                // Cancelled by a newer query, which shows its own results
                if (status === 'abort') {
                    return;
                }
                showMessage(results_container, 'search-error-template');
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
