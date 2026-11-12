"""Media storage on Cloudinary (used when the CLOUDINARY_URL env var is set).

Serverless hosts like Vercel have no persistent disk, so uploaded files
(profile photo, project images, blog covers, CV) are stored on Cloudinary.
The file *name* saved in the database stays the same as with local storage
(e.g. "profile/me.jpg"), so data can be moved between local and cloud freely.
"""
import os
import urllib.request

from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible

# extensions Cloudinary handles as "image" (transformable); everything else is "raw"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".avif", ".bmp", ".svg", ".ico", ".tif", ".tiff", ".pdf"}
FOLDER = os.environ.get("CLOUDINARY_FOLDER", "portfolio")


def _parts(name):
    """'profile/me.jpg' -> ('image', 'portfolio/profile/me', 'jpg')."""
    name = name.replace("\\", "/")
    base, ext = os.path.splitext(name)
    if ext.lower() in IMAGE_EXTENSIONS:
        return "image", f"{FOLDER}/{base}", ext.lstrip(".").lower()
    return "raw", f"{FOLDER}/{name}", ""  # raw files keep their extension in the public id


@deconstructible
class CloudinaryStorage(Storage):
    def _save(self, name, content):
        import cloudinary.uploader

        rtype, public_id, _ = _parts(name)
        if hasattr(content, "seek"):
            content.seek(0)
        cloudinary.uploader.upload(content, public_id=public_id, resource_type=rtype, overwrite=True, invalidate=True)
        return name.replace("\\", "/")

    def _open(self, name, mode="rb"):
        with urllib.request.urlopen(self.url(name), timeout=20) as resp:  # noqa: S310 (our own CDN URL)
            return ContentFile(resp.read(), name=name)

    def exists(self, name):
        import cloudinary.api

        rtype, public_id, _ = _parts(name)
        try:
            cloudinary.api.resource(public_id, resource_type=rtype)
            return True
        except Exception:  # NotFound, or API unreachable -> treat as free name
            return False

    def delete(self, name):
        import cloudinary.uploader

        if not name:
            return
        rtype, public_id, _ = _parts(name)
        cloudinary.uploader.destroy(public_id, resource_type=rtype, invalidate=True)

    def url(self, name):
        import cloudinary.utils

        rtype, public_id, fmt = _parts(name)
        options = {"resource_type": rtype, "secure": True}
        if rtype == "image":
            options.update(format=fmt, fetch_format="auto", quality="auto")  # smaller, faster images
        return cloudinary.utils.cloudinary_url(public_id, **options)[0]

    def size(self, name):
        return 0
