from django.db import migrations

URL = "/image-to-text/"


def add_menu_link(apps, schema_editor):
    db = schema_editor.connection.alias  # the database being migrated
    MenuItem = apps.get_model("core", "MenuItem")
    if not MenuItem.objects.using(db).filter(url=URL).exists():
        MenuItem.objects.using(db).create(location="header", label="Image to Text", url=URL, order=80, is_active=True)


def remove_menu_link(apps, schema_editor):
    db = schema_editor.connection.alias  # the database being migrated
    apps.get_model("core", "MenuItem").objects.using(db).filter(url=URL, label="Image to Text").delete()


class Migration(migrations.Migration):
    dependencies = [("core", "0010_stored_file")]
    operations = [migrations.RunPython(add_menu_link, remove_menu_link)]
