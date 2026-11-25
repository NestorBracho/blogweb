"""
Case studies: the work the home shows and each case's own page (main:case-detail).

The content lives here, in the repository, and changes through pull requests
(docs/adr/0008-case-studies-in-the-repository.md). Its only source is docs/home-cases.md: nothing here is made up,
and a field that document still marks as pending is simply left out (None, or an empty tuple). A case is published
only when it is marked `published` and has a title, summary, problem and solution; the others are drafts, shown
only in development (DEBUG) and marked as such.
"""

from dataclasses import dataclass

from django.conf import settings
from django.urls import reverse

from blog.models import content_language

WORLD_BANK = 'world-bank'
OTHER = 'other'

WIDE = 'wide'
NORMAL = 'normal'


@dataclass(frozen=True)
class Text:
    """
    A text in each language. `es` is left out for what reads the same in both: names, stacks, and proof lines unless
    they hold words that need translating.
    """

    en: str
    es: str | None = None

    def in_language(self, language):
        return self.es if language == 'es' and self.es is not None else self.en


@dataclass(frozen=True)
class Link:
    """An external link: a name that reads the same in both languages (PyPI, GitHub) and its address."""

    label: str
    url: str


@dataclass(frozen=True)
class Screenshot:
    """An image under static/ and its alternative text."""

    path: str
    alt: Text


@dataclass(frozen=True)
class Case:
    slug: str
    group: str
    layout: str
    published: bool
    title: Text
    summary: Text | None = None
    proof_line: Text | None = None
    # Short label: "Team", "Sole author"...
    authorship: Text | None = None
    # The metadata line of the home's card: client and period
    card_meta: Text | None = None
    client: Text | None = None
    period: Text | None = None
    role: Text | None = None
    problem: Text | None = None
    solution: tuple[Text, ...] = ()
    how_built: Text | None = None
    result: Text | None = None
    # Names read the same in both languages; a Text for the odd one that doesn't
    stack: tuple[str | Text, ...] = ()
    links: tuple[Link, ...] = ()
    screenshot: Screenshot | None = None

    # The texts each language has its own version of
    TEXT_FIELDS = (
        'title',
        'summary',
        'proof_line',
        'authorship',
        'card_meta',
        'client',
        'period',
        'role',
        'problem',
        'how_built',
        'result',
    )

    def is_published(self):
        return bool(self.published and self.title and self.summary and self.problem and self.solution)

    def texts(self):
        """Every text of the case, as (field name, Text), the solution's points included."""
        named = [(name, getattr(self, name)) for name in self.TEXT_FIELDS if getattr(self, name) is not None]
        return [*named, *(('solution', point) for point in self.solution)]

    def get_absolute_url(self):
        return reverse('main:case-detail', kwargs={'slug': self.slug})

    def localized(self):
        """The case in the page's language, as plain strings for the templates."""
        language = content_language()

        def text(value):
            return value.in_language(language) if value is not None else ''

        return LocalizedCase(
            slug=self.slug,
            url=self.get_absolute_url(),
            group=self.group,
            is_wide=self.layout == WIDE,
            is_published=self.is_published(),
            solution=[point.in_language(language) for point in self.solution],
            stack=[item.in_language(language) if isinstance(item, Text) else item for item in self.stack],
            links=list(self.links),
            screenshot=(
                {'path': self.screenshot.path, 'alt': self.screenshot.alt.in_language(language)}
                if self.screenshot
                else None
            ),
            **{name: text(getattr(self, name)) for name in self.TEXT_FIELDS},
        )


@dataclass(frozen=True)
class LocalizedCase:
    slug: str
    url: str
    group: str
    is_wide: bool
    is_published: bool
    title: str
    summary: str
    proof_line: str
    authorship: str
    card_meta: str
    client: str
    period: str
    role: str
    problem: str
    how_built: str
    result: str
    solution: list
    stack: list
    links: list
    screenshot: dict | None


def drafts_visible():
    """Unpublished cases are for development only."""
    return settings.DEBUG


def visible_cases():
    """The cases this site shows, in the order of CASES."""
    return [case for case in CASES if drafts_visible() or case.is_published()]


def get_case(slug):
    return next((case for case in visible_cases() if case.slug == slug), None)


def next_case(case):
    """The case after this one among those the site shows; the last one leads back to the first."""
    shown = visible_cases()
    return shown[(shown.index(case) + 1) % len(shown)]


# The home's groups, in order, each with its label
GROUPS = [WORLD_BANK, OTHER]


def grouped_cases():
    """The visible cases of each group, localized, wide cards first: [(group, [wide...], [normal...])]."""
    shown = [case.localized() for case in visible_cases()]
    groups = []
    for group in GROUPS:
        in_group = [case for case in shown if case.group == group]
        if in_group:
            wide = [case for case in in_group if case.is_wide]
            normal = [case for case in in_group if not case.is_wide]
            groups.append((group, wide, normal))
    return groups


GITHUB = 'GitHub'

# His own published work, which the structured data also lists among his profiles (config/structured_data.py)
E3_PYPI_URL = 'https://pypi.org/project/e3-django-dynamic-forms/'
SITE_REPO_URL = 'https://github.com/NestorBracho/blogweb'

CASES = [
    Case(
        slug='local-development-portal',
        group=WORLD_BANK,
        layout=WIDE,
        published=True,
        authorship=Text('Team', 'Equipo'),
        title=Text(
            'Local development portal for community-driven programs',
            'Portal de desarrollo local para programas comunitarios',
        ),
        proof_line=Text(
            'Django · PostgreSQL · CouchDB · 2 languages · 2023 to 2026',
            'Django · PostgreSQL · CouchDB · 2 idiomas · 2023 a 2026',
        ),
        summary=Text(
            "A platform that makes each village's investment priorities visible to the organizations that can fund "
            'them. Funders filter, select sub-projects, submit them for review and track their status.',
            'Una plataforma donde las prioridades de inversión de cada aldea se vuelven visibles para quien puede '
            'financiarlas. El financiador filtra, selecciona subproyectos, los envía a revisión y sigue su estado.',
        ),
        client=Text('World Bank Group', 'Grupo Banco Mundial'),
        period=Text('2023 to 2026', '2023 a 2026'),
        role=Text('Fullstack developer in a distributed team', 'Desarrollador fullstack en un equipo distribuido'),
        problem=Text(
            'In community-driven development programs, each village defines its own investment priorities. That '
            'information lived in the internal management system, but funding organizations had nowhere to browse '
            'it, choose what to support, or follow what happened next.',
            'En los programas de desarrollo impulsado por la comunidad, cada aldea define sus prioridades de '
            'inversión. Esa información existía en el sistema de gestión interno, pero las organizaciones que '
            'financian no tenían dónde consultarla, elegir qué apoyar ni seguir qué pasó después.',
        ),
        solution=(
            Text(
                "Defined the portal's initial data model: administrative levels, projects, sectors, investments, "
                'packages and attachments.',
                'Definí el modelo de datos inicial del portal: niveles administrativos, proyectos, sectores, '
                'inversiones, paquetes y adjuntos.',
            ),
            Text(
                "Built the funder's main flow: investment list with dynamic filters, cart, package submission and "
                'tracking.',
                'Construí el flujo principal del financiador: listado de inversiones con filtros dinámicos, carrito, '
                'envío del paquete y seguimiento.',
            ),
            Text(
                'Built the moderator review, with reasoned approval or rejection, role-based permissions and email '
                'notifications in English and French.',
                'Construí la revisión por moderador, con aprobación o rechazo razonado, permisos por rol y '
                'notificaciones por correo en inglés y francés.',
            ),
            Text(
                'Moved the investment list to server-side processing when data volume required it.',
                'Llevé el listado de inversiones a procesamiento en servidor cuando el volumen de datos lo exigió.',
            ),
            Text(
                'Added the geographic layer: Mapbox maps, a climate map by administrative level and coordinate '
                'syncing.',
                'Añadí la capa geográfica: mapas con Mapbox, mapa climático por nivel administrativo y '
                'sincronización de coordenadas.',
            ),
            Text(
                'Worked on data that flows from the management system (CouchDB) into PostgreSQL through sync jobs.',
                'Trabajé sobre datos que llegan desde el sistema de gestión (CouchDB) hacia PostgreSQL mediante '
                'sincronizaciones.',
            ),
            Text(
                'For a grievance redress system of the same client, designed the SMS and email notifications module '
                "(Twilio, Africa's Talking, SendGrid and Mailchimp), which switches provider through configuration, "
                'and an LLM analysis layer in its diagnostics dashboard. Both are running in production.',
                'Para un sistema de gestión de quejas del mismo cliente, diseñé el módulo de notificaciones por SMS y '
                "email (Twilio, Africa's Talking, SendGrid y Mailchimp), que cambia de proveedor por configuración, y "
                'una capa de análisis con un LLM en su panel de diagnóstico. Ambos están en producción.',
            ),
        ),
        stack=(
            'Python',
            'Django',
            'Django REST Framework',
            'PostgreSQL',
            'CouchDB',
            'Celery',
            'Redis',
            'HTMX',
            'Mapbox',
            'AWS S3',
        ),
        result=Text(
            "A bilingual portal covering the full path, from a village's priority to an approved, tracked investment.",
            'Un portal bilingüe que cubre el recorrido completo, desde la prioridad de una aldea hasta la inversión '
            'aprobada y en seguimiento.',
        ),
    ),
    Case(
        slug='participatory-monitoring-app',
        group=WORLD_BANK,
        layout=NORMAL,
        published=True,
        authorship=Text('Lead author', 'Autor principal'),
        title=Text(
            'Offline-first mobile app for participatory monitoring',
            'App móvil offline-first para monitoreo participativo',
        ),
        proof_line=Text(
            'React Native · Expo · SQLite · GPS + photo · EN/FR',
            'React Native · Expo · SQLite · GPS + foto · EN/FR',
        ),
        summary=Text(
            "Village committees check the state of their community's infrastructure on site. The app works without "
            'a connection: every visit is stored on the phone with its answers, coordinates and photo.',
            'Los comités de aldea verifican sobre el terreno el estado de las obras de su comunidad. La app funciona '
            'sin conexión: cada visita se guarda en el teléfono con sus respuestas, coordenadas y foto.',
        ),
        client=Text('World Bank Group', 'Grupo Banco Mundial'),
        period=Text('2026'),
        role=Text(
            'Architecture design and development of the app, almost entirely solo, using AI agent-assisted development',
            'Diseño de la arquitectura y desarrollo de la app, prácticamente en solitario, con desarrollo asistido '
            'por agentes de IA',
        ),
        problem=Text(
            'Nobody knows whether a piece of infrastructure works better than the community that uses it. But those '
            'communities are often where coverage fails, so an app that depends on the network cannot collect that '
            'information.',
            'Quien mejor sabe si una obra funciona es la comunidad que la usa. Pero esas comunidades suelen estar '
            'donde la cobertura falla, así que una app que dependa de la red no sirve para recoger esa información.',
        ),
        solution=(
            Text(
                'Data lives on the device first. The app uses local SQLite with migrations that apply themselves on '
                'startup.',
                'Los datos viven primero en el dispositivo. La app usa SQLite local con migraciones que se aplican '
                'solas al arrancar.',
            ),
            Text(
                'Every visit follows a guided flow: task sheet with a map, step-by-step survey, review with GPS '
                'capture and a photo as evidence, and confirmation.',
                'Cada visita sigue un flujo guiado: ficha de la tarea con mapa, encuesta paso a paso, revisión con '
                'captura de GPS y foto como evidencia, y confirmación.',
            ),
            Text(
                'Every report carries its sync status, so the user always knows what has been sent and what is '
                'still pending.',
                'Cada informe lleva su estado de sincronización, de modo que el usuario siempre sabe qué está '
                'enviado y qué sigue pendiente.',
            ),
            Text(
                'Data access is isolated behind repository interfaces and a service layer. Switching from local '
                'storage to an API is a configuration change, not a rewrite of the screens.',
                'Separé el acceso a datos con interfaces de repositorio y una capa de servicios. Cambiar de '
                'almacenamiento local a API es un ajuste de configuración, no una reescritura de pantallas.',
            ),
            Text(
                'Three roles (village committee, partner officer, admin) and an interface in English and French.',
                'Tres roles (comité de aldea, oficial de socio, administrador) e interfaz en inglés y francés.',
            ),
        ),
        stack=(
            'React Native',
            'Expo',
            'TypeScript',
            'SQLite',
            'Zustand',
            'react-hook-form',
            'zod',
            'Mapbox',
            'i18next',
        ),
    ),
    Case(
        slug='e3-django-dynamic-forms',
        group=WORLD_BANK,
        layout=NORMAL,
        published=True,
        authorship=Text('Sole author · Open source', 'Autor único · Open source'),
        title=Text('e3-django-dynamic-forms'),
        proof_line=Text('pip install e3-django-dynamic-forms · MIT · 210 tests'),
        summary=Text(
            'A form engine for Django. The team designs forms in a visual builder, with no code changes or deploys, '
            'and responses are validated the same way on the web and through the API.',
            'Un motor de formularios para Django. El equipo diseña formularios en un constructor visual, sin tocar '
            'código ni desplegar, y las respuestas se validan igual en la web y en la API.',
        ),
        client=Text(
            'Built as part of the work for the World Bank Group',
            'Desarrollado en el marco del trabajo para el Grupo Banco Mundial',
        ),
        period=Text('2026'),
        role=Text(
            'Sole author. Design, implementation, tests and release',
            'Autor único. Diseño, implementación, tests y publicación',
        ),
        problem=Text(
            'In field programs, questionnaires change all the time. If every form change needs a developer, a '
            'migration and a deploy, the program team is blocked and the codebase fills up with near-identical '
            'forms.',
            'En programas de campo los cuestionarios cambian constantemente. Si cada cambio de formulario exige un '
            'desarrollador, una migración y un despliegue, el equipo de programa queda bloqueado y el código se '
            'llena de formularios casi iguales.',
        ),
        solution=(
            Text(
                'The form is data, not code: a JSON schema that staff edit in a visual builder.',
                'El formulario es un dato, no código: un esquema JSON que el personal edita en un constructor visual.',
            ),
            Text(
                'The server turns that schema into real Django forms, with multiple pages and fields that show or '
                'hide depending on earlier answers.',
                'El servidor convierte ese esquema en formularios de Django reales, con varias páginas y campos que '
                'aparecen o no según respuestas anteriores.',
            ),
            Text(
                'One validator for the schema and one for the responses, shared by the web interface and the REST '
                'API. There are no two paths with different rules.',
                'Un solo validador para el esquema y otro para las respuestas, compartidos por la interfaz web y la '
                'API REST. No hay dos caminos con reglas distintas.',
            ),
            Text(
                "The schema, response and attachment models can be swapped for the host project's own, using the "
                'same pattern Django uses for the user model.',
                'Los modelos de esquema, respuesta y adjunto se pueden sustituir por los del proyecto anfitrión, con '
                'el mismo patrón que usa Django para el modelo de usuario.',
            ),
            Text(
                'State between pages is kept in a pluggable backend.',
                'El estado entre páginas se guarda en un backend intercambiable.',
            ),
            Text(
                'Ships with file and geolocation fields, designed for field work.',
                'Incluye campos de archivo y de geolocalización, pensados para trabajo de campo.',
            ),
        ),
        stack=(
            'Python',
            'Django',
            'Django REST Framework',
            'pytest',
            Text('dependency-free JavaScript', 'JavaScript sin dependencias'),
        ),
        result=Text(
            'Published on PyPI under the MIT license, with eight releases and 210 automated tests. Supports Python '
            '3.10 to 3.13 and Django 4.1 to 5.1.',
            'Publicado en PyPI bajo licencia MIT, con ocho versiones y 210 tests automáticos. Compatible con Python '
            '3.10 a 3.13 y Django 4.1 a 5.1.',
        ),
        links=(
            Link('PyPI', E3_PYPI_URL),
            Link(GITHUB, 'https://github.com/e3tools/e3-django-dynamic-forms'),
        ),
    ),
    Case(
        slug='mid-term-rental-crm',
        group=OTHER,
        layout=WIDE,
        published=True,
        authorship=Text('Lead author', 'Autor principal'),
        card_meta=Text(
            'Vacation and mid-term rental management company · September to November 2026',
            'Gestora de alquiler vacacional y de media estancia · septiembre a noviembre de 2026',
        ),
        title=Text(
            'CRM for mid-term rentals, from spec to production',
            'CRM para alquiler de media estancia, de la especificación a producción',
        ),
        proof_line=Text(
            'Django · PostgreSQL · HTMX · WhatsApp · Idealista · 2,000+ tests',
            'Django · PostgreSQL · HTMX · WhatsApp · Idealista · +2.000 tests',
        ),
        summary=Text(
            "A CRM built into the company's property management system. Idealista inquiries arrive as leads on their "
            'own, agents work them on a board and talk to the customer over WhatsApp without leaving the platform. '
            'When a deal closes, the reservation is created automatically.',
            'Un CRM integrado en el sistema de gestión de la empresa. Las consultas de Idealista entran solas como '
            'leads, el agente las trabaja en un tablero y habla con el cliente por WhatsApp sin salir de la '
            'plataforma. Al cerrar, la reserva se crea sola.',
        ),
        client=Text(
            'Vacation and mid-term rental management company',
            'Gestora de alquiler vacacional y de media estancia',
        ),
        period=Text('September to November 2026', 'Septiembre a noviembre de 2026'),
        role=Text(
            'Lead author of the module. Product definition (PRD, architecture and stories), implementation and '
            'tests, using AI agent-driven development',
            'Autor principal del módulo. Definición del producto (PRD, arquitectura e historias), implementación y '
            'tests, con desarrollo dirigido por agentes de IA',
        ),
        problem=Text(
            'The company opened a mid-term rental line sourced through Idealista. An agent handling several '
            'inquiries had no shared view of what was open, what had been sent or what was waiting on a reply. '
            'Idealista listings and the properties in the management system were not connected, so suggesting a '
            'flat meant cross-checking both by hand.',
            'La empresa abrió una línea de alquiler de media estancia con captación por Idealista. Un agente con '
            'varias consultas abiertas no tenía una vista común de qué estaba pendiente, qué se había enviado ni qué '
            'esperaba respuesta. Los anuncios de Idealista y las propiedades del sistema de gestión no estaban '
            'conectados, así que sugerir un piso exigía cruzar los dos a mano.',
        ),
        solution=(
            Text(
                'A pipeline configurable per company, with personal and team boards, drag and drop, filters and KPIs.',
                'Un pipeline configurable por compañía, con tablero personal y de equipo, arrastrar y soltar, filtros '
                'y KPIs.',
            ),
            Text(
                'Inquiries that arrive by email from Idealista are read and turned into leads with no manual step.',
                'Las consultas que llegan por correo desde Idealista se leen y se convierten en leads sin '
                'intervención.',
            ),
            Text(
                'Idealista listings are synced and reconciled with the real inventory, with deduplication and manual '
                'review of doubtful matches. Flat suggestions come from that inventory.',
                'Los anuncios de Idealista se sincronizan y se concilian con el inventario real, con deduplicación y '
                'revisión manual de los casos dudosos. Las sugerencias de piso salen de ese inventario.',
            ),
            Text(
                "WhatsApp conversation from the lead's record: templates, sending, inbound replies and delivery "
                'status.',
                'Conversación por WhatsApp desde la ficha del lead: plantillas, envío, respuestas entrantes y estado '
                'de entrega.',
            ),
            Text(
                'When a mid-term lead is won, the reservation is created in the management system. No double entry.',
                'Al ganar un lead de media estancia, la reserva se crea en el sistema de gestión. No hay doble '
                'captura.',
            ),
            Text(
                'For sales management: team pipeline, reassignment, most requested properties and analysis of lost '
                'leads by category.',
                'Para la dirección comercial: pipeline del equipo, reasignación, propiedades más solicitadas y '
                'análisis de leads perdidos por categoría.',
            ),
            Text(
                'GDPR and marketing consent recorded on every lead, and no message goes out without it.',
                'Consentimiento RGPD y de marketing registrado en cada lead, y ningún mensaje sale sin él.',
            ),
            Text(
                'On the same platform, before the CRM, I built a financial analysis service using an LLM that '
                'generates insights on revenue, occupancy and channels in the dashboards, with response caching and '
                'graceful degradation when the model is unavailable.',
                'En la misma plataforma, antes del CRM, construí un servicio de análisis financiero con un LLM que '
                'genera insights sobre ingresos, ocupación y canales en los paneles, con caché de respuestas y '
                'degradación controlada si el modelo no está disponible.',
            ),
        ),
        how_built=Text(
            'The specification lives in the repository next to the code: PRD, architecture, epics and one spec per '
            'story, written with the BMAD method. Each story was implemented with coding agents from that spec and '
            'reviewed before merging. The first five epics, 19 stories, were implemented in two weeks.',
            'La especificación vive en el repositorio junto al código: PRD, arquitectura, épicas y una '
            'especificación por historia, escritas con el método BMAD. Cada historia se implementó con agentes de '
            'código a partir de esa especificación y pasó revisión antes de integrarse. Las cinco primeras épicas, '
            '19 historias, se implementaron en dos semanas.',
        ),
        stack=(
            'Python',
            'Django',
            'PostgreSQL',
            'Django REST Framework',
            'Jinja2',
            'HTMX',
            'WhatsApp Business API',
            'OpenAI API',
            'GitHub Actions',
            'AWS',
        ),
        result=Text(
            'In production and still evolving with the rest of the team. The module has more than 2,000 automated '
            'tests.',
            'En producción y en evolución por el resto del equipo. El módulo tiene más de 2.000 tests automáticos.',
        ),
    ),
    # Unpublished: its problem is still pending in docs/home-cases.md
    Case(
        slug='payments-and-b2b',
        group=OTHER,
        layout=NORMAL,
        published=False,
        card_meta=Text('Selia · 2022 to 2023', 'Selia · 2022 a 2023'),
        title=Text('Payment platform and B2B product', 'Plataforma de pagos y producto B2B'),
        proof_line=Text('Django · PostgreSQL · AWS · Stripe'),
        summary=Text(
            'Design, development and rollout of the payment platform and the B2B product, owning the backend '
            'architecture.',
            'Diseño, desarrollo e implantación de la plataforma de pagos y del producto B2B, con responsabilidad '
            'sobre la arquitectura backend.',
        ),
        client=Text('Selia'),
        period=Text('January 2022 to September 2023', 'Enero de 2022 a septiembre de 2023'),
        # A job title, the same in both languages, but prose everywhere else: written out so the tests can tell
        role=Text('Senior Full Stack Engineer', 'Senior Full Stack Engineer'),
        solution=(
            Text(
                'Designed and built the full payment platform, with Stripe integration.',
                'Diseñé y construí la plataforma de pagos completa, con integración de Stripe.',
            ),
            Text(
                'Designed and built the B2B platform, owning the backend architecture.',
                'Diseñé y construí la plataforma B2B, con responsabilidad sobre la arquitectura backend.',
            ),
            Text(
                'Optimized the infrastructure for scalability and reliability as the business grew.',
                'Optimicé la infraestructura para ganar escalabilidad y fiabilidad a medida que crecía el negocio.',
            ),
        ),
        stack=('Python', 'Django', 'Django REST Framework', 'PostgreSQL', 'AWS', 'Stripe'),
    ),
    # Unpublished: its proof line, problem, the rest of its solution and its result are still pending
    Case(
        slug='warehouse-management-system',
        group=OTHER,
        layout=NORMAL,
        published=False,
        authorship=Text('Sole author', 'Autor único'),
        card_meta=Text('Logistics company · 2026', 'Empresa de logística · 2026'),
        title=Text('Warehouse management system', 'Sistema de gestión de almacén'),
        summary=Text(
            'A warehouse management system for an operation that until then ran on paper. I was given the '
            'functional requirements and built everything else as the only person in technology, using AI '
            'agent-driven development.',
            'Un sistema de gestión de almacén para una operación que hasta entonces se llevaba en papel. Recibí los '
            'requisitos funcionales y levanté todo lo demás como único responsable de tecnología, con desarrollo '
            'dirigido por agentes de IA.',
        ),
        client=Text('Logistics company', 'Empresa de logística'),
        role=Text(
            'Sole technology owner: architecture, development, testing and deployment',
            'Único responsable de tecnología: arquitectura, desarrollo, pruebas y despliegue',
        ),
        solution=(
            Text(
                'Starting from the functional requirements, I designed the architecture from scratch and built the '
                'whole platform: goods receiving, per-client stock visibility, self-service delivery requests and '
                'monthly pre-settlement.',
                'A partir de los requisitos funcionales diseñé la arquitectura desde cero y construí la plataforma '
                'completa: recepción de mercancía, stock visible por cliente, solicitudes de entrega en autoservicio y '
                'preliquidación mensual.',
            ),
        ),
        stack=('Python', 'Django', 'HTMX', 'PostgreSQL', 'Celery', 'AWS', 'Terraform'),
    ),
    Case(
        slug='this-site',
        group=OTHER,
        layout=NORMAL,
        published=True,
        authorship=Text('Sole author · Open source', 'Autor único · Código abierto'),
        card_meta=Text('In production', 'En producción'),
        title=Text('This site', 'Este sitio'),
        proof_line=Text('Django · htmx · GitHub Actions · Cloudflare'),
        summary=Text(
            'Django with a REST API, tests and CI/CD, and a hardened self-hosted deployment that costs nothing to '
            'run. Every architecture decision is documented in the repository.',
            'Django con API REST, tests y CI/CD, y un despliegue propio endurecido que no cuesta nada operar. Cada '
            'decisión de arquitectura está documentada en el repositorio.',
        ),
        client=Text('Own project', 'Proyecto propio'),
        period=Text('In production', 'En producción'),
        role=Text('Sole author', 'Autor único'),
        problem=Text(
            'I wanted a site of my own that works as a sample of how I build and run web applications, and that '
            'costs nothing to keep running.',
            'Quería un sitio propio que sirviera de muestra de cómo construyo y opero aplicaciones web, y que no '
            'costara nada mantener en marcha.',
        ),
        solution=(
            Text(
                'A bilingual site with the language in the URL, so every page can be indexed and shared in its own '
                'language.',
                'Sitio bilingüe con el idioma en la URL, para que cada página se pueda indexar y compartir en su '
                'idioma.',
            ),
            Text(
                'Server-rendered content, with htmx only where it improves the experience. Everything works without '
                'JavaScript.',
                'Contenido renderizado en servidor, con htmx solo donde mejora la experiencia. Todo funciona sin '
                'JavaScript.',
            ),
            Text(
                "Secure by default: a content security policy that only lets the site's own scripts run, per-visitor "
                'rate limits and bot protection on forms.',
                'Seguridad por defecto: una política de seguridad de contenido que solo deja ejecutar los scripts '
                'del propio sitio, límites de peticiones por visitante y formularios con protección contra bots.',
            ),
            Text(
                'Fonts and icons served by the site itself, with no third-party requests.',
                'Fuentes e iconos servidos por el propio sitio, sin peticiones a terceros.',
            ),
            Text(
                'Deployed from CI to a single free-tier virtual machine behind Cloudflare, with nightly off-site '
                'backups.',
                'Despliegue desde CI en una única máquina virtual gratuita, detrás de Cloudflare, con copias de '
                'seguridad nocturnas fuera del servidor.',
            ),
            Text(
                'Every structural decision has its architecture decision record in the repository.',
                'Cada decisión estructural tiene su registro de decisión de arquitectura en el repositorio.',
            ),
        ),
        stack=(
            'Python',
            'Django',
            'Django REST Framework',
            'SQLite',
            'htmx',
            'nginx',
            'Gunicorn',
            'Cloudflare',
            'GitHub Actions',
        ),
        result=Text(
            'In production, with the code and the architecture decisions in the open.',
            'En producción, con el código y las decisiones de arquitectura abiertos.',
        ),
        links=(Link(GITHUB, SITE_REPO_URL),),
    ),
]
