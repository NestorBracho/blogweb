# Bracho: identidad visual

Marca personal de Nestor Bracho (nestorbracho.com). Dirección "Terminal": el nombre como si fuera una ruta en la shell, con el cursor esperando.

## Logo

| Pieza | Archivo | Cuándo usarla |
|---|---|---|
| Wordmark completo | `logo/wordmark-light.svg`, `logo/wordmark-dark.svg` | Header del blog, cabecera de propuestas y CV, OG image |
| Wordmark corto | `logo/wordmark-short-light.svg`, `logo/wordmark-short-dark.svg` | Firma de email, pies de página, espacios estrechos |
| Monograma | `logo/monogram.svg` (esquinas redondeadas), `logo/monogram-square.svg` (a sangre) | Favicon, icono de app, sellos pequeños |
| Avatar | `logo/avatar-1024.png` | GitHub, LinkedIn, chess.com (la red lo recorta en círculo) |

- Todos los SVG tienen el texto **convertido a trazos**: se ven igual sin tener la fuente instalada.
- `-light` = para fondo claro; `-dark` = para fondo oscuro.
- **Espacio libre:** alrededor del logo, como mínimo la altura de la "b".
- **Tamaño mínimo:** wordmark 96 px de ancho; por debajo, monograma.
- **No:** cambiar los colores de las piezas, poner el cursor en otro color, añadir sombras o degradados, separar `~/` y `bracho` en líneas distintas.

## Color

| Token | Hex | Uso |
|---|---|---|
| Ink | `#10141f` | Texto del logo sobre claro, fondo del monograma (= `--dark-blue`) |
| Paper | `#ffffff` | Fondo claro |
| Muted (claro) | `#697585` | `~/` sobre fondo claro (= `--blue-gray`) |
| Muted (oscuro) | `#94a3b8` | `~/` sobre fondo oscuro (= `--dark-gray`) |
| Text (oscuro) | `#f0f0f0` | Texto del logo sobre oscuro (= `--light-gray`) |
| **Accent** | `#ae00ee` | **Solo el cursor** y detalles puntuales (= `--primary-color` en modo claro) |

El acento del logo es fijo en `#ae00ee` también en modo oscuro, aunque el theme cambie `--primary-color` a `#d60067`: el logo no cambia con el theme.

## Tipografía

- **Logo:** Roboto Mono 500 (el wordmark) y 700 (el monograma), con tracking -0.03em. El blog ya carga Roboto Mono, así que no añade peticiones.
- **Texto del sitio:** Poppins, como hasta ahora.

## Regenerar

`source/gen.py` genera todo el paquete desde la fuente (Roboto Mono de @fontsource). Cambia los colores arriba del script y vuelve a correrlo; qué necesita y cómo se ejecuta está en [`source/README.md`](source/README.md).
