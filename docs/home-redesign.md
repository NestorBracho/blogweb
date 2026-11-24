# Brief: nueva home de nestorbracho.com (v2)

Estado: aprobado por Nestor · actualizado el 24 nov 2026
Sustituye a la versión anterior de este documento. Se lee junto con `home-design.md` (diseño) y `home-cases.md` (contenido de los casos).

## 1. Por qué

La home era la portada de un blog. Quien llegaba tenía que leer artículos para deducir qué hace Nestor y si le sirve. La raíz del dominio pasa a ser una página de posicionamiento profesional. El blog se conserva, deja de ser la portada y más adelante se muda a `blog.nestorbracho.com`.

## 2. Para quién

| Audiencia | Qué necesita ver en diez segundos | Acción que queremos |
|---|---|---|
| Headhunter o recruiter (llega desde LinkedIn) | Rol y seniority, stack, ubicación y modalidad, para quién ha trabajado, CV | Abrir el CV o LinkedIn |
| Cliente potencial (necesita un freelance) | Si resuelve problemas como el suyo, prueba de que ya lo ha hecho, cómo hablar con él | Escribir por el formulario de contacto |

Las dos audiencias leen la misma prueba (casos reales). Solo cambia el botón final. Hay una sola home.

## 3. Qué cambia respecto a la v1 de este brief

1. **Rediseño visual completo.** El sitio principal (home, casos, CV, contacto, about, privacidad) deja el theme Coderon y pasa a un layout base y un CSS nuevos, definidos en `home-design.md`. El blog (listado, post, categoría) conserva el theme actual hasta la fase 2.
2. **Los casos cambian.** Son siete, en dos grupos, con campos nuevos (grupo, línea de prueba, autoría, enlaces, cómo se construyó). El contenido está en `home-cases.md`.
3. **Decisiones cerradas**, ver sección 8.

## 4. Estructura de la home

En este orden, en una sola página. El detalle visual de cada sección está en `home-design.md`.

1. **Cabecera.** Wordmark, navegación (Casos, Cómo trabajo, Blog, CV), cambio de idioma y botón Contacto.
2. **Hero.** A la izquierda: nombre y rol, titular, una línea de credibilidad, dos botones (contacto primario, CV secundario) y enlaces a LinkedIn y GitHub. A la derecha: ficha de perfil con rol, stack, IA, experiencia, ubicación, modalidad e idiomas. Sin foto.
3. **Franja de clientes.** En texto, sin logotipos.
4. **Casos.** Dos grupos con rótulo. Ver sección 5.
5. **Cómo trabajo.** Cuatro pasos y un enlace al caso del CRM como ejemplo real.
6. **Qué ofrezco.** Tres bloques.
7. **Contacto.** Titular y dos botones que llevan a la página de contacto y al CV. El formulario no se incrusta en la home.
8. **Blog.** Como mucho los tres últimos posts en una lista compacta, con enlace al listado. Si no hay posts publicados, la sección no se muestra.
9. **Pie.** Wordmark, enlaces (Casos, Blog, CV, Sobre mí, Privacidad), copyright y franja de acento.

## 5. Sección Casos

- **Grupo 1, rótulo "Grupo Banco Mundial · 2023 a 2026":** el portal a ancho completo, y debajo la app móvil y `e3-django-dynamic-forms`.
- **Grupo 2, rótulo "Otros clientes y proyectos":** el CRM a ancho completo, y debajo Selia, el sistema de almacén y este sitio.
- Cada tarjeta muestra, si existen: etiqueta de autoría, cliente y periodo, título, línea de prueba, resumen y enlaces.
- Las dos tarjetas a ancho completo reservan un hueco para una captura. Sin captura, la tarjeta ocupa todo el ancho con el texto y no deja un hueco vacío.
- Un caso solo se publica si tiene completos título, resumen, problema y solución. Los demás quedan como borrador, visibles solo en desarrollo.
- Un campo marcado `[PENDIENTE]` no se pinta. Nunca se muestra el texto del marcador en producción.

## 6. Lo que se conserva

- Django 5.2, plantillas, htmx. Sin framework de frontend nuevo.
- Idiomas en la URL, `hreflang`, sitemap, datos schema.org (ADR 6).
- Página de CV, formulario de contacto con honeypot y rate limit, about, privacidad.
- Datos del propietario desde settings (`owner.*`).
- Marca Terminal (`brand/BRAND.md`): wordmark, colores, Roboto Mono.
- CSP sin scripts ni estilos inline, fuentes servidas por el propio sitio, CI, tests y despliegue.
- Lo ya hecho en la rama anterior: listado del blog en `/{lang}/blog/` y la base de datos, vistas y URLs de los casos.

## 7. Restricciones

- Mismo repo y mismo stack. Sin dependencias de frontend nuevas ni peticiones a CDNs.
- Todo en inglés y español.
- La home y las páginas de caso funcionan sin JavaScript.
- Temas claro y oscuro, con el oscuro por defecto.
- Ninguna URL de post, categoría o feed cambia.
- En los textos del sitio no se usan rayas largas.
- No se inventa contenido: ni cifras, ni resultados, ni clientes.
- **Anonimato.** Dos clientes son anónimos y así aparecen en `home-cases.md`. No se añade su nombre, su marca, su ciudad ni el nombre de sus repositorios en ningún archivo del repo: ni plantillas, ni datos, ni tests, ni comentarios, ni mensajes de commit. Del trabajo para el Banco Mundial no se nombra ningún país.
- No se usan logotipos de terceros.

## 8. Decisiones cerradas

1. Rol: "Senior Software Engineer" en home, CV y about.
2. Se puede nombrar al Grupo Banco Mundial como cliente. No se nombran países.
3. El caso de notificaciones e IA del sistema de quejas no tiene tarjeta: va como un punto dentro del caso del portal y como ejemplo en "Qué ofrezco".
4. El cliente del CRM es anónimo: "Gestora de alquiler vacacional y de media estancia", sin ciudad. Idealista y WhatsApp sí se nombran.
5. El cliente del sistema de almacén es anónimo: "Empresa de logística". Nestor es autor único.
6. El lema "Science, storytelling & software" se queda solo en el blog.
7. Titulares en Roboto Mono. Poppins solo para texto corrido.
8. La página about se mantiene y se enlaza desde el pie, no desde el menú.
9. El `<link>` del feed se queda como está hasta la fase 2.
10. Nestor terminó su contrato con el Grupo Banco Mundial en junio de 2026 y trabaja como freelance. El sitio habla del Banco en pasado.
11. El nombre se escribe "Nestor", sin acento, en los dos idiomas.
12. Nivel de inglés: B2.
13. El contenido del CV está en `cv-content.md`.

## 9. Fases

### Fase 1 · Home nueva (en curso)

Hecho: listado del blog en `/{lang}/blog/`, y datos, vistas y URLs de los casos.

Falta:
- Layout base y CSS nuevos para el sitio principal.
- Home con la estructura de la sección 4.
- Página de detalle de caso con el diseño nuevo.
- CV, contacto, about y privacidad sobre el layout nuevo, sin cambiar su contenido.
- Campos nuevos de los casos y carga del contenido de `home-cases.md`.
- Navegación y pie nuevos. En las páginas del blog, la navegación del theme actual enlaza también a Casos.
- `owner.role`, imagen social y datos estructurados acordes al nuevo posicionamiento.
- Pendientes de la revisión anterior: el h1 de `/blog/` y el test de la ruta de la hoja de estilos.

### Fase 2 · Blog a blog.nestorbracho.com

Dos hosts desde el mismo Django, redirecciones 301, canonical, sitemap, `hreflang`, robots, cookies y DNS. ADR propio.

### Fase 3 · Agente "pregunta por mi experiencia"

Responde solo desde el CV y los casos publicados. Especificación propia antes de construir.

## 10. Criterios de aceptación de la fase 1

1. En el primer pantallazo de escritorio (1440 × 900) se leen nombre, rol, titular, los dos botones y la ficha de perfil.
2. A 360 px de ancho no hay scroll horizontal en ninguna página nueva y los botones miden al menos 44 px de alto.
3. La home y las páginas de caso coinciden con `design/home.html` y `design/case-detail.html` en estructura, tipografía, espaciado y color.
4. Home y páginas de caso existen en `/en/` y `/es/`, con `hreflang`, canonical, Open Graph y entrada en el sitemap.
5. Temas claro y oscuro correctos en todas las páginas del sitio principal, con contraste de texto de al menos 4,5:1.
6. Ninguna URL de post, categoría o feed devuelve algo distinto de lo que devuelve hoy.
7. Sin violaciones de CSP en la consola y sin peticiones a dominios de terceros.
8. `ruff check .`, `ruff format --check .` y `manage.py test` pasan; las vistas, URLs y campos nuevos tienen tests.
9. Ningún marcador `[PENDIENTE]` ni texto de relleno visible con `DEBUG=False`.
10. Una búsqueda en el repo no encuentra nombres de los clientes anónimos ni de países del trabajo para el Banco Mundial.

## 11. Pendiente de Nestor (no bloquea el desarrollo)

1. Frase exacta sobre su papel en la fase de 2024 del portal.
2. Capturas del portal y del tablero del CRM con datos de demostración.
3. Contenido del caso del sistema de almacén.
4. Problema y resultado del caso de Selia.
5. Estado actual de la app móvil, para su frase de resultado.
6. Disponibilidad, si quiere mostrarla en la ficha del hero.
7. Hecho: la página de CV sale de `cv-content.md`, y `resume.md` se borró porque ya no se usaba.
