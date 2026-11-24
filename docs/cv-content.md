# Contenido del CV del sitio

Estado: preparado para revisión de Nestor · 24 nov 2026
Fuente única del contenido de `/es/cv/` y `/en/cv/` (`main/templates/main/_lib/_cv_es.html` y `_cv_en.html`).

## 0. Cómo usar este documento

- Sustituye por completo el contenido actual de las dos plantillas del CV. No se añade nada que no esté aquí.
- La cabecera de la página (nombre, titular, contacto, botón de PDF) sigue saliendo de `owner.*`. El titular pasa a ser `{{ owner.role }} · Python/Django · Desarrollo con agentes de IA` en español y `{{ owner.role }} · Python/Django · AI agent-driven development` en inglés.
- El nombre se escribe "Nestor Bracho", sin acento, en los dos idiomas.
- Donde aparece `{{ owner.years }}` se usa el valor calculado, como hoy.
- Dos clientes son anónimos y así aparecen. No se nombran países del trabajo para el Grupo Banco Mundial.
- En los textos no se usan rayas largas. En los rangos de fechas se usa la raya corta que ya usa la plantilla.
- Los PDF enlazados desde `OWNER_CV_PDF_URLS` quedan desactualizados con este cambio. Los regenera Nestor; no los toques.

---

## ES

### Perfil

Ingeniero de software senior con más de {{ owner.years }} años construyendo plataformas web con Python y Django, enfocado en el diseño de backend, la arquitectura de sistemas y en llevar la IA a productos reales. Durante tres años fui arquitecto y desarrollador para el Grupo Banco Mundial, en plataformas de desarrollo comunitario y de clima utilizadas en varios países de África. Actualmente trabajo como freelance y he entregado un CRM y un sistema de gestión de almacén construidos con agentes de principio a fin.

He integrado IA generativa en productos reales (LLMs vía API, modelos de Hugging Face en pipelines de procesamiento) y el desarrollo con agentes es el centro de mi forma de trabajar: Claude Code, agentes con roles definidos y especificaciones por fases que reviso y valido antes de integrar.

### IA generativa y agentes

- **LLMs en producción:** integración de modelos vía API (OpenAI) con prompt engineering y tool calling; modelos de Hugging Face en pipelines de procesamiento de contenido.
- **Agentes y flujos multiagente:** trabajo diario con Claude Code, agentes con roles definidos (BMAD Method), subagents, custom commands, instruction files y servidores MCP.
- **Desarrollo guiado por especificaciones:** PRD, arquitectura, épicas y specs por historia que los agentes implementan y que reviso antes de integrar.
- **Validación de código generado por agentes:** contratos de API fijados con OpenAPI, tests automatizados (pytest, Jest, Maestro) y CI en cada cambio.

### Experiencia profesional

**Senior Software Engineer, desarrollo con IA**
Freelance · Madrid · jun 2026 – actualidad
Sistemas completos construidos con agentes de IA para clientes propios.

*Plataforma de gestión y CRM para una gestora de alquiler vacacional y de media estancia* (Django multiempresa, PostgreSQL, HTMX, AWS Elastic Beanstalk)

- **IA generativa en producción:** servicio de análisis financiero con un LLM (API de OpenAI) que genera insights y recomendaciones sobre ingresos, ocupación y canales en los paneles, con contexto por empresa, caché de respuestas y degradación controlada si el modelo no está disponible.
- **CRM de principio a fin con agentes:** escribí el PRD, la arquitectura y las épicas con BMAD e implementé el módulo con Claude Code: pipeline por etapas con tableros de arrastrar y soltar, reasignación, KPIs y análisis de leads cerrados. Las cinco primeras épicas, 19 historias, se implementaron en dos semanas.
- **Integración con Idealista:** sincronización de anuncios con deduplicación y conciliación de propiedades, y conversión automática en leads de las consultas recibidas por correo.
- **Integración con WhatsApp:** plantillas configurables, envío desde la ficha del lead, respuestas entrantes por webhook y estado de entrega.
- **Calidad del código generado por agentes:** más de 2.000 tests automáticos en el módulo, CI sobre PostgreSQL en GitHub Actions, una spec por historia y revisión antes de cada integración.

*Sistema de gestión de almacén para una empresa de logística* (Django, HTMX, PostgreSQL, Celery, AWS, Terraform)

- Único responsable técnico del cliente. A partir de los requisitos funcionales diseñé la arquitectura desde cero y construí la plataforma completa con agentes de IA: recepción de mercancía, stock visible por cliente, solicitudes de entrega en autoservicio y preliquidación mensual.
- Sustituyó una operativa diaria que se llevaba en papel.

**Senior Full Stack Engineer & System Architect**
Grupo Banco Mundial · Contrato · Madrid, remoto · jun 2023 – jun 2026
En paralelo con mi puesto en Selia hasta sep 2023 y con Ekwi-three en 2024.

- Portal de desarrollo local para programas de desarrollo impulsado por la comunidad: modelo de datos inicial, flujo del financiador (listado con filtros, selección y envío de paquetes de inversión), revisión por moderador con permisos por rol y capa geográfica con Mapbox. Lideré la fase de 2024, centrada en escalabilidad, nuevas herramientas de analítica de datos y usabilidad.
- Climate Vulnerability Portal, plataforma que monitoriza el impacto del cambio climático en la actividad sociopolítica de países africanos.
- App móvil offline-first de monitoreo participativo (React Native/Expo, SQLite): visitas de campo guiadas con encuesta, GPS y foto, almacenamiento local con estado de sincronización y acceso a datos aislado tras una capa de repositorios. Desarrollada con agentes de IA.
- `e3-django-dynamic-forms`: motor de formularios dinámicos para Django, de autoría única, publicado en PyPI bajo licencia MIT con 210 tests automáticos.
- Módulo de notificaciones por SMS y email para un sistema de gestión de quejas (Twilio, Africa's Talking, SendGrid, Mailchimp), que cambia de proveedor por configuración, y una capa de análisis con un LLM en su panel de diagnóstico.

Stack: Python, Django, Django REST Framework, PostgreSQL, CouchDB, Celery, HTMX, React Native, AWS

**Full Stack Developer & System Architect**
Ekwi-three GmbH · Freelance · Remoto · may 2024 – dic 2024
En paralelo con mi contrato en el Grupo Banco Mundial.

- Diseño de la arquitectura backend de una plataforma de gestión de contenidos que utiliza modelos de machine learning para procesar y organizar grandes volúmenes de recursos para los usuarios finales.
- Integración de modelos de Hugging Face en el pipeline de procesamiento.

Stack: Python, Django, Hugging Face

**Senior Full Stack Engineer**
Selia · Jornada completa · Remoto · ene 2022 – sep 2023
Desde dic 2022, en paralelo con mis proyectos para el Grupo Banco Mundial.

- Diseño y construcción de la plataforma de pagos completa y de la plataforma B2B de Selia, con responsabilidad sobre la arquitectura backend.
- Integración de pasarelas de pago (Stripe) y optimización de la infraestructura para ganar escalabilidad y fiabilidad a medida que crecía el negocio.

Stack: Python, Django, Django REST Framework, PostgreSQL, AWS

**Full Stack Developer**
Grupo Banco Mundial · Freelance · Remoto · dic 2022 – mar 2023
En paralelo con mi puesto a jornada completa en Selia.

- Desarrollo de un portal para apoyar la reintegración de 900 mujeres asociadas a grupos armados, dentro de un proyecto de reintegración de excombatientes administrado por el BIRF.

**Senior Python Developer**
LSV-Tech (cliente: Nokia) · Jornada completa · Remoto · jun 2021 – dic 2021

- Desarrollo de nuevas funcionalidades y mantenimiento de la base de código en Django del producto Zina de Nokia (CRM/ERP).

**Lead Software Engineer**
Turpial Development · Jornada completa · Caracas, Venezuela · ene 2015 – jun 2021

- Liderazgo de equipos de desarrollo en la entrega de software a medida para clientes de Europa, Estados Unidos y Latinoamérica.
- Responsable de la arquitectura en AWS (EC2, Elastic Beanstalk, RDS, Route 53, S3), incluyendo balanceo de carga y autoscaling.
- Proyectos destacados: plataforma GIS para la Lista Roja de Ecosistemas de la UICN (Reino Unido), VenezuelaSinFiltro (medición de censura en Internet), Oterca (motor de optimización de sistemas de filtración de aire con datos en vivo) y SteamEnergy (monitorización de trampas de vapor industriales).

**Full Stack Developer**
Turpial Development · Jornada completa · Caracas, Venezuela · ene 2013 – dic 2014

- Proyectos web y móviles: un ERP a medida para una empresa de fotografía profesional, una app de servicios de mudanza bajo demanda (Denver, EE. UU.) y una plataforma de redes sociales.

Stack: Django, MySQL, JavaScript, PhoneGap

### Habilidades técnicas

- **Backend:** Python, Django, Django REST Framework, Celery, Redis, diseño de APIs REST, NestJS
- **IA y agentes:** integración de LLMs (API de OpenAI), tool calling, prompt engineering, Hugging Face, Claude Code, MCP, BMAD Method
- **Datos:** PostgreSQL, MySQL, CouchDB, modelado de datos, optimización de consultas
- **Cloud y DevOps:** AWS (EC2, ECS, RDS, Lambda, Elastic Beanstalk, S3, SQS, CloudFront, Route 53), Terraform, Docker, Linux, CI/CD con GitHub Actions
- **Frontend y móvil:** HTMX, Angular, TypeScript, JavaScript, React Native (Expo)
- **Testing:** pytest, Jest, Maestro, testing con contratos OpenAPI

### Certificaciones

Master AI Spec-Driven Development with BMAD Method · Udemy · jun 2026
ID de credencial: UC-5a8ad8a3-f861-4390-8fe0-b6b33e4dfea7 (mantener el enlace actual)

### Formación

- Estudios de Ingeniería de Sistemas · Universidad Metropolitana, Caracas
- Estudios de Ciencias de la Computación · Universidad Nueva Esparta, Caracas

### Idiomas

Español (nativo) · Inglés (B2, intermedio alto)

---

## EN

### Summary

Senior software engineer with more than {{ owner.years }} years building web platforms in Python and Django, focused on backend design, system architecture and bringing AI into real products. For three years I was an architect and developer for the World Bank Group, on community-driven development and climate platforms used across several African countries. I now work as a freelancer and have delivered a CRM and a warehouse management system built with agents from start to finish.

I have integrated generative AI into real products (LLMs through APIs, Hugging Face models in processing pipelines), and agent-driven development is at the center of how I work: Claude Code, agents with defined roles and phased specifications that I review and validate before merging.

### Generative AI and agents

- **LLMs in production:** model integration through APIs (OpenAI) with prompt engineering and tool calling; Hugging Face models in content processing pipelines.
- **Agents and multi-agent workflows:** daily work with Claude Code, agents with defined roles (BMAD Method), subagents, custom commands, instruction files and MCP servers.
- **Spec-driven development:** PRD, architecture, epics and per-story specs that agents implement and that I review before merging.
- **Validation of agent-generated code:** API contracts locked with OpenAPI, automated tests (pytest, Jest, Maestro) and CI on every change.

### Professional experience

**Senior Software Engineer, AI-driven development**
Freelance · Madrid · Jun 2026 – Present
Complete systems built with AI agents for my own clients.

*Management platform and CRM for a vacation and mid-term rental management company* (multi-tenant Django, PostgreSQL, HTMX, AWS Elastic Beanstalk)

- **Generative AI in production:** financial analysis service using an LLM (OpenAI API) that generates insights and recommendations on revenue, occupancy and channels in the dashboards, with per-company context, response caching and graceful degradation when the model is unavailable.
- **End-to-end CRM built with agents:** wrote the PRD, architecture and epics with BMAD and implemented the module with Claude Code: staged pipeline with drag-and-drop boards, reassignment, KPIs and analysis of closed leads. The first five epics, 19 stories, were implemented in two weeks.
- **Idealista integration:** listing sync with deduplication and property reconciliation, and automatic conversion of email inquiries into leads.
- **WhatsApp integration:** configurable templates, sending from the lead's record, inbound replies through webhooks and delivery status.
- **Quality of agent-generated code:** more than 2,000 automated tests in the module, CI on PostgreSQL in GitHub Actions, one spec per story and review before every merge.

*Warehouse management system for a logistics company* (Django, HTMX, PostgreSQL, Celery, AWS, Terraform)

- Sole technical owner for the client. Starting from the functional requirements, I designed the architecture from scratch and built the whole platform with AI agents: goods receiving, per-client stock visibility, self-service delivery requests and monthly pre-settlement.
- It replaced a day-to-day operation that ran on paper.

**Senior Full Stack Engineer & System Architect**
World Bank Group · Contract · Madrid, remote · Jun 2023 – Jun 2026
Alongside my role at Selia until Sep 2023 and Ekwi-three in 2024.

- Local development portal for community-driven development programs: initial data model, funder flow (filtered list, selection and submission of investment packages), moderator review with role-based permissions and a geographic layer with Mapbox. Led the 2024 phase, focused on scaling, new data analytics tools and usability.
- Climate Vulnerability Portal, a platform that monitors the impact of climate change on socio-political activity in African countries.
- Offline-first mobile app for participatory monitoring (React Native/Expo, SQLite): guided field visits with survey, GPS and photo, local storage with sync status, and data access isolated behind a repository layer. Built with AI agents.
- `e3-django-dynamic-forms`: a dynamic form engine for Django, solely authored, published on PyPI under the MIT license with 210 automated tests.
- SMS and email notifications module for a grievance redress system (Twilio, Africa's Talking, SendGrid, Mailchimp), which switches provider through configuration, and an LLM analysis layer in its diagnostics dashboard.

Stack: Python, Django, Django REST Framework, PostgreSQL, CouchDB, Celery, HTMX, React Native, AWS

**Full Stack Developer & System Architect**
Ekwi-three GmbH · Freelance · Remote · May 2024 – Dec 2024
Alongside my contract with the World Bank Group.

- Designed the backend architecture of a content management platform that uses machine learning models to process and organize large volumes of resources for end users.
- Integrated Hugging Face models into the processing pipeline.

Stack: Python, Django, Hugging Face

**Senior Full Stack Engineer**
Selia · Full-time · Remote · Jan 2022 – Sep 2023
From Dec 2022, alongside my projects for the World Bank Group.

- Designed and built Selia's full payment platform and B2B platform, owning the backend architecture.
- Integrated payment gateways (Stripe) and optimized the infrastructure for scalability and reliability as the business grew.

Stack: Python, Django, Django REST Framework, PostgreSQL, AWS

**Full Stack Developer**
World Bank Group · Freelance · Remote · Dec 2022 – Mar 2023
Alongside my full-time role at Selia.

- Developed a portal supporting the reintegration of 900 women associated with armed groups, part of an ex-combatant reintegration project administered by the IBRD.

**Senior Python Developer**
LSV-Tech (client: Nokia) · Full-time · Remote · Jun 2021 – Dec 2021

- Built new features and maintained the Django codebase of Nokia's Zina product (CRM/ERP).

**Lead Software Engineer**
Turpial Development · Full-time · Caracas, Venezuela · Jan 2015 – Jun 2021

- Led development teams delivering custom software for clients in Europe, the US and Latin America.
- Owned the AWS architecture (EC2, Elastic Beanstalk, RDS, Route 53, S3), including load balancing and auto-scaling.
- Selected projects: GIS platform for the IUCN Red List of Ecosystems (UK), VenezuelaSinFiltro (internet censorship measurement), Oterca (air filtration optimization engine with live data integrations) and SteamEnergy (industrial steam trap monitoring).

**Full Stack Developer**
Turpial Development · Full-time · Caracas, Venezuela · Jan 2013 – Dec 2014

- Web and mobile projects: a custom ERP for a professional photography company, an on-demand moving services app (Denver, US) and a social media platform.

Stack: Django, MySQL, JavaScript, PhoneGap

### Technical skills

- **Backend:** Python, Django, Django REST Framework, Celery, Redis, REST API design, NestJS
- **AI and agents:** LLM integration (OpenAI API), tool calling, prompt engineering, Hugging Face, Claude Code, MCP, BMAD Method
- **Data:** PostgreSQL, MySQL, CouchDB, data modeling, query optimization
- **Cloud and DevOps:** AWS (EC2, ECS, RDS, Lambda, Elastic Beanstalk, S3, SQS, CloudFront, Route 53), Terraform, Docker, Linux, CI/CD with GitHub Actions
- **Frontend and mobile:** HTMX, Angular, TypeScript, JavaScript, React Native (Expo)
- **Testing:** pytest, Jest, Maestro, OpenAPI contract testing

### Certifications

Master AI Spec-Driven Development with BMAD Method · Udemy · Jun 2026
Credential ID: UC-5a8ad8a3-f861-4390-8fe0-b6b33e4dfea7 (keep the current link)

### Education

- Systems Engineering studies · Universidad Metropolitana, Caracas
- Computer Science studies · Universidad Nueva Esparta, Caracas

### Languages

Spanish (native) · English (B2, upper intermediate)
