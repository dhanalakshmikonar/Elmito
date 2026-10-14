# Deploying EL MITO on Render Free

## Deploy

- Build command: `./build.sh`
- Start command: `bash start.sh`
- Set `DJANGO_SETTINGS_MODULE=config.settings.prod` and a production `SECRET_KEY`.
- Leave `DATABASE_URL` unset to use the project's SQLite file, `db.sqlite3`.
- Leave `MEDIA_ROOT` unset to use the source snapshot's `media/` directory (do not set the
  old `/var/data/media` path on a Free service).

Both projects use Django's ordinary `FileSystemStorage`. Noplastiks sets `MEDIA_ROOT` to its
project's `media/`, uses `products/` as the image upload path, and serves `/media/` while `DEBUG`
is enabled. Its ZIP's Git index contains `db.sqlite3` and 12 files under `media/products/`; those
committed files are part of the source snapshot. EL MITO now allows its SQLite and media files to
be included in that same kind of snapshot.

This does **not** make new Admin uploads durable on Render Free. EL MITO writes them below
`MEDIA_ROOT` and stores only the relative filename (such as `products/name.jpg`) in SQLite. Render
Free discards runtime filesystem changes when the service spins down, restarts, or redeploys. The
SQLite database is ephemeral for the same reason. Django does not copy uploads back into Git, and
the Noplastiks ZIP contains no code that does so. Its checked-in images survive as deployment
files; the archive does not establish that an upload made after the deployed snapshot survives a
Free service restart.

Therefore there is no implementation that can guarantee persistence of newly uploaded Admin
files across Free restarts while also using only the service's local filesystem and requiring no
external/persistent storage or source snapshot updates. That is a Render platform constraint,
not a difference in Django's image field or URL handling. The closest option within these limits
is to use committed media/database snapshots, which requires carrying each new upload into a
future source snapshot. For automatic persistence, the constraint must change to permit durable
storage outside the Free instance.

## First deploy

The deploy runs `build.sh` to install dependencies and collect static files. `start.sh` applies
SQLite migrations, creates the cache table, verifies the product table, and starts Gunicorn.
Create the admin account with `python manage.py createsuperuser` where shell access is available,
or configure the existing bootstrap-superuser environment variables.

Set the remaining payment, email, and domain environment variables as described in `.env.example`.
