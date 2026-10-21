# 7. Server-rendered lists of posts, with htmx for "Load more"

- **Status:** Accepted
- **Date:** 2026-10-21

## Context

The home's lists of posts, The Binary Journal and Hacker's Haven, were built in the browser: once the page had
loaded, jQuery asked the JSON API for the posts and filled in `<template>` copies of the cards. That meant:

- Without JavaScript, or for a crawler that doesn't run it, the home had no posts at all.
- A failed request left "Load more" saying "Loading" for good.
- Each card existed twice, as a Django template and as a `<template>` for jQuery, and the API sent presentation
  for the latter (dates written out in the page's language, "5 min read").

The rest of the site is Django templates on top of a jQuery theme, and stays that way.

## Decision

Django renders every list of posts with the page. The home is paginated (`?page=N`) and "Load more" is a link to
the next page, so it works without JavaScript and each page has a canonical address.

[htmx](https://htmx.org) turns that link into a request for the next page's posts alone (`main:more-posts`, the same
card template, nothing else) and appends them; the response also replaces the link with the one after it. htmx is
vendored in `static/js/` at a pinned version, exactly as published on npm, and only the home loads it.

The JSON API stays for the live search and for the staff's writes, and returns raw data (ISO 8601 dates, minutes as
numbers): the search formats it in the browser, in the page's language.

Alternatives considered:

- **Keep building the lists in jQuery from the API**: the problems above stay, and the API keeps serving one page.
- **A single-page app (React or similar)**: a build step and a second codebase for a site of a handful of pages,
  which would still need server rendering for crawlers and link previews.
- **jQuery fetching the server's HTML**: no new library, but the same request, swap and error handling written by
  hand for every partial update; with htmx they are attributes in the template.
- **htmx from a CDN**: the Content-Security-Policy would have to allow another origin for scripts. Served by the site,
  `script-src 'self'` stays as it is.

## Consequences

- The home shows its posts on the first response, with or without JavaScript, and the API no longer depends on how
  any page looks.
- The home loads about 16 KB more (htmx, compressed). No other page does.
- Dependabot doesn't follow files in `static/`. Updating htmx means reading its changelog, replacing the file and
  its versioned name, and checking "Load more" again.
- htmx is told not to inject styles or evaluate code from attributes, which the policy would block anyway.
