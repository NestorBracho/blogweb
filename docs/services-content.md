# Contenido de las páginas de servicio y de "Cómo trabajo"

Estado: revisado por Nestor · 25 nov 2026
Fuente única del texto de las tres páginas de servicio y de la página "Cómo trabajo", en español e inglés.

## 0. Cómo usar este documento

- Solo contiene texto a publicar. Todo sale de `home-cases.md` y `cv-content.md`; no se añaden datos que no estén allí.
- Un campo marcado `[PENDIENTE]` no se publica. Son datos de negocio que solo Nestor puede dar (precios, disponibilidad, condiciones). Si se queda sin respuesta, la pregunta del FAQ se elimina.
- Las URL usan el slug en inglés en los dos idiomas, como los casos: `/es/services/django-backend/` y `/en/services/django-backend/`.
- No se nombran países en los trabajos del Grupo Banco Mundial. Los dos clientes anónimos se describen como en `home-cases.md`.
- En los textos no se usan rayas largas.
- `{{ owner.years }}` es el valor calculado de los años, como en el resto del sitio.
- Cada página termina con el bloque de contacto de la home ("¿Tienes un proyecto o una vacante? Hablemos.").

### Estructura de una página de servicio

| Campo | Uso |
|---|---|
| `slug` | URL, igual en los dos idiomas |
| Título SEO | `<title>`, hasta unos 60 caracteres |
| Descripción | meta description y Open Graph, hasta unos 155 caracteres |
| H1 | Titular visible |
| Respuesta corta | Primer párrafo, 2 o 3 frases: qué haces, para quién y una prueba con número |
| Qué hago | Lista de 4 a 6 puntos |
| Casos | Dos o tres casos publicados, enlazados con su tarjeta |
| Cómo trabajo | Una frase y el enlace a la página "Cómo trabajo" |
| Preguntas frecuentes | De 4 a 6, respondidas en 2 o 3 frases |

---

## Servicio 1 · Backend con Django y Django REST Framework

`slug`: `django-backend` · casos: `local-development-portal`, `mid-term-rental-crm`, `e3-django-dynamic-forms`

### ES

- Título SEO: Desarrollador Django freelance en Madrid · Nestor Bracho
- Descripción: Desarrollador Django y Django REST Framework freelance en Madrid. Más de {{ owner.years }} años diseñando APIs, modelos de datos y backends en producción.
- H1: Desarrollador Django freelance: APIs y backends que crecen sin reescribirse
- Respuesta corta: Diseño y construyo backends con Python, Django y Django REST Framework para productos que tienen que crecer sin rehacerse. Llevo más de {{ owner.years }} años con Django: tres de ellos como arquitecto y desarrollador para el Grupo Banco Mundial, y ahora como freelance desde Madrid, en remoto o en formato híbrido.
- Qué hago:
  1. Diseño de APIs REST con Django REST Framework, con contratos fijados en OpenAPI.
  2. Modelado de datos y optimización de consultas en PostgreSQL.
  3. Integraciones con terceros: pagos con Stripe, WhatsApp Business API, Idealista, SMS y email (Twilio, SendGrid, Mailchimp).
  4. Tareas en segundo plano con Celery y Redis.
  5. Infraestructura en AWS (EC2, RDS, S3, Elastic Beanstalk, Lambda) con Terraform y CI/CD en GitHub Actions.
  6. Trabajo sobre bases de código Django que ya existen: nuevas funcionalidades, mantenimiento y migraciones de versión.
- Casos, entradilla: Tres backends Django en producción.
- Cómo trabajo: Escribo la especificación, los agentes de IA implementan y yo reviso cada cambio antes de integrarlo. Ver cómo trabajo.
- Preguntas frecuentes:
  1. **¿Puedes trabajar sobre un proyecto Django que ya existe?** Sí. Buena parte de mi trabajo ha sido sobre código ajeno, como el CRM/ERP Zina de Nokia o el sistema de gestión en el que integré el CRM de media estancia. Empiezo leyendo el código y los tests, y propongo cambios por fases.
  2. **¿Trabajas solo con Django o también con el frontend?** El backend es mi especialidad, pero entrego también la interfaz cuando hace falta: HTMX en plantillas de Django, Angular, o React Native para móvil.
  3. **¿Trabajas en remoto?** Sí. Vivo en Madrid y trabajo en remoto o en formato híbrido, en español o en inglés.
  4. **¿Qué pasa con la calidad si usas agentes de IA?** Ningún cambio se integra sin que lo revise y sin que pase los tests y la integración continua. El módulo de CRM de media estancia, construido así, tiene más de 2.000 tests automáticos.
  5. **¿Cómo presupuestas un proyecto?** Por fases. La primera es la especificación, y cada fase se presupuesta con su alcance ya definido. Cuéntame el proyecto y te preparo una propuesta.

### EN

- SEO title: Freelance Django developer in Madrid · Nestor Bracho
- Description: Freelance Django and Django REST Framework developer in Madrid. More than {{ owner.years }} years designing APIs, data models and production backends.
- H1: Freelance Django developer: APIs and backends that grow without a rewrite
- Short answer: I design and build backends with Python, Django and Django REST Framework for products that need to grow without being rebuilt. I have more than {{ owner.years }} years with Django: three of them as an architect and developer for the World Bank Group, and now as a freelancer based in Madrid, working remotely or hybrid.
- What I do:
  1. REST API design with Django REST Framework, with contracts locked in OpenAPI.
  2. Data modeling and query optimization in PostgreSQL.
  3. Third-party integrations: Stripe payments, WhatsApp Business API, Idealista, SMS and email (Twilio, SendGrid, Mailchimp).
  4. Background jobs with Celery and Redis.
  5. AWS infrastructure (EC2, RDS, S3, Elastic Beanstalk, Lambda) with Terraform and CI/CD on GitHub Actions.
  6. Work on existing Django codebases: new features, maintenance and version upgrades.
- Cases, lead: Three Django backends in production.
- How I work: I write the specification, AI agents implement it and I review every change before it is merged. See how I work.
- FAQ:
  1. **Can you work on an existing Django project?** Yes. Much of my work has been on other people's code, such as Nokia's Zina CRM/ERP or the management system I built the mid-term rental CRM into. I start by reading the code and the tests, and propose changes in phases.
  2. **Do you only do Django, or the frontend too?** Backend is my specialty, but I also deliver the interface when needed: HTMX in Django templates, Angular, or React Native for mobile.
  3. **Do you work remotely?** Yes. I live in Madrid and work remotely or hybrid, in Spanish or English.
  4. **What about quality if you use AI agents?** No change is merged until I have reviewed it and it has passed the tests and continuous integration. The mid-term rental CRM module, built this way, has more than 2,000 automated tests.
  5. **How do you quote a project?** By phase. The first phase is the specification, and each phase is quoted once its scope is defined. Tell me about the project and I will prepare a proposal.

---

## Servicio 2 · IA en productos que ya existen

`slug`: `ai-integration` · casos: `mid-term-rental-crm`, `local-development-portal`

### ES

- Título SEO: Integración de IA y LLMs en productos Django · Nestor Bracho
- Descripción: Integro LLMs y modelos de Hugging Face en productos que ya están en producción, sin reescribirlos. Con caché, degradación controlada y tests.
- H1: IA en tu producto actual, sin reescribirlo
- Respuesta corta: Integro LLMs y modelos de Hugging Face en sistemas que ya están en producción, como una pieza más del backend y no como un proyecto aparte. Lo más reciente: un servicio de análisis financiero que explica en lenguaje claro los paneles de una plataforma de gestión de alquileres.
- Qué hago:
  1. Integración de LLMs vía API (OpenAI) con prompt engineering y tool calling.
  2. Modelos de Hugging Face en pipelines de procesamiento de contenido.
  3. Diseño del servicio para producción: contexto por cliente, caché de respuestas y degradación controlada cuando el modelo no está disponible.
  4. Análisis con LLM dentro de paneles existentes, como el de diagnóstico de un sistema de gestión de quejas.
  5. Integración en el backend Django que ya tienes, con sus permisos, sus datos y sus tests.
- Ejemplos:
  - Gestora de alquiler vacacional y de media estancia: servicio de análisis financiero con un LLM que genera insights sobre ingresos, ocupación y canales en los paneles. En producción.
  - Grupo Banco Mundial: capa de análisis con un LLM en el panel de diagnóstico de un sistema de gestión de quejas. En producción.
  - Ekwi-three: modelos de Hugging Face en el pipeline de una plataforma de gestión de contenidos que procesa y organiza grandes volúmenes de recursos.
- Cómo trabajo: La integración se especifica y se revisa como cualquier otra funcionalidad del backend. Ver cómo trabajo.
- Preguntas frecuentes:
  1. **¿Hace falta rehacer el producto para añadir IA?** No. La integración entra como un servicio más del backend que lee los datos que ya existen. En los dos casos en producción no se cambió la arquitectura del producto.
  2. **¿Qué pasa si el modelo falla o tarda?** El servicio guarda en caché las respuestas y, si el modelo no está disponible, el panel sigue funcionando sin el análisis. El usuario no ve un error.
  3. **¿Con qué modelos trabajas?** He integrado la API de OpenAI y modelos de Hugging Face. La elección depende del caso: coste, latencia y dónde pueden ir los datos.
  4. **¿Qué pasa con tus datos y los de tus clientes?** Son confidenciales. Si después uso el proyecto como referencia, lo hago anonimizado, como los clientes de los casos de este sitio.

### EN

- SEO title: AI and LLM integration for Django products · Nestor Bracho
- Description: I integrate LLMs and Hugging Face models into products already in production, without a rewrite. With caching, graceful degradation and tests.
- H1: AI in your current product, without a rewrite
- Short answer: I integrate LLMs and Hugging Face models into systems that are already in production, as one more part of the backend rather than a separate project. Most recently: a financial analysis service that explains the dashboards of a rental management platform in plain language.
- What I do:
  1. LLM integration through APIs (OpenAI) with prompt engineering and tool calling.
  2. Hugging Face models in content processing pipelines.
  3. Production-ready service design: per-client context, response caching and graceful degradation when the model is unavailable.
  4. LLM analysis inside existing dashboards, such as the diagnostics dashboard of a grievance redress system.
  5. Integration into your existing Django backend, with its permissions, its data and its tests.
- Examples:
  - Vacation and mid-term rental management company: a financial analysis service using an LLM that generates insights on revenue, occupancy and channels in the dashboards. In production.
  - World Bank Group: an LLM analysis layer in the diagnostics dashboard of a grievance redress system. In production.
  - Ekwi-three: Hugging Face models in the pipeline of a content management platform that processes and organizes large volumes of resources.
- How I work: The integration is specified and reviewed like any other backend feature. See how I work.
- FAQ:
  1. **Do I need to rebuild my product to add AI?** No. The integration goes in as one more backend service that reads the data you already have. In both production cases the product's architecture did not change.
  2. **What if the model fails or is slow?** The service caches responses and, if the model is unavailable, the dashboard keeps working without the analysis. Users don't see an error.
  3. **Which models do you work with?** I have integrated the OpenAI API and Hugging Face models. The choice depends on the case: cost, latency and where the data is allowed to go.
  4. **What about your data and your customers' data?** It stays confidential. If I later use the project as a reference, I do it anonymized, like the clients in this site's case studies.

---

## Servicio 3 · Producto de principio a fin

`slug`: `end-to-end-product` · casos: `mid-term-rental-crm`, `participatory-monitoring-app`, `this-site`

### ES

- Título SEO: Desarrollo de producto de principio a fin · Nestor Bracho
- Descripción: De la especificación al despliegue: backend, frontend, tests y puesta en producción, con una sola persona responsable y desarrollo con agentes de IA.
- H1: De la especificación a producción, con una sola persona responsable
- Respuesta corta: Llevo un producto desde la especificación hasta producción: backend, frontend, tests y despliegue. Trabajo con agentes de IA bajo especificación y revisión humana; así entregué las cinco primeras épicas de un CRM, 19 historias, en dos semanas.
- Qué hago:
  1. Especificación antes del código: PRD, arquitectura, épicas y una especificación por historia, con criterios de aceptación.
  2. Arquitectura del sistema y elección del stack según el problema, no al revés.
  3. Backend en Django, interfaz con HTMX o Angular, y apps móviles offline-first con React Native y Expo.
  4. Tests automáticos (pytest, Jest, Maestro) e integración continua en cada cambio.
  5. Despliegue en AWS o en infraestructura mínima detrás de Cloudflare, con copias de seguridad fuera del servidor.
  6. Traspaso al equipo: el código, la especificación y las decisiones de arquitectura quedan en el repositorio.
- Casos, entradilla: Tres productos construidos de principio a fin.
- Cómo trabajo: Este servicio es el método aplicado completo. Ver cómo trabajo.
- Preguntas frecuentes:
  1. **¿Qué necesitas para empezar?** El problema que quieres resolver y quién lo tiene. A partir de ahí escribo con tu equipo la especificación y la divido en fases que se pueden revisar y entregar por separado.
  2. **¿Qué recibo al final?** El producto en producción, el código con sus tests y la especificación en el mismo repositorio. Cualquier desarrollador, o cualquier agente, puede continuar desde ahí.
  3. **¿Haces también apps móviles?** Sí, con React Native y Expo. La app de monitoreo participativo funciona sin conexión y sincroniza cuando vuelve la red.
  4. **¿Cuánto tarda un producto?** Depende del alcance, por eso la primera entrega es la especificación por fases. Como referencia, las cinco primeras épicas del CRM de media estancia, 19 historias, se implementaron en dos semanas.

### EN

- SEO title: End-to-end product development · Nestor Bracho
- Description: From specification to deployment: backend, frontend, testing and release, with one person accountable and AI agent-driven development.
- H1: From specification to production, with one person accountable
- Short answer: I take a product from specification to production: backend, frontend, testing and deployment. I work with AI agents under specification and human review; that is how I delivered the first five epics of a CRM, 19 stories, in two weeks.
- What I do:
  1. Specification before code: PRD, architecture, epics and one spec per story, with acceptance criteria.
  2. System architecture and a stack chosen for the problem, not the other way round.
  3. Django backend, HTMX or Angular interfaces, and offline-first mobile apps with React Native and Expo.
  4. Automated tests (pytest, Jest, Maestro) and continuous integration on every change.
  5. Deployment on AWS or on minimal infrastructure behind Cloudflare, with off-site backups.
  6. Handover to the team: the code, the specification and the architecture decisions stay in the repository.
- Cases, lead: Three products built end to end.
- How I work: This service is the full method in practice. See how I work.
- FAQ:
  1. **What do you need to get started?** The problem you want to solve and who has it. From there I write the specification with your team and split it into phases that can be reviewed and delivered on their own.
  2. **What do I get at the end?** The product in production, the code with its tests and the specification in the same repository. Any developer, or any agent, can carry on from there.
  3. **Do you build mobile apps too?** Yes, with React Native and Expo. The participatory monitoring app works offline and syncs when the network comes back.
  4. **How long does a product take?** It depends on the scope, which is why the first deliverable is the phased specification. For reference, the first five epics of the mid-term rental CRM, 19 stories, were implemented in two weeks.

---

## Página · Cómo trabajo

`slug`: `how-i-work` · sustituye al ancla `/#how-i-work` como destino de los enlaces; el bloque de la home se queda y enlaza aquí.

### ES

- Título SEO: Cómo construyo software con agentes de IA · Nestor Bracho
- Descripción: Desarrollo dirigido por especificaciones con agentes de IA: especificación, agentes con roles, revisión humana y verificación. Con un caso real y sus números.
- H1: Los agentes escriben el código. La especificación y la revisión son mías.
- Respuesta corta: Construyo software con agentes de IA en cuatro pasos: escribo la especificación, agentes con roles distintos la implementan, yo reviso cada plan y cada cambio, y nada llega a producción sin pasar los tests y la integración continua. Con este método entregué las cinco primeras épicas de un CRM, 19 historias, en dos semanas, con más de 2.000 tests automáticos.
- 01 · Especificación: Antes de escribir código hay un brief, un alcance por fases y criterios de aceptación. En proyectos grandes eso es un PRD, una arquitectura, épicas y una especificación por historia. La especificación vive en el repositorio junto al código, así que cualquier persona o agente que llegue después sabe qué se decidió y por qué.
- 02 · Agentes con roles: Trabajo con Claude Code y el método BMAD. Un agente planifica, otro implementa y otro revisa, cada uno con sus instrucciones. Uso subagentes, comandos propios, archivos de instrucciones y servidores MCP para que cada agente tenga solo el contexto que necesita.
- 03 · Revisión humana: Apruebo cada plan antes de que se ejecute y leo cada cambio antes de integrarlo. Los agentes aceleran la escritura del código; las decisiones de producto y de arquitectura no se delegan.
- 04 · Verificación: Tests automáticos (pytest, Jest, Maestro), contratos de API fijados con OpenAPI e integración continua en cada cambio. Si algo no pasa, no se integra.
- Ejemplo real, titular: Un CRM en producción, de la especificación al despliegue
- Ejemplo real, texto: Para una gestora de alquiler vacacional y de media estancia construí un CRM dentro de su sistema de gestión: leads automáticos desde Idealista, conversación por WhatsApp y reservas que se crean solas al cerrar. Escribí el PRD, la arquitectura y las épicas con BMAD, y cada historia se implementó con agentes a partir de su especificación y pasó revisión antes de integrarse.
- Ejemplo real, datos clave:
  - 19 historias en las cinco primeras épicas
  - 2 semanas de implementación para esas épicas
  - Más de 2.000 tests automáticos en el módulo
  - CI sobre PostgreSQL en GitHub Actions en cada cambio
  - En producción y en evolución por el resto del equipo
- Ejemplo real, enlace: Ver el caso completo
- Otros proyectos con este método: la app móvil offline-first de monitoreo participativo para el Grupo Banco Mundial, un sistema de gestión de almacén para una empresa de logística y este sitio.
- Preguntas frecuentes:
  1. **¿Qué es el desarrollo dirigido por especificaciones?** Es escribir primero qué hay que construir y cómo se sabrá que está bien, y después implementarlo. Con agentes de IA es lo que convierte un generador de código en un equipo predecible: el agente trabaja contra la especificación y la revisión compara contra ella.
  2. **¿Qué es el método BMAD?** Un método de código abierto para desarrollo con agentes de IA que reparte el trabajo en roles (analista, producto, arquitectura, desarrollo, revisión) y produce documentos que se encadenan: brief, PRD, arquitectura, épicas e historias.
  3. **¿El código escrito por agentes es fiable?** Tanto como la revisión y los tests que lo acompañan. Por eso reviso cada cambio y nada se integra sin pasar los tests y la integración continua.
  4. **¿Puedo usar este método con mi equipo?** Sí. Ofrezco formación y acompañamiento para que tu equipo trabaje con agentes de IA bajo especificación y revisión, sobre vuestros propios proyectos.

### EN

- SEO title: How I build software with AI agents · Nestor Bracho
- Description: Spec-driven development with AI agents: specification, agents with roles, human review and verification. With a real case and its numbers.
- H1: Agents write the code. The specification and the review are mine.
- Short answer: I build software with AI agents in four steps: I write the specification, agents with different roles implement it, I review every plan and every change, and nothing reaches production without passing the tests and continuous integration. With this method I delivered the first five epics of a CRM, 19 stories, in two weeks, with more than 2,000 automated tests.
- 01 · Specification: Before any code is written there is a brief, a phased scope and acceptance criteria. On larger projects that means a PRD, an architecture, epics and one spec per story. The specification lives in the repository next to the code, so whoever comes later, person or agent, knows what was decided and why.
- 02 · Agents with roles: I work with Claude Code and the BMAD method. One agent plans, another implements and another reviews, each with its own instructions. I use subagents, custom commands, instruction files and MCP servers so each agent only has the context it needs.
- 03 · Human review: I approve every plan before it runs and read every change before it is merged. Agents speed up writing the code; product and architecture decisions are not delegated.
- 04 · Verification: Automated tests (pytest, Jest, Maestro), API contracts locked with OpenAPI and continuous integration on every change. If something fails, it is not merged.
- Real example, heading: A CRM in production, from spec to deployment
- Real example, text: For a vacation and mid-term rental management company I built a CRM inside their management system: leads created automatically from Idealista, WhatsApp conversations and reservations created on their own when a deal closes. I wrote the PRD, the architecture and the epics with BMAD, and each story was implemented with agents from its spec and reviewed before merging.
- Real example, key facts:
  - 19 stories in the first five epics
  - 2 weeks to implement those epics
  - More than 2,000 automated tests in the module
  - CI on PostgreSQL in GitHub Actions on every change
  - In production and still evolving with the rest of the team
- Real example, link: See the full case
- Other projects built this way: the offline-first participatory monitoring app for the World Bank Group, a warehouse management system for a logistics company and this site.
- FAQ:
  1. **What is spec-driven development?** Writing down first what has to be built and how you will know it is right, and then building it. With AI agents, it is what turns a code generator into a predictable team: the agent works against the specification and the review checks against it.
  2. **What is the BMAD method?** An open-source method for AI agent-driven development that splits the work into roles (analyst, product, architecture, development, review) and produces documents that build on each other: brief, PRD, architecture, epics and stories.
  3. **Is code written by agents reliable?** As reliable as the review and the tests around it. That is why I review every change and nothing is merged without passing the tests and continuous integration.
  4. **Can I use this method with my team?** Yes. I offer training and hands-on support so your team can work with AI agents under specification and review, on your own projects.
