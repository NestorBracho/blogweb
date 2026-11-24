# Contenido de los casos

Estado: revisado por Nestor · actualizado el 24 nov 2026
Fuente única del contenido de los casos. Sustituye a los documentos de caso anteriores, que no se guardan en este repositorio.

## 0. Cómo usar este documento

- Contiene solo el texto a publicar, en español e inglés. No se añaden datos que no estén aquí.
- Un campo marcado `[PENDIENTE]` no se carga y no se pinta. Un caso con el problema o la solución pendientes queda como borrador, visible solo en desarrollo.
- Dos clientes son anónimos. Su descripción es la que aparece aquí y no se cambia ni se completa.
- No se nombran países en ningún caso del Grupo Banco Mundial.
- En los textos no se usan rayas largas.

## 1. Campos de un caso

| Campo | Notas |
|---|---|
| `slug` | Uno por idioma si el sitio ya traduce slugs; si no, el de esta tabla |
| `grupo` | `banco-mundial` u `otros` |
| `orden` | Posición dentro del grupo |
| `formato` | `ancha` o `normal` |
| `autoria` | Etiqueta corta, opcional |
| `cliente_periodo` | Línea de metadato de la tarjeta, opcional |
| `titulo`, `linea_de_prueba`, `resumen` | Tarjeta |
| `cliente`, `periodo`, `rol` | Ficha de la página de detalle |
| `problema`, `solucion` (lista), `como_se_construyo` (opcional), `stack` (lista), `resultado` (opcional) | Página de detalle |
| `enlaces` (lista de texto y URL, opcional) | Tarjeta y página de detalle |
| `captura` (opcional) | Imagen para la tarjeta ancha y la página de detalle |
| `publicado` | Falso mientras falte problema o solución |

Rótulos de grupo:
- `banco-mundial`: "Grupo Banco Mundial · 2023 a 2026" / "World Bank Group · 2023 to 2026"
- `otros`: "Otros clientes y proyectos" / "Other clients and projects"

## 2. Estado de publicación

| Orden | Caso | Grupo | Formato | Listo para publicar |
|---|---|---|---|---|
| 1 | Portal de desarrollo local | banco-mundial | ancha | Sí |
| 2 | App móvil de monitoreo participativo | banco-mundial | normal | Sí, sin resultado |
| 3 | e3-django-dynamic-forms | banco-mundial | normal | Sí |
| 4 | CRM de media estancia | otros | ancha | Sí |
| 5 | Plataforma de pagos y producto B2B | otros | normal | No, falta el problema |
| 6 | Sistema de gestión de almacén | otros | normal | No, falta el contenido |
| 7 | Este sitio | otros | normal | Sí |

Con cinco casos listos se cumple el mínimo de tres para lanzar.

---

## Caso 1 · Portal de desarrollo local

`slug`: `portal-desarrollo-local` / `local-development-portal` · `grupo`: banco-mundial · `formato`: ancha
`captura`: [PENDIENTE: captura del portal con datos de demostración]

### ES

- Autoría: Equipo
- Título: Portal de desarrollo local para programas comunitarios
- Línea de prueba: `Django · PostgreSQL · CouchDB · 2 idiomas · 2023 a 2026`
- Resumen: Una plataforma donde las prioridades de inversión de cada aldea se vuelven visibles para quien puede financiarlas. El financiador filtra, selecciona subproyectos, los envía a revisión y sigue su estado.
- Cliente: Grupo Banco Mundial
- Periodo: 2023 a 2026
- Rol: Desarrollador fullstack en un equipo distribuido
- Problema: En los programas de desarrollo impulsado por la comunidad, cada aldea define sus prioridades de inversión. Esa información existía en el sistema de gestión interno, pero las organizaciones que financian no tenían dónde consultarla, elegir qué apoyar ni seguir qué pasó después.
- Solución:
  1. Definí el modelo de datos inicial del portal: niveles administrativos, proyectos, sectores, inversiones, paquetes y adjuntos.
  2. Construí el flujo principal del financiador: listado de inversiones con filtros dinámicos, carrito, envío del paquete y seguimiento.
  3. Construí la revisión por moderador, con aprobación o rechazo razonado, permisos por rol y notificaciones por correo en inglés y francés.
  4. Llevé el listado de inversiones a procesamiento en servidor cuando el volumen de datos lo exigió.
  5. Añadí la capa geográfica: mapas con Mapbox, mapa climático por nivel administrativo y sincronización de coordenadas.
  6. Trabajé sobre datos que llegan desde el sistema de gestión (CouchDB) hacia PostgreSQL mediante sincronizaciones.
  7. Para un sistema de gestión de quejas del mismo cliente, diseñé el módulo de notificaciones por SMS y email (Twilio, Africa's Talking, SendGrid y Mailchimp), que cambia de proveedor por configuración, y una capa de análisis con un LLM en su panel de diagnóstico. Ambos están en producción.
- Stack: Python, Django, Django REST Framework, PostgreSQL, CouchDB, Celery, Redis, HTMX, Mapbox, AWS S3
- Resultado: Un portal bilingüe que cubre el recorrido completo, desde la prioridad de una aldea hasta la inversión aprobada y en seguimiento.
- Enlaces: ninguno

### EN

- Authorship: Team
- Title: Local development portal for community-driven programs
- Proof line: `Django · PostgreSQL · CouchDB · 2 languages · 2023 to 2026`
- Summary: A platform that makes each village's investment priorities visible to the organizations that can fund them. Funders filter, select sub-projects, submit them for review and track their status.
- Client: World Bank Group
- Period: 2023 to 2026
- Role: Fullstack developer in a distributed team
- Problem: In community-driven development programs, each village defines its own investment priorities. That information lived in the internal management system, but funding organizations had nowhere to browse it, choose what to support, or follow what happened next.
- Solution:
  1. Defined the portal's initial data model: administrative levels, projects, sectors, investments, packages and attachments.
  2. Built the funder's main flow: investment list with dynamic filters, cart, package submission and tracking.
  3. Built the moderator review, with reasoned approval or rejection, role-based permissions and email notifications in English and French.
  4. Moved the investment list to server-side processing when data volume required it.
  5. Added the geographic layer: Mapbox maps, a climate map by administrative level and coordinate syncing.
  6. Worked on data that flows from the management system (CouchDB) into PostgreSQL through sync jobs.
  7. For a grievance redress system of the same client, designed the SMS and email notifications module (Twilio, Africa's Talking, SendGrid and Mailchimp), which switches provider through configuration, and an LLM analysis layer in its diagnostics dashboard. Both are running in production.
- Stack: Python, Django, Django REST Framework, PostgreSQL, CouchDB, Celery, Redis, HTMX, Mapbox, AWS S3
- Result: A bilingual portal covering the full path, from a village's priority to an approved, tracked investment.
- Links: none

---

## Caso 2 · App móvil de monitoreo participativo

`slug`: `app-monitoreo-participativo` / `participatory-monitoring-app` · `grupo`: banco-mundial · `formato`: normal

### ES

- Autoría: Autor principal
- Título: App móvil offline-first para monitoreo participativo
- Línea de prueba: `React Native · Expo · SQLite · GPS + foto · EN/FR`
- Resumen: Los comités de aldea verifican sobre el terreno el estado de las obras de su comunidad. La app funciona sin conexión: cada visita se guarda en el teléfono con sus respuestas, coordenadas y foto.
- Cliente: Grupo Banco Mundial
- Periodo: 2026
- Rol: Diseño de la arquitectura y desarrollo de la app, prácticamente en solitario, con desarrollo asistido por agentes de IA
- Problema: Quien mejor sabe si una obra funciona es la comunidad que la usa. Pero esas comunidades suelen estar donde la cobertura falla, así que una app que dependa de la red no sirve para recoger esa información.
- Solución:
  1. Los datos viven primero en el dispositivo. La app usa SQLite local con migraciones que se aplican solas al arrancar.
  2. Cada visita sigue un flujo guiado: ficha de la tarea con mapa, encuesta paso a paso, revisión con captura de GPS y foto como evidencia, y confirmación.
  3. Cada informe lleva su estado de sincronización, de modo que el usuario siempre sabe qué está enviado y qué sigue pendiente.
  4. Separé el acceso a datos con interfaces de repositorio y una capa de servicios. Cambiar de almacenamiento local a API es un ajuste de configuración, no una reescritura de pantallas.
  5. Tres roles (comité de aldea, oficial de socio, administrador) e interfaz en inglés y francés.
- Stack: React Native, Expo, TypeScript, SQLite, Zustand, react-hook-form, zod, Mapbox, i18next
- Resultado: [PENDIENTE]
- Enlaces: ninguno

### EN

- Authorship: Lead author
- Title: Offline-first mobile app for participatory monitoring
- Proof line: `React Native · Expo · SQLite · GPS + photo · EN/FR`
- Summary: Village committees check the state of their community's infrastructure on site. The app works without a connection: every visit is stored on the phone with its answers, coordinates and photo.
- Client: World Bank Group
- Period: 2026
- Role: Architecture design and development of the app, almost entirely solo, using AI agent-assisted development
- Problem: Nobody knows whether a piece of infrastructure works better than the community that uses it. But those communities are often where coverage fails, so an app that depends on the network cannot collect that information.
- Solution:
  1. Data lives on the device first. The app uses local SQLite with migrations that apply themselves on startup.
  2. Every visit follows a guided flow: task sheet with a map, step-by-step survey, review with GPS capture and a photo as evidence, and confirmation.
  3. Every report carries its sync status, so the user always knows what has been sent and what is still pending.
  4. Data access is isolated behind repository interfaces and a service layer. Switching from local storage to an API is a configuration change, not a rewrite of the screens.
  5. Three roles (village committee, partner officer, admin) and an interface in English and French.
- Stack: React Native, Expo, TypeScript, SQLite, Zustand, react-hook-form, zod, Mapbox, i18next
- Result: [PENDING]
- Links: none

---

## Caso 3 · e3-django-dynamic-forms

`slug`: `e3-django-dynamic-forms` (igual en los dos idiomas) · `grupo`: banco-mundial · `formato`: normal

### ES

- Autoría: Autor único · Open source
- Título: e3-django-dynamic-forms
- Línea de prueba: `pip install e3-django-dynamic-forms · MIT · 210 tests`
- Resumen: Un motor de formularios para Django. El equipo diseña formularios en un constructor visual, sin tocar código ni desplegar, y las respuestas se validan igual en la web y en la API.
- Cliente: Desarrollado en el marco del trabajo para el Grupo Banco Mundial
- Periodo: 2026
- Rol: Autor único. Diseño, implementación, tests y publicación
- Problema: En programas de campo los cuestionarios cambian constantemente. Si cada cambio de formulario exige un desarrollador, una migración y un despliegue, el equipo de programa queda bloqueado y el código se llena de formularios casi iguales.
- Solución:
  1. El formulario es un dato, no código: un esquema JSON que el personal edita en un constructor visual.
  2. El servidor convierte ese esquema en formularios de Django reales, con varias páginas y campos que aparecen o no según respuestas anteriores.
  3. Un solo validador para el esquema y otro para las respuestas, compartidos por la interfaz web y la API REST. No hay dos caminos con reglas distintas.
  4. Los modelos de esquema, respuesta y adjunto se pueden sustituir por los del proyecto anfitrión, con el mismo patrón que usa Django para el modelo de usuario.
  5. El estado entre páginas se guarda en un backend intercambiable.
  6. Incluye campos de archivo y de geolocalización, pensados para trabajo de campo.
- Stack: Python, Django, Django REST Framework, pytest, JavaScript sin dependencias
- Resultado: Publicado en PyPI bajo licencia MIT, con ocho versiones y 210 tests automáticos. Compatible con Python 3.10 a 3.13 y Django 4.1 a 5.1.
- Enlaces:
  - PyPI: https://pypi.org/project/e3-django-dynamic-forms/
  - GitHub: https://github.com/e3tools/e3-django-dynamic-forms

### EN

- Authorship: Sole author · Open source
- Title: e3-django-dynamic-forms
- Proof line: `pip install e3-django-dynamic-forms · MIT · 210 tests`
- Summary: A form engine for Django. The team designs forms in a visual builder, with no code changes or deploys, and responses are validated the same way on the web and through the API.
- Client: Built as part of the work for the World Bank Group
- Period: 2026
- Role: Sole author. Design, implementation, tests and release
- Problem: In field programs, questionnaires change all the time. If every form change needs a developer, a migration and a deploy, the program team is blocked and the codebase fills up with near-identical forms.
- Solution:
  1. The form is data, not code: a JSON schema that staff edit in a visual builder.
  2. The server turns that schema into real Django forms, with multiple pages and fields that show or hide depending on earlier answers.
  3. One validator for the schema and one for the responses, shared by the web interface and the REST API. There are no two paths with different rules.
  4. The schema, response and attachment models can be swapped for the host project's own, using the same pattern Django uses for the user model.
  5. State between pages is kept in a pluggable backend.
  6. Ships with file and geolocation fields, designed for field work.
- Stack: Python, Django, Django REST Framework, pytest, dependency-free JavaScript
- Result: Published on PyPI under the MIT license, with eight releases and 210 automated tests. Supports Python 3.10 to 3.13 and Django 4.1 to 5.1.
- Links:
  - PyPI: https://pypi.org/project/e3-django-dynamic-forms/
  - GitHub: https://github.com/e3tools/e3-django-dynamic-forms

---

## Caso 4 · CRM de media estancia

`slug`: `crm-media-estancia` / `mid-term-rental-crm` · `grupo`: otros · `formato`: ancha
`captura`: [PENDIENTE: captura del tablero con datos de demostración]
El bloque "Cómo trabajo" de la home enlaza a la página de detalle de este caso.

### ES

- Autoría: Autor principal
- Cliente y periodo (tarjeta): Gestora de alquiler vacacional y de media estancia · septiembre a noviembre de 2026
- Título: CRM para alquiler de media estancia, de la especificación a producción
- Línea de prueba: `Django · PostgreSQL · HTMX · WhatsApp · Idealista · +2.000 tests`
- Resumen: Un CRM integrado en el sistema de gestión de la empresa. Las consultas de Idealista entran solas como leads, el agente las trabaja en un tablero y habla con el cliente por WhatsApp sin salir de la plataforma. Al cerrar, la reserva se crea sola.
- Cliente: Gestora de alquiler vacacional y de media estancia
- Periodo: Septiembre a noviembre de 2026
- Rol: Autor principal del módulo. Definición del producto (PRD, arquitectura e historias), implementación y tests, con desarrollo dirigido por agentes de IA
- Problema: La empresa abrió una línea de alquiler de media estancia con captación por Idealista. Un agente con varias consultas abiertas no tenía una vista común de qué estaba pendiente, qué se había enviado ni qué esperaba respuesta. Los anuncios de Idealista y las propiedades del sistema de gestión no estaban conectados, así que sugerir un piso exigía cruzar los dos a mano.
- Solución:
  1. Un pipeline configurable por compañía, con tablero personal y de equipo, arrastrar y soltar, filtros y KPIs.
  2. Las consultas que llegan por correo desde Idealista se leen y se convierten en leads sin intervención.
  3. Los anuncios de Idealista se sincronizan y se concilian con el inventario real, con deduplicación y revisión manual de los casos dudosos. Las sugerencias de piso salen de ese inventario.
  4. Conversación por WhatsApp desde la ficha del lead: plantillas, envío, respuestas entrantes y estado de entrega.
  5. Al ganar un lead de media estancia, la reserva se crea en el sistema de gestión. No hay doble captura.
  6. Para la dirección comercial: pipeline del equipo, reasignación, propiedades más solicitadas y análisis de leads perdidos por categoría.
  7. Consentimiento RGPD y de marketing registrado en cada lead, y ningún mensaje sale sin él.
  8. En la misma plataforma, antes del CRM, construí un servicio de análisis financiero con un LLM que genera insights sobre ingresos, ocupación y canales en los paneles, con caché de respuestas y degradación controlada si el modelo no está disponible.
- Cómo se construyó: La especificación vive en el repositorio junto al código: PRD, arquitectura, épicas y una especificación por historia, escritas con el método BMAD. Cada historia se implementó con agentes de código a partir de esa especificación y pasó revisión antes de integrarse. Las cinco primeras épicas, 19 historias, se implementaron en dos semanas.
- Stack: Python, Django, PostgreSQL, Django REST Framework, Jinja2, HTMX, WhatsApp Business API, OpenAI API, GitHub Actions, AWS
- Resultado: En producción y en evolución por el resto del equipo. El módulo tiene más de 2.000 tests automáticos.
- Enlaces: ninguno

### EN

- Authorship: Lead author
- Client and period (card): Vacation and mid-term rental management company · September to November 2026
- Title: CRM for mid-term rentals, from spec to production
- Proof line: `Django · PostgreSQL · HTMX · WhatsApp · Idealista · 2,000+ tests`
- Summary: A CRM built into the company's property management system. Idealista inquiries arrive as leads on their own, agents work them on a board and talk to the customer over WhatsApp without leaving the platform. When a deal closes, the reservation is created automatically.
- Client: Vacation and mid-term rental management company
- Period: September to November 2026
- Role: Lead author of the module. Product definition (PRD, architecture and stories), implementation and tests, using AI agent-driven development
- Problem: The company opened a mid-term rental line sourced through Idealista. An agent handling several inquiries had no shared view of what was open, what had been sent or what was waiting on a reply. Idealista listings and the properties in the management system were not connected, so suggesting a flat meant cross-checking both by hand.
- Solution:
  1. A pipeline configurable per company, with personal and team boards, drag and drop, filters and KPIs.
  2. Inquiries that arrive by email from Idealista are read and turned into leads with no manual step.
  3. Idealista listings are synced and reconciled with the real inventory, with deduplication and manual review of doubtful matches. Flat suggestions come from that inventory.
  4. WhatsApp conversation from the lead's record: templates, sending, inbound replies and delivery status.
  5. When a mid-term lead is won, the reservation is created in the management system. No double entry.
  6. For sales management: team pipeline, reassignment, most requested properties and analysis of lost leads by category.
  7. GDPR and marketing consent recorded on every lead, and no message goes out without it.
  8. On the same platform, before the CRM, I built a financial analysis service using an LLM that generates insights on revenue, occupancy and channels in the dashboards, with response caching and graceful degradation when the model is unavailable.
- How it was built: The specification lives in the repository next to the code: PRD, architecture, epics and one spec per story, written with the BMAD method. Each story was implemented with coding agents from that spec and reviewed before merging. The first five epics, 19 stories, were implemented in two weeks.
- Stack: Python, Django, PostgreSQL, Django REST Framework, Jinja2, HTMX, WhatsApp Business API, OpenAI API, GitHub Actions, AWS
- Result: In production and still evolving with the rest of the team. The module has more than 2,000 automated tests.
- Links: none

---

## Caso 5 · Plataforma de pagos y producto B2B

`slug`: `pagos-y-b2b` / `payments-and-b2b` · `grupo`: otros · `formato`: normal · `publicado`: no

### ES

- Cliente y periodo (tarjeta): Selia · 2022 a 2023
- Título: Plataforma de pagos y producto B2B
- Línea de prueba: `Django · PostgreSQL · AWS · Stripe`
- Resumen: Diseño, desarrollo e implantación de la plataforma de pagos y del producto B2B, con responsabilidad sobre la arquitectura backend.
- Cliente: Selia
- Periodo: Enero de 2022 a septiembre de 2023
- Rol: Senior Full Stack Engineer
- Problema: [PENDIENTE]
- Solución:
  1. Diseñé y construí la plataforma de pagos completa, con integración de Stripe.
  2. Diseñé y construí la plataforma B2B, con responsabilidad sobre la arquitectura backend.
  3. Optimicé la infraestructura para ganar escalabilidad y fiabilidad a medida que crecía el negocio.
- Stack: Python, Django, Django REST Framework, PostgreSQL, AWS, Stripe
- Resultado: [PENDIENTE]
- Enlaces: ninguno

### EN

- Client and period (card): Selia · 2022 to 2023
- Title: Payment platform and B2B product
- Proof line: `Django · PostgreSQL · AWS · Stripe`
- Summary: Design, development and rollout of the payment platform and the B2B product, owning the backend architecture.
- Client: Selia
- Period: January 2022 to September 2023
- Role: Senior Full Stack Engineer
- Problem: [PENDING]
- Solution:
  1. Designed and built the full payment platform, with Stripe integration.
  2. Designed and built the B2B platform, owning the backend architecture.
  3. Optimized the infrastructure for scalability and reliability as the business grew.
- Stack: Python, Django, Django REST Framework, PostgreSQL, AWS, Stripe
- Result: [PENDING]
- Links: none

---

## Caso 6 · Sistema de gestión de almacén

`slug`: `sistema-gestion-almacen` / `warehouse-management-system` · `grupo`: otros · `formato`: normal · `publicado`: no

### ES

- Autoría: Autor único
- Cliente y periodo (tarjeta): Empresa de logística · 2026
- Título: Sistema de gestión de almacén
- Línea de prueba: [PENDIENTE]
- Resumen: Un sistema de gestión de almacén para una operación que hasta entonces se llevaba en papel. Recibí los requisitos funcionales y levanté todo lo demás como único responsable de tecnología, con desarrollo dirigido por agentes de IA.
- Cliente: Empresa de logística
- Rol: Único responsable de tecnología: arquitectura, desarrollo, pruebas y despliegue
- Problema: [PENDIENTE]
- Solución:
  1. A partir de los requisitos funcionales diseñé la arquitectura desde cero y construí la plataforma completa: recepción de mercancía, stock visible por cliente, solicitudes de entrega en autoservicio y preliquidación mensual.
  2. [PENDIENTE: resto de la solución]
- Stack: Python, Django, HTMX, PostgreSQL, Celery, AWS, Terraform
- Resultado: [PENDIENTE]

### EN

- Authorship: Sole author
- Client and period (card): Logistics company · 2026
- Title: Warehouse management system
- Proof line: [PENDING]
- Summary: A warehouse management system for an operation that until then ran on paper. I was given the functional requirements and built everything else as the only person in technology, using AI agent-driven development.
- Client: Logistics company
- Role: Sole technology owner: architecture, development, testing and deployment
- Problem: [PENDING]
- Solution:
  1. Starting from the functional requirements, I designed the architecture from scratch and built the whole platform: goods receiving, per-client stock visibility, self-service delivery requests and monthly pre-settlement.
  2. [PENDING: rest of the solution]
- Stack: Python, Django, HTMX, PostgreSQL, Celery, AWS, Terraform
- Result: [PENDING]

---

## Caso 7 · Este sitio

`slug`: `este-sitio` / `this-site` · `grupo`: otros · `formato`: normal

Antes de publicar, comprueba cada punto de la solución contra el propio repositorio (`README.md` y `docs/adr/`) y corrige lo que haya cambiado.

### ES

- Autoría: Autor único · Código abierto
- Cliente y periodo (tarjeta): En producción
- Título: Este sitio
- Línea de prueba: `Django · htmx · GitHub Actions · Cloudflare`
- Resumen: Django con API REST, tests y CI/CD, y un despliegue propio endurecido que no cuesta nada operar. Cada decisión de arquitectura está documentada en el repositorio.
- Cliente: Proyecto propio
- Periodo: En producción
- Rol: Autor único
- Problema: Quería un sitio propio que sirviera de muestra de cómo construyo y opero aplicaciones web, y que no costara nada mantener en marcha.
- Solución:
  1. Sitio bilingüe con el idioma en la URL, para que cada página se pueda indexar y compartir en su idioma.
  2. Contenido renderizado en servidor, con htmx solo donde mejora la experiencia. Todo funciona sin JavaScript.
  3. Seguridad por defecto: una política de seguridad de contenido que solo deja ejecutar los scripts del propio sitio, límites de peticiones por visitante y formularios con protección contra bots.
  4. Fuentes e iconos servidos por el propio sitio, sin peticiones a terceros.
  5. Despliegue desde CI en una única máquina virtual gratuita, detrás de Cloudflare, con copias de seguridad nocturnas fuera del servidor.
  6. Cada decisión estructural tiene su registro de decisión de arquitectura en el repositorio.
- Stack: Python, Django, Django REST Framework, SQLite, htmx, nginx, Gunicorn, Cloudflare, GitHub Actions
- Resultado: En producción, con el código y las decisiones de arquitectura abiertos.
- Enlaces:
  - GitHub: https://github.com/NestorBracho/blogweb

### EN

- Authorship: Sole author · Open source
- Client and period (card): In production
- Title: This site
- Proof line: `Django · htmx · GitHub Actions · Cloudflare`
- Summary: Django with a REST API, tests and CI/CD, and a hardened self-hosted deployment that costs nothing to run. Every architecture decision is documented in the repository.
- Client: Own project
- Period: In production
- Role: Sole author
- Problem: I wanted a site of my own that works as a sample of how I build and run web applications, and that costs nothing to keep running.
- Solution:
  1. A bilingual site with the language in the URL, so every page can be indexed and shared in its own language.
  2. Server-rendered content, with htmx only where it improves the experience. Everything works without JavaScript.
  3. Secure by default: a content security policy that only lets the site's own scripts run, per-visitor rate limits and bot protection on forms.
  4. Fonts and icons served by the site itself, with no third-party requests.
  5. Deployed from CI to a single free-tier virtual machine behind Cloudflare, with nightly off-site backups.
  6. Every structural decision has its architecture decision record in the repository.
- Stack: Python, Django, Django REST Framework, SQLite, htmx, nginx, Gunicorn, Cloudflare, GitHub Actions
- Result: In production, with the code and the architecture decisions in the open.
- Links:
  - GitHub: https://github.com/NestorBracho/blogweb

---

## Textos de la home que no son de casos

Actualizados el 24 nov 2026: Nestor terminó su contrato con el Grupo Banco Mundial en junio de 2026 y trabaja como freelance. Estos textos mandan sobre los de `design/home.html`, que conserva los anteriores.

### ES

- Hero, línea superior: Nestor Bracho · Senior Software Engineer
- Hero, titular: Diseño y construyo plataformas web y sus backends, de la arquitectura al despliegue.
- Hero, entradilla: Más de {{ owner.years }} años con Python y Django, tres de ellos como arquitecto y desarrollador para el Grupo Banco Mundial. Hoy trabajo como freelance y construyo sistemas completos con agentes de IA, bajo especificación y revisión humana.
- Descripción de la página (meta y Open Graph): Senior Software Engineer con más de {{ owner.years }} años construyendo plataformas web con Python y Django. Tres años para el Grupo Banco Mundial; hoy, freelance con desarrollo dirigido por agentes de IA.
- Ficha, fila idiomas: Español nativo · Inglés B2
- Ficha, fila ubicación: Madrid, España (hoy muestra "Madrid, Spain" en la versión en español)
- Franja de clientes: Grupo Banco Mundial · Nokia · Selia · Ekwi-three · UICN
- Qué ofrezco, IA en productos existentes: Integración de LLMs y modelos de Hugging Face en sistemas que ya están en producción. Lo más reciente: un servicio de análisis financiero que explica los paneles de una plataforma de gestión de alquileres en lenguaje claro.
- El resto de textos en español no cambia.

### EN

- Hero, línea superior: Nestor Bracho · Senior Software Engineer
- Hero, titular: I design and build web platforms and their backends, from architecture to deployment.
- Hero, entradilla: More than {{ owner.years }} years with Python and Django, three of them as an architect and developer for the World Bank Group. I now work as a freelancer and build complete systems with AI agents, under specification and human review.
- Page description (meta and Open Graph): Senior Software Engineer with more than {{ owner.years }} years building web platforms with Python and Django. Three years for the World Bank Group; now freelance, with AI agent-driven development.
- Botones: Let's work together · View CV · Write to me
- Ficha: role, stack, ai, experience, location, mode, languages. Valores: Senior Software Engineer · Python · Django · DRF · PostgreSQL · AWS · Claude Code · BMAD · LLM APIs · Hugging Face · More than {{ owner.years }} years · Madrid, Spain · Remote or hybrid · Native Spanish · English B2
- Franja de clientes: I have worked for · World Bank Group · Nokia · Selia · Ekwi-three · IUCN
- Casos, titular: What I have built
- Cómo trabajo, titular: Agents write the code. The specification and the review are mine.
  1. Specification: Brief, phased scope and acceptance criteria before any code is written.
  2. Agents with roles: Claude Code and the BMAD method: one agent plans, another implements and another reviews.
  3. Human review: I approve every plan before it runs and read every change before it is merged.
  4. Verification: Tests, locked API contracts and continuous integration. Nothing reaches production without going through them.
  - Enlace: See a real example: the mid-term rental CRM
- Qué ofrezco, titular: How I can help
  - Backend architecture: API design, data modeling and AWS infrastructure for products that need to grow without being rebuilt.
  - End-to-end product: From specification to deployment: backend, frontend, testing and release, with one person accountable.
  - AI in existing products: Integration of LLMs and Hugging Face models into systems that are already in production. Most recently: a financial analysis service that explains the dashboards of a rental management platform in plain language.
- Contacto, titular: Have a project or an open role? Let's talk.
- Contacto, línea: I reply in Spanish or English.
- Blog: From the blog · View all
- Detalle de caso: The problem · What I built · How it was built · Stack · Result · Next case · Have a similar problem? Let's talk.
