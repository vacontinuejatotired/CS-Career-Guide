"""SQLite demonstration settings for the low-resource deployment profile.

The existing MySQL settings remain the default for development and future
production use. This module only changes the database and writable paths.
"""

import os
from pathlib import Path

from django.db.backends.signals import connection_created

from .settings import *  # noqa: F401,F403


def _database_path():
    value = os.getenv('DB_PATH', '/data/cs-career-guide.sqlite3')
    path = Path(os.path.expandvars(os.path.expanduser(value)))
    return path if path.is_absolute() else Path(BASE_DIR) / path


DB_FILE = _database_path()
DB_FILE.parent.mkdir(parents=True, exist_ok=True)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': str(DB_FILE),
        'OPTIONS': {
            'timeout': 20,
        },
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'cs-career-guide-sqlite',
        'TIMEOUT': 300,
    }
}

STATIC_ROOT = Path(os.getenv('STATIC_ROOT', '/data/staticfiles'))
MEDIA_ROOT = Path(os.getenv('MEDIA_ROOT', '/data/media'))
STATIC_ROOT.mkdir(parents=True, exist_ok=True)
MEDIA_ROOT.mkdir(parents=True, exist_ok=True)


def _enable_sqlite_wal(sender, connection, **kwargs):
    if connection.vendor == 'sqlite':
        with connection.cursor() as cursor:
            cursor.execute('PRAGMA journal_mode=WAL')
            cursor.execute('PRAGMA busy_timeout=20000')


connection_created.connect(_enable_sqlite_wal, dispatch_uid='cs_career_guide.sqlite_wal')
