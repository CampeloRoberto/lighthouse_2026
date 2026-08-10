"""
Questao 3 - Carrega todos os CSVs no PostgreSQL, respeitando o schema da Questao 2.

Premissas obrigatorias do desafio:
- Carregar todos os CSVs.
- Python 3, qualquer biblioteca (usa psycopg2 para conexao/COPY).
- Sem tratamento: nao remove nulos, nao corrige caracteres especiais. A unica
  conversao aplicada e a de string vazia -> NULL, feita pelo proprio COPY do
  Postgres (opcao NULL ''), exigida porque colunas tipadas (INTEGER, DATE...)
  nao aceitam literalmente uma string vazia - isso e mecanica de carga, nao
  uma decisao analitica de limpeza.

Uso:
    python src/q3_load_data.py [diretorio_csvs] [schema.sql]
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from db import get_connection  # noqa: E402

TABLE_NAME_RE = re.compile(r'CREATE TABLE "([^"]+)"')


def table_names_in_schema(schema_sql):
    return TABLE_NAME_RE.findall(schema_sql)


def load_csv_into_table(cursor, table_name, csv_path):
    copy_sql = 'COPY "{}" FROM STDIN WITH (FORMAT csv, HEADER true, NULL \'\')'.format(table_name)
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        cursor.copy_expert(copy_sql, f)


def main(csv_dir="data/raw", schema_path="sql/q2_schema.sql"):
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    tables = table_names_in_schema(schema_sql)

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            print("Recriando {} tabelas a partir de {}...".format(len(tables), schema_path))
            for table in tables:
                cur.execute('DROP TABLE IF EXISTS "{}" CASCADE'.format(table))
            cur.execute(schema_sql)
        conn.commit()

        with conn.cursor() as cur:
            for table in tables:
                csv_path = os.path.join(csv_dir, table + ".csv")
                if not os.path.exists(csv_path):
                    print("  [aviso] {} nao encontrado, pulando".format(csv_path))
                    continue
                load_csv_into_table(cur, table, csv_path)
                cur.execute('SELECT COUNT(*) FROM "{}"'.format(table))
                count = cur.fetchone()[0]
                print("  {:<28} {:>8} linhas carregadas".format(table, count))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    print("Carga concluida.")


if __name__ == "__main__":
    csv_dir = sys.argv[1] if len(sys.argv) > 1 else "data/raw"
    schema_path = sys.argv[2] if len(sys.argv) > 2 else "sql/q2_schema.sql"
    main(csv_dir, schema_path)
