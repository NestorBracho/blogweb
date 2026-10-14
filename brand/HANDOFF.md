Vamos a aplicar la nueva identidad visual del blog. La especificación está en `brand/BRAND.md` y los recursos ya generados en `brand/` (logo, favicons, OG image). Léelo antes de empezar. Trabaja por fases, verifica cada una antes de pasar a la siguiente, y al final dame el informe que pido abajo.

## Contexto que ya sé (verifícalo, no lo asumas)

- Marca: wordmark `~/bracho_` (prefijo `~/` atenuado, "bracho", y un cursor como barra baja en `#ae00ee`) y monograma `nb_`. Tipografía Roboto Mono 500, que `templates/base.html` ya carga desde Google Fonts.
- El modo oscuro es el **tema por defecto**; se activa con el atributo `dark` y la clase `.dark-mode` en `<html>` (`templates/base.html`, `static/js/common.js`). Las variables de color están en `:root` y `[dark]:root` de `static/css/main.css`.
- El logo actual es texto: `templates/lib/_main_navbar.html` → `<a class="logo__link">Bracho</a>`, con estilo en `.logo__link` de `main.css` (Poppins 700, 32px).
- El footer repite la marca en `templates/lib/_main_footer.html` → `<h3 class="footer__info__title">Bracho</h3>`.
- La OG image por defecto se define en `templates/lib/_main_meta_seo.html` con `{% static 'images/02.jpg' as default_social_image %}`. `main/tests.py` y `blog/tests.py` comprueban el `og:image`.
- Estáticos con `whitenoise.storage.CompressedManifestStaticFilesStorage` (nombres con hash).
- Bug conocido: en `static/favicon/site.webmanifest` los `src` de los iconos empiezan por `/` (`/web-app-manifest-192x192.png`), pero los archivos viven en `/static/favicon/` y no hay ninguna URL en la raíz que los sirva.
- `MEJORAS.md` tiene un punto abierto: "El logo y el título del footer siguen diciendo 'Bracho'; ¿se cambian a 'Nestor Bracho'?". La decisión es **mantener "bracho" como marca**, ahora con el wordmark nuevo.

## Fase 0 · Preparación

1. `git status`. Si hay cambios sin commitear o staged en la rama actual, **para y pregúntame**: no los muevas, no hagas stash, no los mezcles.
2. Actualiza `main` y crea la rama `feat/brand` desde ella.
3. La carpeta `brand/` está sin trackear: va en este PR, tal cual. **No modifiques los archivos de `brand/`**; si algo te parece mal en ellos, dímelo en el informe.

## Fase 1 · Wordmark en header y footer

1. Crea un include reutilizable `templates/lib/_brand_wordmark.html` con el wordmark como **texto vivo** (no SVG ni imagen):
   ```html
   <span class="brand-wordmark"><span class="brand-wordmark__prefix" aria-hidden="true">~/</span>bracho<span class="brand-wordmark__cursor" aria-hidden="true"></span></span>
   ```
2. Header: dentro de `.logo__link`, sustituye el texto `Bracho` por el include. Añade al enlace un `aria-label` traducible (`{% translate 'Bracho, home' %}` o similar) para que los lectores de pantalla no lean "virgulilla barra".
3. Footer: sustituye el texto del `h3.footer__info__title` por el mismo include, a un tamaño acorde con el footer. No toques la línea de copyright ni el crédito del theme.
4. CSS en `static/css/main.css`, junto a `.logo__link`. Reemplaza los estilos de Poppins del logo:
   - `.brand-wordmark`: `font-family: "Roboto Mono", "Courier New", monospace; font-weight: 500; letter-spacing: -0.03em; color: var(--heading-font-color); white-space: nowrap;`
   - `.brand-wordmark__prefix`: `color: var(--text-alt-color);`
   - `.brand-wordmark__cursor`: `display: inline-block; width: 0.5em; height: 0.11em; margin-left: 0.08em; background: #ae00ee; vertical-align: baseline;`. Color **fijo**, no `var(--primary-color)`, que en modo oscuro cambia a `#d60067`.
   - Tamaño en el header: que ocupe un ancho visual parecido al logo actual (prueba ~28px en escritorio). En `max-width: 576px`, que no empuje ni descuadre el botón hamburguesa.
   - Hover y focus del enlace: sin subrayado ni cambio de color; con un `:focus-visible` con outline claro.
   - **Sin animación** en el cursor.
5. i18n: `makemessages` para `es`, traduce la cadena nueva del `aria-label` y ejecuta `compilemessages`.

## Fase 2 · Favicons y manifest

1. Copia todo `brand/favicon/*` a `static/favicon/`, sobrescribiendo. Los nombres coinciden con los que ya usa `base.html`, así que esas etiquetas no cambian.
2. En `static/favicon/site.webmanifest`:
   - Pon los `src` de los iconos **relativos al manifest**, sin `/` inicial (`"web-app-manifest-192x192.png"`).
   - `theme_color` y `background_color` → `#10141f`.
   - Deja `name` y `short_name` como "Bracho".
3. En `base.html`, añade `<meta name="theme-color" content="#10141f">`.
4. Comprueba que, con `DEBUG=False` y tras `collectstatic`, `/static/favicon/site.webmanifest` y los dos PNG que referencia responden 200. WhiteNoise también sirve los nombres sin hash, pero verifícalo, no lo supongas.

## Fase 3 · OG image por defecto

1. Copia `brand/social/og-image.png` a `static/images/og-default.png`.
2. En `_main_meta_seo.html`, cambia la imagen por defecto de `images/02.jpg` a `images/og-default.png`. Las páginas y posts con imagen propia (`social_image_url`) la mantienen.
3. Antes de plantearte borrar `static/images/02.jpg`, busca si se usa en otro sitio. Si no se usa, **no lo borres**: déjalo anotado en el informe.
4. Ajusta los tests de `og:image` si hace falta. Añade uno que compruebe que una página sin imagen propia usa `og-default.png`.

## Fase 4 · Documentación

1. En `README.md`, añade una sección corta "Marca" que enlace a `brand/BRAND.md`.
2. En `MEJORAS.md`, marca como resuelto el punto del logo/título del footer. Anota la decisión: se mantiene "bracho" con el wordmark `~/bracho_`.

## Fase 5 · Verificación (obligatoria antes del PR)

- `ruff check .` y `ruff format --check .` sin errores. Pasa también los hooks de `pre-commit`.
- `python manage.py check` y la suite de tests completa en verde.
- `collectstatic --noinput` sin errores con el storage de manifest. Hazlo en un `STATIC_ROOT` temporal si no quieres ensuciar el repo.
- Revisión visual con `runserver`, con capturas de:
  - header en modo oscuro y claro, en escritorio (1440px) y móvil (375px);
  - footer en ambos modos;
  - favicon en la pestaña, sobre tema claro y oscuro del navegador.
- En DevTools > Application > Manifest: los iconos cargan sin errores.
- Busca con grep que no quede ninguna referencia a la marca antigua que se te haya pasado (logo `Bracho` en Poppins, `logo__image`, imágenes de logo antiguas).

## Fase 6 · Commits y PR

- Commits pequeños y separados (conventional commits):
  1. `chore(brand): add brand kit`
  2. `feat(ui): new ~/bracho_ wordmark in header and footer`
  3. `fix(pwa): favicons and manifest icon paths`
  4. `feat(seo): branded default OG image`
  5. `docs: brand section and MEJORAS update`
- Abre un PR contra `main` con: resumen, las capturas de la fase 5 y una checklist de lo verificado. **No hagas merge ni despliegues.**

## No hagas

- No cambies `--primary-color`, los degradados ni la paleta del theme: la marca convive con ellos.
- No añadas fuentes ni dependencias nuevas.
- No uses los SVG del wordmark en el header (son para usos fuera de la web).
- No toques el crédito del theme en el footer: su licencia está sin revisar.
- No toques nada fuera del alcance de esta tarea. Si ves otros problemas, apúntalos en el informe.

## Informe final

Cuando termines, dame:
1. El enlace al PR.
2. La lista de archivos cambiados.
3. Las decisiones que tomaste por tu cuenta (tamaños, la traducción del aria-label…).
4. Cualquier cosa que no pudiste verificar.
5. Lo que queda para mí a mano: desplegar y ejecutar `collectstatic` en el servidor, refrescar la caché de la OG en LinkedIn Post Inspector, y poner `brand/logo/avatar-1024.png` en GitHub y LinkedIn.
