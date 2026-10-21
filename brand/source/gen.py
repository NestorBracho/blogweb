"""Genera el paquete de marca 'Bracho' (dirección B · Terminal) con el texto convertido a trazos.

Qué necesita y cómo se ejecuta: README.md, en esta carpeta.
"""
import io, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_FILES = {w: os.path.join(HERE, f"package/files/roboto-mono-latin-{w}-normal.woff2") for w in (500, 700)}
HELP = f"See {os.path.join(HERE, 'README.md')}"

# Ni las dependencias ni la fuente están en el repo: si falta algo, decirlo antes de generar nada
try:
    import brotli  # fontTools lo necesita para leer WOFF2
    from fontTools.ttLib import TTFont
    from fontTools.pens.svgPathPen import SVGPathPen
    from fontTools.pens.boundsPen import BoundsPen
    from fontTools.pens.transformPen import TransformPen
    import cairosvg
    from PIL import Image
except (ImportError, OSError) as error:  # OSError: CairoSVG instalado, pero sin la librería Cairo del sistema
    sys.exit(f"Missing dependency: {str(error).splitlines()[0]}\n{HELP}")
missing = [path for path in FONT_FILES.values() if not os.path.exists(path)]
if missing:
    sys.exit(f"Missing font file: {missing[0]}\n{HELP}")

OUT = os.path.join(HERE, "out")
for d in ["logo", "favicon", "social"]:
    os.makedirs(os.path.join(OUT, d), exist_ok=True)

INK = "#10141f"        # --dark-blue del blog
PAPER = "#ffffff"
MUTED_L = "#697585"    # --blue-gray
MUTED_D = "#94a3b8"    # --dark-gray
TEXT_D = "#f0f0f0"     # --light-gray (modo oscuro)
ACCENT = "#ae00ee"     # --primary-color

FONTS = {w: TTFont(path) for w, path in FONT_FILES.items()}


def text_path(s, weight, size, x, y, tracking=-0.03):
    """Devuelve (d, bounds, advance) del texto s como trazos, baseline en y."""
    font = FONTS[weight]
    upm = font["head"].unitsPerEm
    gs = font.getGlyphSet()
    cmap = font.getBestCmap()
    k = size / upm
    pen = SVGPathPen(gs)
    bp = BoundsPen(gs)
    cx = x
    for ch in s:
        g = cmap[ord(ch)]
        t = (k, 0, 0, -k, cx, y)
        gs[g].draw(TransformPen(pen, t))
        gs[g].draw(TransformPen(bp, t))
        cx += gs[g].width * k + tracking * size
    return pen.getCommands(), bp.bounds, cx - x - tracking * size


def wordmark(dark=False, prefix=True, size=100):
    ink = TEXT_D if dark else INK
    muted = MUTED_D if dark else MUTED_L
    parts, x = [], 0
    if prefix:
        d, b1, adv = text_path("~/", 500, size, x, 0)
        parts.append((d, muted))
        x += adv + (-0.03 * size)
    d, b2, adv = text_path("bracho", 500, size, x, 0)
    parts.append((d, ink))
    x += adv + 0.08 * size
    cw, ch = 0.5 * size, 0.11 * size
    cursor = f'<rect x="{x:.2f}" y="{-ch:.2f}" width="{cw:.2f}" height="{ch:.2f}" fill="{ACCENT}"/>'
    xmax = x + cw
    # bounds en coordenadas SVG (y hacia abajo): b[1] = ascendente (negativo), b[3] = descendente
    top = b2[1]
    bottom = max(b2[3], 0)
    if prefix:
        top = min(top, b1[1])
        bottom = max(bottom, b1[3])
    pad = 0.04 * size
    vb = (-pad, top - pad, xmax + 2 * pad, (bottom - top) + 2 * pad)
    body = "".join(f'<path d="{d}" fill="{c}"/>' for d, c in parts) + cursor
    return vb, body


def svg(vb, body, w=None, h=None, bg=None):
    size = f' width="{w}" height="{h}"' if w else ""
    bgr = f'<rect x="{vb[0]}" y="{vb[1]}" width="{vb[2]}" height="{vb[3]}" fill="{bg}"/>' if bg else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb[0]:.2f} {vb[1]:.2f} {vb[2]:.2f} {vb[3]:.2f}"{size} role="img" aria-label="Bracho">'
            f'{bgr}{body}</svg>\n')


def monogram_body(full_bleed=False, scale=1.0, radius=12, simple=False):
    """Monograma 'nb' + cursor en un cuadrado 64x64."""
    bg = f'<rect width="64" height="64" fill="{INK}"/>' if full_bleed else f'<rect width="64" height="64" rx="{radius}" fill="{INK}"/>'
    if simple:
        return bg + f'<rect x="14" y="38" width="36" height="10" fill="{ACCENT}"/>'
    S = 27
    d, b, adv = text_path("nb", 700, S, 0, 0, tracking=-0.04)
    gap, cw, chh = 2.0, 12.0, 4.0
    total = adv + gap + cw
    # centrar ópticamente: caja de 'nb' (de ascendente de b a baseline)
    height = -b[1]
    ox = (64 - total * scale) / 2
    oy = 32 + (height * scale) / 2
    g = (f'<g transform="translate({ox:.2f} {oy:.2f}) scale({scale})">'
         f'<path d="{d}" fill="#ffffff"/>'
         f'<rect x="{adv + gap:.2f}" y="{-chh:.2f}" width="{cw}" height="{chh}" fill="{ACCENT}"/></g>')
    return bg + g


def write(path, s):
    with open(os.path.join(OUT, path), "w") as f:
        f.write(s)


def png(svg_str, path, w, h=None):
    cairosvg.svg2png(bytestring=svg_str.encode(), write_to=os.path.join(OUT, path), output_width=w, output_height=h or w)


# --- Logo
for dark in (False, True):
    for prefix in (True, False):
        vb, body = wordmark(dark, prefix)
        name = f"wordmark{'' if prefix else '-short'}-{'dark' if dark else 'light'}.svg"
        write(f"logo/{name}", svg(vb, body))

mono = svg((0, 0, 64, 64), monogram_body())
write("logo/monogram.svg", mono)
write("logo/monogram-square.svg", svg((0, 0, 64, 64), monogram_body(full_bleed=True)))
png(mono, "logo/monogram-512.png", 512)
# avatar para redes: cuadrado a sangre (las redes recortan en círculo), contenido en zona segura
avatar = svg((0, 0, 64, 64), monogram_body(full_bleed=True, scale=0.85))
png(avatar, "logo/avatar-1024.png", 1024)

# --- Favicon
write("favicon/favicon.svg", mono)
png(svg((0, 0, 64, 64), monogram_body(simple=True)), "favicon/_16.png", 16)
png(mono, "favicon/_32.png", 32)
png(mono, "favicon/_48.png", 48)
png(mono, "favicon/favicon-96x96.png", 96)
png(svg((0, 0, 64, 64), monogram_body(full_bleed=True)), "favicon/apple-touch-icon.png", 180)
maskable = svg((0, 0, 64, 64), monogram_body(full_bleed=True, scale=0.75))
png(maskable, "favicon/web-app-manifest-192x192.png", 192)
png(maskable, "favicon/web-app-manifest-512x512.png", 512)
ims = [Image.open(os.path.join(OUT, f"favicon/_{s}.png")).convert("RGBA") for s in (16, 32, 48)]
ims[2].save(os.path.join(OUT, "favicon/favicon.ico"), sizes=[(16, 16), (32, 32), (48, 48)], append_images=ims[:2])
for s in (16, 32, 48):
    os.remove(os.path.join(OUT, f"favicon/_{s}.png"))

# --- OG image 1200x630
vb, body = wordmark(dark=True, prefix=True, size=100)
W, H = 1200, 630
wm_w = 760
k = wm_w / vb[2]
wm_h = vb[3] * k
tag_d, tag_b, tag_adv = text_path("Science, storytelling & software", 500, 30, 0, 0, tracking=0)
url_d, url_b, url_adv = text_path("nestorbracho.com", 500, 24, 0, 0, tracking=0)
y0 = (H - wm_h) / 2 - 40
og = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
      f'<rect width="{W}" height="{H}" fill="{INK}"/>'
      f'<g transform="translate({(W - wm_w) / 2:.2f} {y0:.2f}) scale({k:.4f}) translate({-vb[0]:.2f} {-vb[1]:.2f})">{body}</g>'
      f'<path transform="translate({(W - tag_adv) / 2:.2f} {y0 + wm_h + 70:.2f})" d="{tag_d}" fill="{MUTED_D}"/>'
      f'<path transform="translate({(W - url_adv) / 2:.2f} {H - 56})" d="{url_d}" fill="{MUTED_L}"/>'
      f'<rect x="0" y="{H - 8}" width="{W}" height="8" fill="{ACCENT}"/>'
      f'</svg>')
write("social/og-image.svg", og)
png(og, "social/og-image.png", W, H)

# --- Hoja de contacto para revisar
def b64png(svg_str, w, h=None):
    import base64
    return base64.b64encode(cairosvg.svg2png(bytestring=svg_str.encode(), output_width=w, output_height=h or w)).decode()
print("ok")
