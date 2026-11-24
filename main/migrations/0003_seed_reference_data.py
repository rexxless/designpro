from django.db import migrations


def seed_reference_data(apps, schema_editor):
    database = schema_editor.connection.alias
    statuses = apps.get_model('main', 'Status').objects.using(database)
    categories = apps.get_model('main', 'Category').objects.using(database)

    for code, name in (
        ('new', 'Новая'),
        ('in_progress', 'Принято в работу'),
        ('completed', 'Выполнено'),
    ):
        if statuses.filter(code=code).exists():
            continue

        status, created = statuses.get_or_create(name=name, defaults={'code': code})
        if not created:
            status.code = code
            status.save(update_fields=['code'])

    for name in ('3D-дизайн', '2D-дизайн', 'Эскиз'):
        categories.get_or_create(name__iexact=name, defaults={'name': name})


class Migration(migrations.Migration):
    dependencies = [
        ('main', '0002_status_code'),
    ]

    operations = [
        migrations.RunPython(seed_reference_data, migrations.RunPython.noop),
    ]
