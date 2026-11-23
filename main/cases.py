"""
Case studies: the work the home shows and each case's own page (main:case-detail).

The content lives here, in the repository, and changes through pull requests
(docs/adr/0008-case-studies-in-the-repository.md). Every text starts as a draft that Nestor has to confirm: drafts
are shown only in development (DEBUG), marked as such, and a case is published only once every one of its fields is
confirmed. A field nobody has written yet is PENDING. Nothing unconfirmed ever reaches production, not even as
placeholder text.
"""

from dataclasses import dataclass, fields

from django.conf import settings
from django.urls import reverse

from blog.models import content_language


@dataclass(frozen=True)
class Text:
    """A field of a case in each language. `es` is left out for what reads the same in both (names, stacks, links)."""

    en: str
    es: str | None = None
    confirmed: bool = False

    def in_language(self, language):
        return self.es if language == 'es' and self.es is not None else self.en


def draft(en, es=None):
    """Written for Nestor to review: shown in development only."""
    return Text(en, es)


def confirmed(en, es=None):
    """Checked by Nestor: can be published."""
    return Text(en, es, confirmed=True)


class Pending:
    """A field nobody has written yet."""

    def __repr__(self):
        return 'PENDING'


PENDING = Pending()


@dataclass(frozen=True)
class Field:
    """A field as a page shows it: its text in the page's language and whether it is confirmed, a draft or pending."""

    text: str
    # 'confirmed', 'draft' or 'pending'
    state: str


@dataclass(frozen=True)
class Case:
    slug: str
    title: Text | Pending
    client: Text | Pending
    period: Text | Pending
    role: Text | Pending
    problem: Text | Pending
    solution: Text | Pending
    stack: Text | Pending
    result: Text | Pending
    # None: the case has nothing to link to
    link: Text | Pending | None = None

    def content_fields(self):
        """Every field but the slug, with its value."""
        return [(field.name, getattr(self, field.name)) for field in fields(self) if field.name != 'slug']

    def is_confirmed(self):
        return all(value is None or (isinstance(value, Text) and value.confirmed) for _, value in self.content_fields())

    def get_absolute_url(self):
        return reverse('main:case-detail', kwargs={'slug': self.slug})

    def localized(self):
        """The case in the page's language, each field as a Field (None for a link the case doesn't have)."""
        language = content_language()
        values = {'slug': self.slug, 'url': self.get_absolute_url(), 'is_confirmed': self.is_confirmed()}
        for name, value in self.content_fields():
            if value is None:
                values[name] = None
            elif isinstance(value, Pending):
                values[name] = Field('', 'pending')
            else:
                values[name] = Field(value.in_language(language), 'confirmed' if value.confirmed else 'draft')
        return LocalizedCase(**values)


@dataclass(frozen=True)
class LocalizedCase:
    slug: str
    url: str
    is_confirmed: bool
    title: Field
    client: Field
    period: Field
    role: Field
    problem: Field
    solution: Field
    stack: Field
    result: Field
    link: Field | None


def drafts_visible():
    """Drafts and cases with pending fields are for development only."""
    return settings.DEBUG


def visible_cases():
    """The cases this site shows, in the order the home lists them."""
    return [case for case in CASES if drafts_visible() or case.is_confirmed()]


def get_case(slug):
    return next((case for case in visible_cases() if case.slug == slug), None)


# Drafts from Nestor's brief for the new home (kept out of the repository) and the CV page (main/_lib/_cv_*.html),
# for Nestor to review. Results, periods and anything else he hasn't given are PENDING: nothing here is made up.
CASES = [
    Case(
        slug='community-driven-development',
        title=draft('Community-Driven Development platform', 'Plataforma de Desarrollo Impulsado por la Comunidad'),
        client=draft('World Bank Group', 'Grupo Banco Mundial'),
        period=PENDING,
        role=draft(
            'Backend architecture and development. Led the 2024 phase.',
            'Arquitectura backend y desarrollo. Lideré la fase de 2024.',
        ),
        problem=draft(
            'Communities and governments in several African countries need to communicate and manage the resources '
            'of local development projects together.',
            'Comunidades y gobiernos de varios países africanos necesitan comunicarse y gestionar juntos los recursos '
            'de proyectos de desarrollo local.',
        ),
        solution=draft(
            'The backend architecture and development of the Community-Driven Development (CDD) platform. The 2024 '
            'phase, which I led, focused on scaling, new data analytics tools and usability.',
            'La arquitectura backend y el desarrollo de la plataforma de Desarrollo Impulsado por la Comunidad (CDD). '
            'La fase de 2024, que lideré, se centró en escalabilidad, nuevas herramientas de analítica de datos y '
            'usabilidad.',
        ),
        stack=draft('Python, Django, Django REST Framework, PostgreSQL, Angular, AWS'),
        result=PENDING,
        link=PENDING,
    ),
    Case(
        slug='offline-first-participatory-monitoring',
        title=draft('Offline-first participatory monitoring', 'Monitoreo participativo offline-first'),
        client=PENDING,
        period=PENDING,
        role=draft('Architecture and development', 'Arquitectura y desarrollo'),
        problem=PENDING,
        solution=draft(
            'A Django REST backend and a React Native (Expo) app that keep working without a connection: JWT '
            'authentication, a versioned mobile API, batch sync contracts, local SQLite storage and a dynamic form '
            'engine. Built AI-first with Claude Code and the BMAD Method, backed by contract-locked testing.',
            'Un backend en Django REST y una app en React Native (Expo) que siguen funcionando sin conexión: '
            'autenticación JWT, API móvil versionada, contratos de sincronización por lotes, almacenamiento local en '
            'SQLite y un motor de formularios dinámicos. Construida con un enfoque AI-first con Claude Code y el BMAD '
            'Method, respaldada por testing con contratos fijados.',
        ),
        stack=draft('Python, Django REST Framework, React Native, Expo, SQLite, OpenAPI, pytest, Jest, Maestro'),
        result=PENDING,
        link=PENDING,
    ),
    Case(
        slug='selia-payments-and-b2b',
        title=draft('Payments and B2B platform for Selia', 'Plataforma de pagos y B2B de Selia'),
        client=draft('Selia'),
        period=draft('2022 to 2023', '2022 a 2023'),
        role=draft(
            'Senior Full Stack Engineer, responsible for the backend architecture',
            'Senior Full Stack Engineer, responsable de la arquitectura backend',
        ),
        problem=PENDING,
        solution=draft(
            "Designed and built Selia's payment platform and its B2B platform, with Stripe as the payment gateway, "
            'and optimized the infrastructure for scalability and reliability as the business grew.',
            'Diseño y construcción de la plataforma de pagos y de la plataforma B2B de Selia, con Stripe como '
            'pasarela de pago, y optimización de la infraestructura para ganar escalabilidad y fiabilidad a medida '
            'que crecía el negocio.',
        ),
        stack=draft('Python, Django, Django REST Framework, PostgreSQL, Stripe, AWS'),
        result=PENDING,
        link=PENDING,
    ),
    Case(
        slug='logistics-wms',
        title=draft(
            'Warehouse management system for a logistics company',
            'Sistema de gestión de almacenes para una empresa de logística',
        ),
        # Anonymous until the client agrees to be named
        client=draft('A logistics company', 'Una empresa de logística'),
        period=PENDING,
        role=PENDING,
        problem=PENDING,
        solution=draft(
            'A warehouse management system (WMS) developed entirely with AI agents.',
            'Un sistema de gestión de almacenes (WMS) desarrollado por completo con agentes de IA.',
        ),
        stack=PENDING,
        result=PENDING,
        link=PENDING,
    ),
    Case(
        slug='nestorbracho-com',
        title=draft('nestorbracho.com, this site', 'nestorbracho.com, este sitio'),
        client=draft('Personal project', 'Proyecto personal'),
        period=draft('2025 to 2026', '2025 a 2026'),
        role=draft(
            'Architecture, development, deployment and operations. The visual design is the Coderon theme.',
            'Arquitectura, desarrollo, despliegue y operación. El diseño visual es el theme Coderon.',
        ),
        problem=draft(
            'A personal site and blog in English and Spanish that also shows how I build and run web '
            'applications, without paying for hosting.',
            'Un sitio personal y un blog en inglés y español que muestran también cómo construyo y opero '
            'aplicaciones web, sin pagar por el alojamiento.',
        ),
        solution=draft(
            'Django with pages rendered on the server and htmx, a REST API, tests and linting in CI, and a hardened '
            'deployment on a single free-tier VM behind Cloudflare, with SQLite and off-site backups. Each '
            'structural decision is recorded in an architecture decision record.',
            'Django con páginas renderizadas en el servidor y htmx, una API REST, tests y linting en CI, y un '
            'despliegue endurecido en una sola VM gratuita detrás de Cloudflare, con SQLite y copias de seguridad '
            'fuera del servidor. Cada decisión estructural queda registrada en un ADR.',
        ),
        stack=draft('Python, Django, Django REST Framework, htmx, SQLite, nginx, Gunicorn, Cloudflare, GitHub Actions'),
        result=draft(
            'In production at no hosting cost, with every change checked in CI and deployed automatically.',
            'En producción sin coste de alojamiento, con cada cambio verificado en CI y desplegado automáticamente.',
        ),
        link=draft('https://github.com/NestorBracho/blogweb'),
    ),
]
