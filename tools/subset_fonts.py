"""
Makes the font files in static/fonts/, which the site serves itself, from the original fonts:

- Poppins and Roboto Mono, cut down to the characters of Google Fonts' "latin" subset, which covers English and
  Spanish (á é í ó ú ñ ü ¿ ¡ « » — …), and to the weights and styles the stylesheets use.
- Font Awesome, cut down to the icons listed in static/fonts/fontawesome/icons.txt.

The originals are downloaded at fixed versions: Poppins and Roboto Mono from the google/fonts repository (the files
Google Fonts serves), Font Awesome Free 6.5.1 from npm (the version static/css/main.css was made for). Their licenses
are copied next to the fonts.

Run it again after adding an icon to icons.txt or a weight below. fontTools is not one of the site's dependencies,
so run the script with it alongside, for example with uv:

    uv run --no-project --with fonttools==4.66.1 --with brotli==1.2.0 python tools/subset_fonts.py
"""

import hashlib
import io
import re
import tarfile
import urllib.request
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

STATIC = Path(__file__).resolve().parent.parent / 'static'
FONTS = STATIC / 'fonts'

GOOGLE_FONTS = 'https://raw.githubusercontent.com/google/fonts/45e3d5269e4a17d823f6d84470bc084dc5ae46f6/ofl/'
FONT_AWESOME = 'https://registry.npmjs.org/@fortawesome/fontawesome-free/-/fontawesome-free-6.5.1.tgz'
FONT_AWESOME_SHA256 = '6b659a2f6596db8403e3761c81e64179383ee9476a9c4f09f4bcca929f94661e'

LATIN = subset.parse_unicodes(
    'U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,'
    'U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD'
)

# Original in google/fonts: file in static/fonts/. Poppins is used at 400, 500 (navigation), 600 (buttons, labels)
# and 700 (headings), never in italics: <em> is in Roboto Mono.
POPPINS = {
    'poppins/Poppins-Regular.ttf': 'poppins/poppins-400.woff2',
    'poppins/Poppins-Medium.ttf': 'poppins/poppins-500.woff2',
    'poppins/Poppins-SemiBold.ttf': 'poppins/poppins-600.woff2',
    'poppins/Poppins-Bold.ttf': 'poppins/poppins-700.woff2',
}
ROBOTO_MONO = {
    'robotomono/RobotoMono[wght].ttf': 'roboto-mono/roboto-mono.woff2',
    'robotomono/RobotoMono-Italic[wght].ttf': 'roboto-mono/roboto-mono-italic.woff2',
}
# Roboto Mono is a variable font. Nothing on the site is lighter than 400, so its lighter weights are left out.
ROBOTO_MONO_WEIGHTS = (400, 700)

# The Font Awesome fonts main.css declares, by the name icons.txt uses for them
FONT_AWESOME_FONTS = {'solid': 'fa-solid-900', 'regular': 'fa-regular-400', 'brands': 'fa-brands-400'}


def main():
    for original, path in POPPINS.items():
        save(cut(TTFont(io.BytesIO(download(GOOGLE_FONTS + original)), recalcTimestamp=False), LATIN), path)
    for original, path in ROBOTO_MONO.items():
        font = cut(TTFont(io.BytesIO(download(GOOGLE_FONTS + original)), recalcTimestamp=False), LATIN)
        save(instancer.instantiateVariableFont(font, {'wght': ROBOTO_MONO_WEIGHTS}), path)
    for family, folder in [('poppins', 'poppins'), ('robotomono', 'roboto-mono')]:
        (FONTS / folder / 'OFL.txt').write_bytes(download(f'{GOOGLE_FONTS}{family}/OFL.txt'))

    package = download(FONT_AWESOME)
    if hashlib.sha256(package).hexdigest() != FONT_AWESOME_SHA256:
        raise SystemExit(f'{FONT_AWESOME} is not the file this script was written for')
    with tarfile.open(fileobj=io.BytesIO(package)) as archive:
        for style, codepoints in icon_codepoints().items():
            original = archive.extractfile(f'package/webfonts/{FONT_AWESOME_FONTS[style]}.ttf').read()
            font = cut(TTFont(io.BytesIO(original), recalcTimestamp=False), codepoints)
            missing = set(codepoints) - set(font.getBestCmap() or {})
            if missing:
                raise SystemExit(f'The {style} font has no {", ".join(f"{c:x}" for c in missing)}')
            save(renamed(font), f'fontawesome/{FONT_AWESOME_FONTS[style]}.woff2')
        (FONTS / 'fontawesome' / 'LICENSE.txt').write_bytes(archive.extractfile('package/LICENSE.txt').read())


def download(url):
    with urllib.request.urlopen(url) as response:
        return response.read()


def cut(font, codepoints):
    """The font with only the glyphs for these code points."""
    options = subset.Options()
    options.name_IDs = ['*']  # keep the copyright and license notices
    # As in the files Google Fonts serves; without the glyph names Chrome on macOS draws the text slightly differently
    options.glyph_names = True
    subsetter = subset.Subsetter(options)
    subsetter.populate(unicodes=codepoints)
    subsetter.subset(font)
    return font


def save(font, path):
    path = FONTS / path
    path.parent.mkdir(parents=True, exist_ok=True)
    font.flavor = 'woff2'
    font.save(path)
    print(f'{path.relative_to(STATIC.parent)}: {path.stat().st_size / 1024:.1f} KB')


def icon_codepoints():
    """The code point of each icon in icons.txt, by font, as main.css defines it (.fa-xmark:before { content: … })."""
    css = (STATIC / 'css' / 'main.css').read_text()
    codepoints = {}
    for selectors, codepoint in re.findall(r'([^{}]+)\{\s*content:\s*"\\([0-9a-f]+)"\s*\}', css):
        for name in re.findall(r'\.fa-([a-z0-9-]+)::?before', selectors):
            codepoints[name] = int(codepoint, 16)

    icons = {style: [] for style in FONT_AWESOME_FONTS}
    for line in (FONTS / 'fontawesome' / 'icons.txt').read_text().splitlines():
        if line.strip() and not line.startswith('#'):
            style, name = line.split()
            icons[style].append(codepoints[name])
    return icons


def renamed(font):
    """
    The font under another name. Font Awesome's license (the SIL OFL) reserves the name "Font Awesome" for its own
    fonts, and a cut-down copy is a modified version. The stylesheet still calls it "Font Awesome 6 Free".
    """
    for record in font['name'].names:
        if record.nameID in {1, 3, 4, 6, 16}:  # family, unique, full, PostScript and typographic family names
            name = record.toUnicode().replace('Font Awesome 6', 'Bracho Icons').replace('FontAwesome6', 'BrachoIcons')
            record.string = name
    return font


if __name__ == '__main__':
    main()
