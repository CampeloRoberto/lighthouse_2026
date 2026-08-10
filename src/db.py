"""Helper de conexao com o Postgres local usado no desafio (reuso entre os scripts)."""

import os

import psycopg2

DB_CONFIG = {
    "host": os.environ.get("LH_PGHOST", "127.0.0.1"),
    "port": os.environ.get("LH_PGPORT", "5432"),
    "dbname": os.environ.get("LH_PGDATABASE", "lh_nautical"),
    "user": os.environ.get("LH_PGUSER", "postgres"),
    "password": os.environ.get("LH_PGPASSWORD", "123456"),
}


def get_connection():
    return psycopg2.connect(**DB_CONFIG)
