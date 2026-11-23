# 8. Case studies in the repository

- **Status:** Accepted
- **Date:** 2026-11-23

## Context

The home becomes a page about Nestor's professional work, built around a few case studies (three to five), each
with its own page in English and Spanish: title, client and period, role, problem, solution, stack, result and a
link when there is one.

The posts already live in the database and are written in the admin. The cases are different:

- They are few and change rarely, and they are what recruiters and clients judge Nestor on, so each change deserves
  a review.
- Nothing about them may be made up. Each text has to be confirmed by Nestor before it is published, and until then
  it must never reach production, not even as placeholder text. Drafts still have to be visible somewhere to be
  reviewed.
- A later phase adds an assistant that answers questions from the CV and the published cases only.

## Decision

The cases live in the repository, as Python data in `main/cases.py`, and change through pull requests like the
code.

- Each translatable field holds its English and Spanish text, as the posts' `_en` and `_es` fields do. Names,
  stacks and links are written once.
- Every text is either a `draft()` or `confirmed()`, and a field nobody has written yet is `PENDING`.
- A case is published only when every one of its fields is confirmed. In development (`DEBUG`) every case is shown,
  with its drafts and pending fields marked, so they can be reviewed on the real page.
- Each case has its page at `/{lang}/cases/<slug>/` (`main:case-detail`), with the same slug in both languages, and
  is in the sitemap, with its canonical URL, `hreflang`, Open Graph data and schema.org data (`CreativeWork` by the
  site's `Person`). Unpublished cases are a 404 and stay out of the sitemap.

Alternatives considered:

- **A model edited in the admin**: changes without a deploy, like the posts. But the content would live only in the
  production database, out of version control and out of reviews; development and production would drift apart; a
  confirmed state per field means twice as many columns or a JSON field the admin edits poorly; and the tests would
  need fixtures to see any case at all.
- **Markdown files with front matter**: closer to how writers work, but it needs a front matter parser, a new
  dependency for a handful of short fields, and the confirmed state per field is clumsier to express.

## Consequences

- Changing a case is a pull request and a deploy. With a handful of cases that change rarely, that is the review
  they need anyway.
- What is published is decided by the code and checked by tests: a draft can't reach production by mistake, and
  the test suite fails if the cases' texts break the rules it checks (unique slugs, a title, prose in both
  languages, no em dashes).
- The texts are not gettext strings: each case carries both languages, and only the interface around it (labels,
  marks) goes through the translation catalog.
- The assistant planned for a later phase can read the published cases straight from `main/cases.py`.
