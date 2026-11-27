"""
The service pages (main:service-detail) and the "How I work" page's title and description.

The only source of their text is docs/services-content.md: nothing here is made up. The English text is the msgid and
the Spanish one lives in locale/es (gettext), so each page reads in the language of its URL. `%(years)s` is the
computed years of experience (config.context_processors.years_of_experience), as everywhere else on the site.
"""

import dataclasses
from dataclasses import dataclass

from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from config.context_processors import years_of_experience

from . import cases


@dataclass(frozen=True)
class Question:
    """A question of a page's FAQ and its answer."""

    question: str
    answer: str


@dataclass(frozen=True)
class Service:
    slug: str
    # The short name: the home's "How I can help" offer title
    name: str
    # <title>, meta description and Open Graph
    title: str
    description: str
    heading: str
    # The first paragraph: what, for whom and a proof with a number
    answer: str
    # "What I do"
    points: tuple[str, ...]
    # The cases the doc lists for it, by slug; only the visible ones are shown
    cases: tuple[str, ...]
    # The line above the cases' cards, when the doc gives one
    cases_lead: str | None
    # The line that leads to the How I work page
    how_i_work: str
    faq: tuple[Question, ...]
    # "Examples", when the doc gives them
    examples: tuple[str, ...] = ()

    def get_absolute_url(self):
        return reverse('main:service-detail', kwargs={'slug': self.slug})

    def localized(self):
        """The service in the page's language, with the years filled in and its visible cases, localized."""

        def text(value):
            # Only where the years go: a literal % elsewhere stays as written
            value = str(value)
            return value % {'years': years_of_experience()} if '%(years)s' in value else value

        shown = (cases.get_case(slug) for slug in self.cases)
        return LocalizedService(
            slug=self.slug,
            url=self.get_absolute_url(),
            name=text(self.name),
            title=text(self.title),
            description=text(self.description),
            heading=text(self.heading),
            answer=text(self.answer),
            points=[text(point) for point in self.points],
            examples=[text(example) for example in self.examples],
            cases_lead=text(self.cases_lead) if self.cases_lead else '',
            # Drafts are left out in production; here every card is a normal one, side by side
            cases=[dataclasses.replace(case.localized(), is_wide=False) for case in shown if case is not None],
            how_i_work=text(self.how_i_work),
            faq=[Question(text(item.question), text(item.answer)) for item in self.faq],
        )


@dataclass(frozen=True)
class LocalizedService:
    slug: str
    url: str
    name: str
    title: str
    description: str
    heading: str
    answer: str
    points: list
    examples: list
    cases_lead: str
    cases: list
    how_i_work: str
    faq: list


def get_service(slug):
    return next((service for service in SERVICES if service.slug == slug), None)


def services_for_case(slug):
    """
    The services whose pages list this case, in the order of SERVICES, as [{'name', 'url'}] in the page's language:
    the inverse of `Service.cases`, so the case page and the service pages cannot disagree.
    """
    return [
        {'name': str(service.name), 'url': service.get_absolute_url()} for service in SERVICES if slug in service.cases
    ]


# The How I work page (main:how-i-work): its title and description, for the page and for /llms.txt
HOW_I_WORK_TITLE = _('How I build software with AI agents · Nestor Bracho')
HOW_I_WORK_DESCRIPTION = _(
    'Spec-driven development with AI agents: specification, agents with roles, human review and verification. With '
    'a real case and its numbers.'
)

# Its FAQ: the page shows it and its FAQPage structured data reads it, so the two cannot drift
HOW_I_WORK_FAQ = (
    Question(
        _('What is spec-driven development?'),
        _(
            'Writing down first what has to be built and how you will know it is right, and then building it. With AI '
            'agents, it is what turns a code generator into a predictable team: the agent works against the '
            'specification and the review checks against it.'
        ),
    ),
    Question(
        _('What is the BMAD method?'),
        _(
            'An open-source method for AI agent-driven development that splits the work into roles (analyst, product, '
            'architecture, development, review) and produces documents that build on each other: brief, PRD, '
            'architecture, epics and stories.'
        ),
    ),
    Question(
        _('Is code written by agents reliable?'),
        _(
            'As reliable as the review and the tests around it. That is why I review every change and nothing is '
            'merged without passing the tests and continuous integration.'
        ),
    ),
    Question(
        _('Can I use this method with my team?'),
        _(
            'Yes. I offer training and hands-on support so your team can work with AI agents under specification and '
            'review, on your own projects.'
        ),
    ),
)


def how_i_work_faq():
    """The How I work FAQ in the page's language."""
    return [Question(str(item.question), str(item.answer)) for item in HOW_I_WORK_FAQ]


# The cases index (main:cases), from the phase 2b copy; its H1 is the home's cases title
CASES_INDEX_TITLE = _('Django and Python case studies · Nestor Bracho')
CASES_INDEX_DESCRIPTION = _(
    'Case studies of Django backends, APIs and products built for the World Bank Group and private clients: the '
    'problem, the solution and the result.'
)
CASES_INDEX_INTRO = _(
    'Each case explains the problem, what I built, how and what changed. Most are Django backends with their API; '
    'some include the frontend and the AI pieces.'
)

SERVICES = [
    Service(
        slug='django-backend',
        name=_('Django backend'),
        title=_('Freelance Django developer in Madrid · Nestor Bracho'),
        description=_(
            'Freelance Django and Django REST Framework developer in Madrid. More than %(years)s years designing APIs, '
            'data models and production backends.'
        ),
        heading=_('Freelance Django developer: APIs and backends that grow without a rewrite'),
        answer=_(
            'I design and build backends with Python, Django and Django REST Framework for products that need to grow '
            'without being rebuilt. I have more than %(years)s years with Django: three of them as an architect and '
            'developer for the World Bank Group, and now as a freelancer based in Madrid, working remotely or hybrid.'
        ),
        points=(
            _('REST API design with Django REST Framework, with contracts locked in OpenAPI.'),
            _('Data modeling and query optimization in PostgreSQL.'),
            _(
                'Third-party integrations: Stripe payments, WhatsApp Business API, Idealista, SMS and email (Twilio, '
                'SendGrid, Mailchimp).'
            ),
            _('Background jobs with Celery and Redis.'),
            _(
                'AWS infrastructure (EC2, RDS, S3, Elastic Beanstalk, Lambda) with Terraform and CI/CD on GitHub '
                'Actions.'
            ),
            _('Work on existing Django codebases: new features, maintenance and version upgrades.'),
        ),
        cases=('local-development-portal', 'mid-term-rental-crm', 'e3-django-dynamic-forms'),
        cases_lead=_('Three Django backends in production.'),
        how_i_work=_(
            'I write the specification, AI agents implement it and I review every change before it is merged.'
        ),
        faq=(
            Question(
                _('Can you work on an existing Django project?'),
                _(
                    "Yes. Much of my work has been on other people's code, such as Nokia's Zina CRM/ERP or the "
                    'management system I built the mid-term rental CRM into. I start by reading the code and the '
                    'tests, and propose changes in phases.'
                ),
            ),
            Question(
                _('Do you only do Django, or the frontend too?'),
                _(
                    'Backend is my specialty, but I also deliver the interface when needed: HTMX in Django templates, '
                    'Angular, or React Native for mobile.'
                ),
            ),
            Question(
                _('Do you work remotely?'),
                _('Yes. I live in Madrid and work remotely or hybrid, in Spanish or English.'),
            ),
            Question(
                _('What about quality if you use AI agents?'),
                _(
                    'No change is merged until I have reviewed it and it has passed the tests and continuous '
                    'integration. The mid-term rental CRM module, built this way, has more than 2,000 automated tests.'
                ),
            ),
            Question(
                _('How do you quote a project?'),
                _(
                    'By phase. The first phase is the specification, and each phase is quoted once its scope is '
                    'defined. Tell me about the project and I will prepare a proposal.'
                ),
            ),
        ),
    ),
    Service(
        slug='ai-integration',
        name=_('AI in existing products'),
        title=_('AI and LLM integration for Django products · Nestor Bracho'),
        description=_(
            'I integrate LLMs and Hugging Face models into products already in production, without a rewrite. With '
            'caching, graceful degradation and tests.'
        ),
        heading=_('AI in your current product, without a rewrite'),
        answer=_(
            'I integrate LLMs and Hugging Face models into systems that are already in production, as one more part '
            'of the backend rather than a separate project. Most recently: a financial analysis service that explains '
            'the dashboards of a rental management platform in plain language.'
        ),
        points=(
            _('LLM integration through APIs (OpenAI) with prompt engineering and tool calling.'),
            _('Hugging Face models in content processing pipelines.'),
            _(
                'Production-ready service design: per-client context, response caching and graceful degradation when '
                'the model is unavailable.'
            ),
            _(
                'LLM analysis inside existing dashboards, such as the diagnostics dashboard of a grievance redress '
                'system.'
            ),
            _('Integration into your existing Django backend, with its permissions, its data and its tests.'),
        ),
        examples=(
            _(
                'Vacation and mid-term rental management company: a financial analysis service using an LLM that '
                'generates insights on revenue, occupancy and channels in the dashboards. In production.'
            ),
            _(
                'World Bank Group: an LLM analysis layer in the diagnostics dashboard of a grievance redress system. '
                'In production.'
            ),
            _(
                'Ekwi-three: Hugging Face models in the pipeline of a content management platform that processes and '
                'organizes large volumes of resources.'
            ),
        ),
        cases=('mid-term-rental-crm', 'local-development-portal'),
        cases_lead=None,
        how_i_work=_('The integration is specified and reviewed like any other backend feature.'),
        faq=(
            Question(
                _('Do I need to rebuild my product to add AI?'),
                _(
                    'No. The integration goes in as one more backend service that reads the data you already have. In '
                    "both production cases the product's architecture did not change."
                ),
            ),
            Question(
                _('What if the model fails or is slow?'),
                _(
                    'The service caches responses and, if the model is unavailable, the dashboard keeps working '
                    "without the analysis. Users don't see an error."
                ),
            ),
            Question(
                _('Which models do you work with?'),
                _(
                    'I have integrated the OpenAI API and Hugging Face models. The choice depends on the case: cost, '
                    'latency and where the data is allowed to go.'
                ),
            ),
            Question(
                _("What about your data and your customers' data?"),
                _(
                    'It stays confidential. If I later use the project as a reference, I do it anonymized, like the '
                    "clients in this site's case studies."
                ),
            ),
        ),
    ),
    Service(
        slug='end-to-end-product',
        name=_('End-to-end product'),
        title=_('End-to-end product development · Nestor Bracho'),
        description=_(
            'From specification to deployment: backend, frontend, testing and release, with one person accountable '
            'and AI agent-driven development.'
        ),
        heading=_('From specification to production, with one person accountable'),
        answer=_(
            'I take a product from specification to production: backend, frontend, testing and deployment. I work '
            'with AI agents under specification and human review; that is how I delivered the first five epics of a '
            'CRM, 19 stories, in two weeks.'
        ),
        points=(
            _('Specification before code: PRD, architecture, epics and one spec per story, with acceptance criteria.'),
            _('System architecture and a stack chosen for the problem, not the other way round.'),
            _('Django backend, HTMX or Angular interfaces, and offline-first mobile apps with React Native and Expo.'),
            _('Automated tests (pytest, Jest, Maestro) and continuous integration on every change.'),
            _('Deployment on AWS or on minimal infrastructure behind Cloudflare, with off-site backups.'),
            _(
                'Handover to the team: the code, the specification and the architecture decisions stay in the '
                'repository.'
            ),
        ),
        cases=('mid-term-rental-crm', 'participatory-monitoring-app', 'this-site'),
        cases_lead=_('Three products built end to end.'),
        how_i_work=_('This service is the full method in practice.'),
        faq=(
            Question(
                _('What do you need to get started?'),
                _(
                    'The problem you want to solve and who has it. From there I write the specification with your team '
                    'and split it into phases that can be reviewed and delivered on their own.'
                ),
            ),
            Question(
                _('What do I get at the end?'),
                _(
                    'The product in production, the code with its tests and the specification in the same repository. '
                    'Any developer, or any agent, can carry on from there.'
                ),
            ),
            Question(
                _('Do you build mobile apps too?'),
                _(
                    'Yes, with React Native and Expo. The participatory monitoring app works offline and syncs when '
                    'the network comes back.'
                ),
            ),
            Question(
                _('How long does a product take?'),
                _(
                    'It depends on the scope, which is why the first deliverable is the phased specification. For '
                    'reference, the first five epics of the mid-term rental CRM, 19 stories, were implemented in two '
                    'weeks.'
                ),
            ),
        ),
    ),
]
