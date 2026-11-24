# 8. Case studies in the repository

- **Status:** Accepted (revised 2026-11-23 for the new home)
- **Date:** 2026-11-23

## Context

The home becomes a page about Nestor's professional work, built around a handful of case studies in two groups,
each with its own page in English and Spanish: title, summary, a proof line, authorship, client and period, role,
problem, what was built, how it was built, stack, result, links and a screenshot when there is one.

The posts already live in the database and are written in the admin. The cases are different:

- They are few and change rarely, and they are what recruiters and clients judge Nestor on, so each change deserves
  a review.
- Nothing about them may be made up. Their only source is `docs/home-cases.md`, which Nestor reviewed, and what that
  document still marks as pending must never reach a page, not even as placeholder text. Unfinished cases still
  have to be visible somewhere to be reviewed.
- A later phase adds an assistant that answers questions from the CV and the published cases only.

## Decision

The cases live in the repository, as Python data in `main/cases.py`, and change through pull requests like the
code.

- Each text holds its English and Spanish version (`Text(en, es)`), as the posts' `_en` and `_es` fields do. Names,
  stacks and links are written once, and so are proof lines unless they hold words that need translating.
- A field `docs/home-cases.md` marks as pending is not loaded at all: it is `None` (or an empty list), and the
  templates leave out whatever a case doesn't have, renumbering the blocks of its page so there are no gaps.
- A case is published only when it is marked `published` and has a title, summary, problem and solution. In
  development (`DEBUG`) every case is shown, unpublished ones marked "development only", so they can be reviewed on
  the real page.
- Each case has its group (World Bank Group or other clients), its layout on the home (wide or normal) and its place
  in the list, which is the order the home shows it in and the order "Next case" follows.
- Each case has its page at `/{lang}/cases/<slug>/` (`main:case-detail`), with one English slug for both languages,
  and is in the sitemap, with its canonical URL, `hreflang`, Open Graph data and schema.org data (`CreativeWork` by
  the site's `Person`). Unpublished cases are a 404 and stay out of the sitemap.

Alternatives considered:

- **A model edited in the admin**: changes without a deploy, like the posts. But the content would live only in the
  production database, out of version control and out of reviews; development and production would drift apart;
  and the tests would need fixtures to see any case at all.
- **Markdown files with front matter**: closer to how writers work, but it needs a front matter parser, a new
  dependency for a handful of short fields.
- **A confirmed flag on every text** (the first version of this record): it guarded against unreviewed drafts, but
  the whole content is now reviewed at once in `docs/home-cases.md`, so the flag only added noise.

## Consequences

- Changing a case is a pull request and a deploy. With a handful of cases that change rarely, that is the review
  they need anyway.
- What is published is decided by the code and checked by tests: an unfinished case can't reach production by
  mistake, and the test suite fails if the cases' texts break the rules it checks (unique slugs, prose in both
  languages, no em dashes, no pending markers).
- The texts are not gettext strings: each case carries both languages, and only the interface around it (labels,
  marks) goes through the translation catalog.
- The assistant planned for a later phase can read the published cases straight from `main/cases.py`.
