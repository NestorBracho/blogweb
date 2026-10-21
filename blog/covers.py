"""
Post covers at the size each part of the site shows them. Post.save() makes them whenever the cover changes, and the
make_cover_sizes command makes them for covers saved before this existed, or again after SIZES changes.
"""

import hashlib
import io

from django.core.files.base import ContentFile
from django.db.models.fields.files import FieldFile
from PIL import Image, ImageOps

# Every place a cover appears is a 4:3 box that the image fills, cropped around its centre (CSS object-fit: cover).
# Width and height are the largest that box gets, in CSS pixels; the files are twice that, for high-density screens.
SIZES = {
    'post': (856, 642),  # top of the post page
    'card': (412, 309),  # post cards (home, categories), category covers and search results
    'thumb': (90, 68),  # sidebar, footer and the previous/next links of a post
}
# Link previews (og:image): the size LinkedIn and others recommend, as a JPEG because not every site reads WebP
SOCIAL_SIZE = (1200, 630)


def make_sizes(cover: FieldFile, folder: str) -> dict[str, str]:
    """
    Saves `cover` at every size under covers/<folder>/ and returns the paths by size name. Files are named after the
    cover's content and their size, so a new cover or a new size gets new URLs (Cloudflare caches /media/ for 30 days),
    and sizes that already exist are not made again.
    """
    with cover.open('rb'):
        data = cover.read()
    digest = hashlib.sha256(data).hexdigest()[:12]
    targets = {name: (2 * width, 2 * height, 'webp') for name, (width, height) in SIZES.items()}
    targets['social'] = (*SOCIAL_SIZE, 'jpg')
    paths = {name: f'covers/{folder}/{digest}-{width}x{height}.{ext}' for name, (width, height, ext) in targets.items()}

    missing = [name for name, path in paths.items() if not cover.storage.exists(path)]
    if missing:
        with Image.open(io.BytesIO(data)) as original:
            image = without_transparency(ImageOps.exif_transpose(original))
        for name in missing:
            width, height, ext = targets[name]
            output = io.BytesIO()
            if ext == 'webp':
                fit(image, width, height).save(output, 'WEBP', quality=80, method=6)
            else:
                fit(image, width, height).save(output, 'JPEG', quality=82, optimize=True, progressive=True)
            cover.storage.save(paths[name], ContentFile(output.getvalue()))
    return paths


def stored_size(storage, path: str) -> tuple[int, int] | None:
    """Width and height of a size already saved (small covers make smaller ones), read from the file's header."""
    try:
        with storage.open(path) as file, Image.open(file) as image:
            return image.size
    except OSError:
        return None


def fit(image: Image.Image, width: int, height: int) -> Image.Image:
    """The image cropped to the shape of width x height around its centre and scaled down to it, never up."""
    scale = min(1, image.width / width, image.height / height)
    return ImageOps.fit(image, (round(width * scale), round(height * scale)), Image.Resampling.LANCZOS)


def without_transparency(image: Image.Image) -> Image.Image:
    """An RGB copy of the image, with any transparent parts on white."""
    if image.mode == 'RGB':
        return image.copy()
    rgba = image.convert('RGBA')
    return Image.alpha_composite(Image.new('RGBA', rgba.size, 'white'), rgba).convert('RGB')
