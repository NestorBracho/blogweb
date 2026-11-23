# Diseño: sitio principal de nestorbracho.com

Estado: aprobado por Nestor · 23 nov 2026
Referencia visual: `design/home.html` y `design/case-detail.html`. Ábrelos en un navegador antes de empezar.

## 0. Cómo usar este documento

- Los dos HTML son la **referencia visual**, no código de producción. Tienen los estilos inline y cargan las fuentes de Google Fonts solo para poder abrirlos sueltos. En el sitio nada de eso está permitido (CSP, fuentes propias).
- La implementación reproduce estructura, tipografía, espaciado y color de la referencia, con plantillas de Django y una hoja de estilos con clases y variables CSS.
- Los valores numéricos de este documento salen de la referencia. Si hay una diferencia entre este documento y los HTML, manda el HTML, salvo en lo que aquí se dice expresamente que cambia.
- La referencia solo existe en tema oscuro y en español. El tema claro se construye con la tabla de la sección 2. Los textos en inglés están en `home-cases.md` y, para el resto, se traducen con gettext.
- Los textos entre corchetes de la referencia son marcadores de contenido pendiente. No se implementan como texto.

## 1. Carácter

Terminal, sobrio y preciso. Esquinas rectas en todo. Sin sombras, sin degradados, sin iconos decorativos, sin animaciones. La jerarquía se construye con tipografía, líneas de 1 px y espacio.

## 2. Color

Variables CSS en `:root` para el tema claro y en `[dark]:root` para el oscuro, igual que hace hoy el sitio. El oscuro es el tema por defecto.

| Token | Oscuro | Claro | Uso |
|---|---|---|---|
| `--bg` | `#10141f` | `#ffffff` | Fondo de página |
| `--bg-alt` | `#0c1018` | `#f8fafc` | Secciones alternas, ficha, línea de prueba, huecos de captura |
| `--text` | `#f0f0f0` | `#10141f` | Titulares y texto principal |
| `--text-2` | `#c3cad6` | `#3b4556` | Párrafos y texto secundario |
| `--muted` | `#94a3b8` | `#697585` | Rótulos, metadatos, prefijo `~/` |
| `--line` | `#232a3a` | `#e7e7e9` | Líneas y bordes de sección y de tarjeta |
| `--line-soft` | `#1b2130` | `#f0f1f3` | Separadores dentro de la ficha |
| `--line-strong` | `#2c3446` | `#cdd3dc` | Borde de etiquetas |
| `--line-btn` | `#5b667a` | `#697585` | Borde del botón secundario y regla de "Qué ofrezco" |
| `--btn-bg` | `#f0f0f0` | `#10141f` | Fondo del botón primario |
| `--btn-text` | `#10141f` | `#ffffff` | Texto del botón primario |
| `--accent` | `#ae00ee` | `#ae00ee` | Fijo en los dos temas |

Reglas del acento:
- Solo se usa en el cursor del wordmark, en la marca de 24 × 2 px que precede a cada rótulo de sección, en la marca de la cabecera de la ficha y en la franja inferior del pie.
- Nunca como color de texto, de botón, de enlace o de fondo de sección.

## 3. Tipografía

- **Roboto Mono**: wordmark, titulares (h1, h2, h3), rótulos, metadatos, navegación, etiquetas, línea de prueba y claves de la ficha.
- **Poppins**: párrafos, valores de la ficha y texto de los botones.
- Pesos necesarios: Roboto Mono 400, 500 y 700; Poppins 400, 500 y 600. Comprueba qué pesos y caracteres sirve hoy el sitio (`static/fonts/`, `tools/subset_fonts.py`) y regenera lo que falte. No se cargan fuentes desde fuera.

| Elemento | Fuente | Tamaño | Peso | Interlineado | Tracking |
|---|---|---|---|---|---|
| h1 | Roboto Mono | `clamp(28px, 3.4vw, 46px)` | 700 | 1.18 | -0.03em |
| h2 de sección | Roboto Mono | `clamp(23px, 2.5vw, 34px)` | 700 | 1.2 | -0.03em |
| h2 de contacto | Roboto Mono | `clamp(25px, 3vw, 40px)` | 700 | 1.18 | -0.03em |
| h3 tarjeta ancha | Roboto Mono | 25px | 700 | 1.25 | -0.03em |
| h3 tarjeta normal | Roboto Mono | 19px | 700 | 1.3 | -0.03em |
| h3 de paso y de oferta | Roboto Mono | 17px y 18px | 700 | normal | -0.02em |
| Rótulo, metadato | Roboto Mono | 13px | 400 | normal | normal |
| Navegación | Roboto Mono | 14px | 400 | normal | normal |
| Entradilla del hero | Poppins | 19px | 400 | 1.6 | normal |
| Párrafo | Poppins | 16px (15px en tarjeta normal) | 400 | 1.6 | normal |
| Wordmark de cabecera | Roboto Mono | 26px (22px por debajo de 576px) | 500 | normal | -0.03em |

Titulares con `text-wrap: balance`, párrafos con `text-wrap: pretty`.

## 4. Rejilla y espaciado

- Contenedor: `max-width: 1200px`, centrado, con 32px de padding lateral (20px por debajo de 576px).
- Padding vertical de sección: 96px (64px por debajo de 768px). Hero: 88px arriba y 96px abajo. Contacto: 104px. Blog: 72px.
- Cada sección se separa de la anterior con una línea superior de 1px `--line`. Las secciones "Cómo trabajo" y "Contacto" usan `--bg-alt`.
- Separación entre tarjetas: 24px. Entre rótulo de grupo y sus tarjetas: 32px.
- Todas las rejillas colapsan solas con `repeat(auto-fit, minmax(min(Npx, 100%), 1fr))`, sin media queries por componente: N = 320 en tarjetas, 240 en pasos, 300 en ofertas, 220 en la ficha del caso.

## 5. Componentes

**Wordmark.** El include existente `templates/lib/_brand_wordmark.html`, sin cambios.

**Rótulo de sección.** Marca de acento de 24 × 2 px, y a su derecha el número y el nombre: `01 / Casos`. Roboto Mono 13px, `--muted`.

**Rótulo de grupo.** Texto en Roboto Mono 14px peso 500, `--text`, seguido de una línea de 1px que ocupa el resto del ancho.

**Botón primario.** Fondo `--btn-bg`, texto `--btn-text`, Poppins 600, padding 14px 28px, sin radio. Lleva una flecha `→` al final.

**Botón secundario.** Transparente, borde de 1px `--line-btn`, Poppins 500, mismo tamaño.

**Enlace de texto.** `--text`, peso 500, con flecha `→` si es interno y `↗` si es externo. Subrayado al pasar el cursor. Área táctil de al menos 44px de alto.

**Foco.** `:focus-visible` con outline de 2px `--text` y 4px de separación en todos los elementos interactivos.

**Etiqueta de autoría.** Roboto Mono 12px, `--text-2`, borde de 1px `--line-strong`, padding 3px 9px, sin radio.

**Línea de prueba.** Roboto Mono 13px, `--text`, fondo `--bg-alt`, borde de 1px `--line`, padding 8px 12px. El texto puede partir en cualquier punto (`overflow-wrap: anywhere`).

**Tarjeta de caso normal.** Borde de 1px `--line`, padding 28px, columna con 16px de separación. Orden: etiqueta de autoría, cliente y periodo, título, línea de prueba, resumen, enlaces. Los enlaces se alinean al fondo de la tarjeta para que queden a la misma altura en toda la fila.

**Tarjeta de caso ancha.** Dos zonas en una fila que se apila en pantallas estrechas: texto (padding 36px) y hueco de captura (mínimo 320px de ancho y 260px de alto, fondo `--bg-alt`, línea izquierda de 1px). La captura se muestra con `object-fit: cover`. Sin captura, la zona de texto ocupa todo el ancho.

**Ficha de perfil (hero).** Caja con borde de 1px `--line` y fondo `--bg-alt`. Cabecera con la ruta `~/bracho/perfil` y una marca de acento. Debajo, una lista de definición en dos columnas (132px y el resto): clave en Roboto Mono 13px `--muted`, valor en Poppins 14px. Filas separadas por `--line-soft`. Marcado con `<dl>`.

Filas: rol, stack, ia, experiencia, ubicación, modalidad, idiomas. La fila de disponibilidad no se implementa hasta que Nestor la confirme. Rol, ubicación y años salen de `owner.*`; el resto son cadenas traducibles.

**Franja de clientes.** Una fila con el texto "He trabajado para" en `--muted` y los nombres en Roboto Mono 16px peso 500. Líneas de 1px arriba y abajo.

**Pasos de "Cómo trabajo".** Rejilla de cuatro celdas con bordes de 1px compartidos, formando una tabla. Cada celda: número, título y una frase. Marcado con `<ol>`.

**Bloques de "Qué ofrezco".** Tres columnas, cada una con una regla superior de 1px `--line-btn`, título y un párrafo.

**Lista del blog.** Filas con título a la izquierda y fecha a la derecha en Roboto Mono, separadas por líneas de 1px. Toda la fila es el enlace.

**Pie.** Wordmark, navegación secundaria y copyright en una fila que se apila. Debajo, una franja de 6px de alto en `--accent` a todo el ancho.

## 6. Página de detalle de caso

En este orden:

1. Cabecera del sitio.
2. Ruta (`~/casos / slug-del-caso`), h1 con el título, entradilla con el resumen y la línea de prueba.
3. Ficha en una fila de cuatro celdas sobre `--bg-alt`: cliente, periodo, rol, autoría.
4. Bloques con el rótulo a la izquierda (columna de 220px) y el contenido a la derecha (máximo 760px), que se apilan en pantallas estrechas:
   - El problema: párrafo.
   - Lo que construí: lista numerada con separadores de 1px.
   - Captura a ancho completo, si existe.
   - Cómo se construyó: párrafo, solo si el caso tiene ese campo.
   - Stack: etiquetas.
   - Resultado: párrafo, solo si existe.
   - Enlaces externos, si existen.
5. Enlace al siguiente caso, a todo el ancho, con título y flecha.
6. Llamada al contacto con los dos botones.
7. Pie.

Los rótulos se numeran según los bloques que realmente se pintan, sin saltos.

## 7. Resto de páginas del sitio principal

CV, contacto, about y privacidad pasan al layout base nuevo (cabecera, pie, tokens y tipografía de este documento) sin cambiar su contenido. Sus estilos propios se adaptan lo justo para que no queden restos del theme anterior: titulares en Roboto Mono, esquinas rectas, mismos botones y mismos campos de formulario (borde de 1px `--line-btn`, sin radio, fondo `--bg-alt`).

Las páginas del blog siguen con `templates/base.html` y el theme actual.

## 8. Accesibilidad y comportamiento

- Elementos reales: `<a>`, `<button>`, `<nav>`, `<dl>`, `<ol>`, un solo `<h1>` por página y jerarquía de titulares sin saltos.
- Los adornos (marcas de acento, flechas, cursor, prefijo `~/`) llevan `aria-hidden="true"`.
- Contraste de texto de al menos 4,5:1 en los dos temas. Compruébalo en el claro, que no tiene referencia visual.
- Sin JavaScript todo el contenido es legible y navegable. El cambio de tema y el menú en móvil pueden usar el JavaScript que ya tiene el sitio.
- Por debajo de 768px la navegación de la cabecera se resuelve como hoy (menú desplegable) o envolviendo los enlaces en dos líneas, lo que resulte más simple sin JavaScript nuevo.
- Respeta `prefers-reduced-motion`. No hay animaciones que desactivar, y no se añaden.
