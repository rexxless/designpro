from django.apps import AppConfig
from django.db.backends.signals import connection_created


def compare_category_names(left, right):
    left, right = left.casefold(), right.casefold()
    return (left > right) - (left < right)


def register_category_collation(sender, connection, **kwargs):
    if connection.vendor == 'sqlite':
        connection.connection.create_collation('portal_casefold', compare_category_names)


class MainConfig(AppConfig):
    name = 'main'

    def ready(self):
        connection_created.connect(register_category_collation)
