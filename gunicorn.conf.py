"""Ensure the runtime SQLite database is migrated before Gunicorn serves requests."""

import os


def on_starting(server):
    """Run database setup in the master before worker processes are spawned."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.prod")

    import django

    django.setup()

    from django.core.management import call_command

    call_command("migrate", interactive=False, verbosity=1)
    call_command("createcachetable", verbosity=1)
    call_command("bootstrap_superuser", verbosity=1)

    from django.db import connection

    database_name = connection.settings_dict["NAME"]
    try:
        products_table_exists = (
            "products_product" in connection.introspection.table_names()
        )
    finally:
        # Do not carry the master's SQLite connection into forked workers.
        connection.close()

    if not products_table_exists:
        raise RuntimeError(
            "products_product is missing after migrations in database "
            f"{database_name}"
        )

