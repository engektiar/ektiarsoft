"""Copy this local site (database + uploaded files) to the cloud.

    1. put CLOUD_DATABASE_URL=<Neon connection string> and CLOUDINARY_URL=<…> in .env
    2. python manage.py clone_to_cloud

Database: the cloud database becomes an exact copy of the local one
(everything in it is REPLACED). Files: every uploaded file referenced in the
database is uploaded from media/ to Cloudinary under the same name.
"""
import io
import os
import tempfile

from django.apps import apps
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connections, models, transaction


class Command(BaseCommand):
    help = "Copy the local database and uploaded files to the cloud database (CLOUD_DATABASE_URL)."

    def add_arguments(self, parser):
        parser.add_argument("--yes", action="store_true", help="Do not ask for confirmation.")
        parser.add_argument("--skip-files", action="store_true", help="Only copy the database.")

    def handle(self, *args, yes=False, skip_files=False, **opts):
        if "cloud" not in settings.DATABASES:
            raise CommandError("Add CLOUD_DATABASE_URL=<your Neon connection string> to .env first.")
        target = settings.DATABASES["cloud"]
        where = f'{target.get("HOST") or ""}/{target.get("NAME")}'
        self.stdout.write(self.style.WARNING(
            f"This REPLACES everything in the cloud database ({where}) with a copy of your local site."))
        if not yes and input("Type 'yes' to continue: ").strip().lower() != "yes":
            raise CommandError("Cancelled - nothing was changed.")

        # 1) create tables in the cloud database
        self.stdout.write("1/4 Creating tables in the cloud database...")
        call_command("migrate", database="cloud", interactive=False, verbosity=0)

        # 2) export local data
        self.stdout.write("2/4 Exporting local data...")
        buf = io.StringIO()
        call_command("dumpdata", exclude=["sessions"], stdout=buf, verbosity=0)
        fd, dump = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:  # always UTF-8 (Windows default is cp1252)
            fh.write(buf.getvalue())
        try:
            # 3) wipe cloud data (incl. rows auto-created by migrations) and load the exact copy.
            #    One transaction: if anything fails, the cloud database is left untouched.
            self.stdout.write("3/4 Copying data...")
            with transaction.atomic(using="cloud"):
                call_command("flush", database="cloud", interactive=False, inhibit_post_migrate=True, verbosity=0)
                call_command("loaddata", dump, database="cloud", verbosity=0)
        finally:
            os.remove(dump)
        self._reset_sequences()

        # 4) upload files
        if skip_files:
            self.stdout.write("4/4 Skipped files (--skip-files).")
        else:
            self._upload_files()
        self.stdout.write(self.style.SUCCESS("Done! Your cloud database is now a copy of this site."))

    def _reset_sequences(self):
        """After loading rows with fixed IDs, PostgreSQL's ID counters must be moved past them."""
        conn = connections["cloud"]
        if conn.vendor != "postgresql":
            return
        with conn.cursor() as cur:
            for model in apps.get_models():
                pk = model._meta.pk
                if isinstance(pk, (models.AutoField, models.BigAutoField)):
                    table = model._meta.db_table
                    cur.execute(
                        f"SELECT setval(pg_get_serial_sequence(%s, %s), COALESCE(MAX({conn.ops.quote_name(pk.column)}), 1), "
                        f"MAX({conn.ops.quote_name(pk.column)}) IS NOT NULL) FROM {conn.ops.quote_name(table)}",
                        [table, pk.column],
                    )

    def _upload_files(self):
        """Uploads go to Cloudinary if CLOUDINARY_URL is set, otherwise into the cloud database."""
        import mimetypes

        from apps.core.models import StoredFile
        from apps.core.storage import CloudinaryStorage

        use_cloudinary = bool(os.environ.get("CLOUDINARY_URL"))
        target = "Cloudinary" if use_cloudinary else "the cloud database"
        storage, done, missing = (CloudinaryStorage() if use_cloudinary else None), 0, []
        names = set()
        for model in apps.get_models():
            fields = [f for f in model._meta.fields if isinstance(f, models.FileField)]
            for f in fields:
                for name in model.objects.exclude(**{f.name: ""}).values_list(f.name, flat=True):
                    if name:
                        names.add(name)
        self.stdout.write(f"4/4 Uploading {len(names)} file(s) to {target}...")
        for name in sorted(names):
            path = os.path.join(settings.MEDIA_ROOT, name)
            if not os.path.exists(path):
                missing.append(name)
                continue
            with open(path, "rb") as fh:
                if use_cloudinary:
                    storage._save(name, fh)
                else:
                    data = fh.read()
                    StoredFile.objects.using("cloud").update_or_create(name=name, defaults={
                        "content": data, "size": len(data),
                        "content_type": mimetypes.guess_type(name)[0] or "application/octet-stream"})
            done += 1
            self.stdout.write(f"   ok  {name}")
        if missing:
            self.stdout.write(self.style.WARNING(f"   Not found locally (skipped): {', '.join(missing)}"))
        self.stdout.write(f"   Uploaded {done} file(s).")
