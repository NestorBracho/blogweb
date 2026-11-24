# 9. An own layout for the main site

- **Status:** Accepted
- **Date:** 2026-11-23

## Context

The whole site used the Coderon Jekyll theme: its layout (`templates/base.html`), its stylesheet
(`static/css/main.css`) and its jQuery scripts (`static/js/common.js`). The theme is a blog theme. The new home
(`docs/home-redesign.md`) is a page about Nestor's professional work, with a design of its own
(`docs/home-design.md`, reference in `docs/design/`): terminal-like, square corners, type and 1px lines, the brand's
accent only as a mark. Its pages (home, cases, CV, contact, about and privacy) share nothing visual with the theme.

Restyling the theme to look like the new design would mean overriding most of a large vendored stylesheet, whose
rules would keep leaking in, and keeping its markup (rows, columns, widgets) that the design doesn't need. The blog
itself is due to move to `blog.nestorbracho.com` in a later phase and keeps the theme until then.

## Decision

The main site has its own layout and stylesheet, and the blog keeps the theme's:

- `templates/site.html`, with `templates/lib/_site_header.html` and `_site_footer.html`, is the layout of the home,
  the case pages, the CV, contact, about and privacy. It reuses the head the whole site shares
  (`lib/_main_meta_seo.html`, favicons, fonts, `js/theme.js`), so search engines and link previews see the same
  metadata as before.
- `static/css/site.css` holds the design as CSS variables (a light value under `:root` and a dark one under
  `[dark]:root`, dark being the default) and plain classes. Neither `main.css` nor `common.js` is loaded on these
  pages; `static/js/site.js` only drives the theme toggle.
- No inline scripts and no `style=` attributes in the new markup. The Content-Security-Policy still allows inline
  styles, for the blog's theme only.
- Everything works without JavaScript: the language switch is a form, the navigation wraps on narrow screens
  instead of opening a menu, and the theme toggle stays hidden.
- The blog's pages keep `templates/base.html`; their navigation only gains a link to the cases.

## Consequences

- Two layouts and two stylesheets to keep in step for what they share: the wordmark (styled in both `site.css` and
  `brand.css`), the honeypot field, the skip link. Tests check which stylesheet each page loads.
- The main site's pages carry far less CSS and no jQuery.
- Moving the blog to its own host later touches only the blog's layout.
- The about page and the privacy policy lose the theme's sidebar (newsletter sign-up, latest posts, topics); the
  blog's pages still have it.
