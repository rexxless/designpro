from django.conf import settings
from django.db import migrations


def seed_admin(apps, schema_editor):
    user_model = apps.get_model(settings.AUTH_USER_MODEL)
    user_model.objects.using(schema_editor.connection.alias).get_or_create(
        username='admin',
        defaults={
            'email': 'admin@example.com',
            'password': 'pbkdf2_sha256$1500000$syyNestnhEYcGjejeJyLqS$U2k5eyGVtC6dzf/VADR21i/mVcrQsN9OwXUUrQpi/JA=',
            'is_active': True,
            'is_staff': True,
            'is_superuser': True,
        },
    )


class Migration(migrations.Migration):
    dependencies = [
        ('main', '0004_alter_request_user'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunPython(seed_admin, migrations.RunPython.noop),
    ]
