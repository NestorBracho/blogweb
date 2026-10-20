# 6. The language in the URL

- **Status:** Accepted
- **Date:** 2026-10-20

## Context

Every page used to have a single address for both languages. Django picked English or Spanish from the language
cookie or the browser's `Accept-Language`, and Spanish when there was neither (`LANGUAGE_CODE` was `es`).

That served visitors who had chosen a language, but not the readers a personal site shown to recruiters needs most:

- Crawlers and link previews send no `Accept-Language`. Google, and LinkedIn when a link is shared, only ever saw
  Spanish. They couldn't find the English pages at all: one address can't be indexed in two languages, and there was
  no way to point to the other version.
- Visitors whose browser asks for a third language, such as a recruiter in Berlin, got Spanish.

## Decision

Put the language in the path with Django's `i18n_patterns`, `/en/…` and `/es/…` for every page, and make English the
default language.

- An address without a language (the bare domain, and every link shared before this change) is redirected (302) by
  `LocaleMiddleware` to the visitor's language: the cookie set by the language switcher, then `Accept-Language`, then
  English. No code of ours decides it.
- The admin, the API, `sitemap.xml`, `robots.txt` and `favicon.ico` stay at the root. The API takes its language
  from the `X-Language` header the page sends, so writes are never redirected.
- The switcher (`set_language`) lives under the prefix too. Django resolves the page the form was sent from in the
  active language, so at the root it couldn't translate a page whose language differed from the cookie.
- The sitemap lists every page in both languages and links the versions to each other, with the address without a
  language as `x-default`.

Alternatives considered:

- **English at the root and Spanish under `/es/`** (`prefix_default_language=False`): shorter English addresses, but
  Django then serves every address without a prefix in English. Spanish browsers landing on the domain would get
  English unless a middleware of our own redirected them.
- **One address per page with English as the default**: link previews would be in English, but Google still
  couldn't index the Spanish pages or tell the two versions apart.

## Consequences

- Each address has one language, so a page can be indexed, cached and shared in it. Pages under a prefix no longer
  vary with `Accept-Language`.
- An address without a language costs a redirect, and Django renders the 404 page (two sidebar queries) before
  turning it into that redirect. The site's own links never point there; only old and typed links do.
- The redirect depends on the visitor (`Vary: Accept-Language, Cookie`). Cloudflare ignores `Vary` on HTML, so a
  "Cache Everything" rule must never cover addresses without a language. Today it only caches static files and
  images ([ADR 3](0003-cloudflare-in-front-of-the-origin.md)).
- Each language has its own feed, `/en/feed.xml` and `/es/feed.xml`. Its item links, which are also their GUIDs,
  changed once with this move, so readers may show the existing posts again.
- A form on a page opened before the deploy posts to the old address; the redirect turns that post into a GET, and
  it is lost once. Newsletter confirmation links already sent keep working through the redirect.
- The deploy health check asks for `/en/` and checks the redirect at the root.
