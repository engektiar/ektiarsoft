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


@deconstructible
class DatabaseStorage(Storage):
    """Stores uploads as rows in core_storedfile — no extra service needed.
    Fine for a portfolio (a handful of images, each max 4 MB)."""

    def _model(self):
        from apps.core.models import StoredFile

        return StoredFile

    def _save(self, name, content):
        import mimetypes

        name = name.replace("\\", "/")
        if hasattr(content, "seek"):
            content.seek(0)
        data = content.read()
        ctype = getattr(content, "content_type", None) or mimetypes.guess_type(name)[0] or "application/octet-stream"
        self._model().objects.update_or_create(
            name=name, defaults={"content": data, "content_type": ctype, "size": len(data)})
        return name

    def _open(self, name, mode="rb"):
        obj = self._model().objects.get(name=name)
        return ContentFile(bytes(obj.content), name=name)

    def exists(self, name):
        return self._model().objects.filter(name=name).exists()

    def delete(self, name):
        if name:
            self._model().objects.filter(name=name).delete()

    def size(self, name):
        return self._model().objects.filter(name=name).values_list("size", flat=True).first() or 0

    def url(self, name):
        from urllib.parse import quote

        return "/files/" + quote(name.replace("\\", "/"))
