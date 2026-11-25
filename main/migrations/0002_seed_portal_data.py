from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.db import migrations


def seed_portal_data(apps, schema_editor):
    database = schema_editor.connection.alias
    statuses = apps.get_model('main', 'Status').objects.using(database)
    categories = apps.get_model('main', 'Category').objects.using(database)
    users = apps.get_model(settings.AUTH_USER_MODEL).objects.using(database)

    for code, name in (
        ('new', 'Новая'),
        ('in_progress', 'Принято в работу'),
        ('completed', 'Выполнено'),
    ):
        if statuses.filter(code=code).exists():
            continue
        statuses.update_or_create(name=name, defaults={'code': code})

    for name in ('3D-дизайн', '2D-дизайн', 'Эскиз'):
        categories.get_or_create(name__iexact=name, defaults={'name': name})

    users.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@example.com',
            'password': lambda: make_password('admin'),
            'is_active': True,
            'is_staff': True,
            'is_superuser': True,
        },
    )


class Migration(migrations.Migration):
    dependencies = [('main', '0001_initial')]

    operations = [migrations.RunPython(seed_portal_data, migrations.RunPython.noop)]
