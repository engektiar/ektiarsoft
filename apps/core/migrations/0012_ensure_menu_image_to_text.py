from django.db import migrations

URL = "/image-to-text/"


def ensure_menu_link(apps, schema_editor):
    """0011 originally wrote to the default database even when migrating another one;
    make sure the link exists in the database actually being migrated."""
    db = schema_editor.connection.alias
    MenuItem = apps.get_model("core", "MenuItem")
    if not MenuItem.objects.using(db).filter(url=URL).exists():
        MenuItem.objects.using(db).create(location="header", label="Image to Text", url=URL, order=80, is_active=True)


class Migration(migrations.Migration):
    dependencies = [("core", "0011_menu_image_to_text")]
    operations = [migrations.RunPython(ensure_menu_link, migrations.RunPython.noop)]
