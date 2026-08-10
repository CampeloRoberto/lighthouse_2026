"""
Questao 2 - Gera um schema.sql (PostgreSQL) a partir dos CSVs de um diretorio.

Premissas obrigatorias do desafio:
- Considerar todos os CSVs como fonte.
- Python 3 puro, somente biblioteca padrao (csv, os, datetime, decimal...). Sem pandas/dask/polars.
- Banco de destino: PostgreSQL.

Uso:
    python src/q2_generate_schema.py [diretorio_csvs] [arquivo_saida.sql]

Padrao: le de "data/raw" e escreve em "sql/q2_schema.sql".

Decisao de projeto: o script infere apenas os TIPOS de coluna a partir dos valores
observados. Nao cria PRIMARY KEY nem FOREIGN KEY, pois a tarefa pede explicitamente
"uma tabela para cada CSV" com as colunas detectadas - nao um schema relacional
com integridade referencial (isso nao foi pedido, entao nao foi adicionado).
"""

import csv
import os
import sys
from datetime import datetime
from decimal import Decimal, InvalidOperation

BOOLEAN_VALUES = {"TRUE", "FALSE"}
TIMESTAMP_FORMATS = ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S")
DATE_FORMATS = ("%Y-%m-%d",)
BIGINT_MIN = -9223372036854775808
BIGINT_MAX = 9223372036854775807


class ColumnProfile:
    """Acumula, coluna a coluna, quais tipos ainda sao compativeis com os valores vistos."""

    def __init__(self):
        self.has_value = False
        self.has_empty = False
        self.is_boolean = True
        self.is_integer = True
        self.is_numeric = True
        self.is_date = True
        self.is_timestamp = True

    def observe(self, raw_value):
        value = raw_value.strip()
        if value == "":
            self.has_empty = True
            return
        self.has_value = True

        if self.is_boolean and value.upper() not in BOOLEAN_VALUES:
            self.is_boolean = False

        if self.is_integer:
            try:
                parsed = int(value)
                if not (BIGINT_MIN <= parsed <= BIGINT_MAX):
                    # cabe em Python (precisao arbitraria), mas estoura o BIGINT do
                    # Postgres (ex.: chave de acesso de NF-e, 44 digitos) - vira NUMERIC.
                    self.is_integer = False
            except ValueError:
                self.is_integer = False

        if self.is_numeric:
            try:
                Decimal(value)
            except InvalidOperation:
                self.is_numeric = False

        if self.is_date:
            if not _matches_any_format(value, DATE_FORMATS):
                self.is_date = False

        if self.is_timestamp:
            if not _matches_any_format(value, TIMESTAMP_FORMATS):
                self.is_timestamp = False

    def sql_type(self):
        if not self.has_value:
            return "TEXT"
        if self.is_boolean:
            return "BOOLEAN"
        if self.is_integer:
            return "BIGINT"
        if self.is_numeric:
            return "NUMERIC"
        if self.is_date:
            return "DATE"
        if self.is_timestamp:
            return "TIMESTAMP"
        return "TEXT"

    def is_nullable(self):
        return self.has_empty or not self.has_value


def _matches_any_format(value, formats):
    for fmt in formats:
        try:
            datetime.strptime(value, fmt)
            return True
        except ValueError:
            continue
    return False


def profile_csv(path):
    """Le um CSV inteiro e devolve (lista_de_colunas, dict coluna -> ColumnProfile)."""
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            return [], {}

        profiles = {col: ColumnProfile() for col in header}
        for row in reader:
            # linhas mal formadas (numero de campos diferente do cabecalho) sao
            # ignoradas na INFERENCIA de tipo, mas isso nao e "limpeza" do dado
            # em si - o CSV original nao e alterado em nenhum momento.
            if len(row) != len(header):
                continue
            for col, value in zip(header, row):
                profiles[col].observe(value)

    return header, profiles


def table_name_from_filename(filename):
    return os.path.splitext(filename)[0]


def quote_identifier(name):
    return '"{}"'.format(name.replace('"', '""'))


def build_create_table(table_name, header, profiles):
    lines = []
    for col in header:
        profile = profiles[col]
        col_type = profile.sql_type()
        nullability = "" if profile.is_nullable() else " NOT NULL"
        lines.append("    {} {}{}".format(quote_identifier(col), col_type, nullability))

    body = ",\n".join(lines)
    return "CREATE TABLE {} (\n{}\n);".format(quote_identifier(table_name), body)


def generate_schema(csv_dir, output_path):
    csv_files = sorted(f for f in os.listdir(csv_dir) if f.lower().endswith(".csv"))
    if not csv_files:
        raise SystemExit("Nenhum CSV encontrado em {}".format(csv_dir))

    statements = [
        "-- Schema gerado automaticamente por src/q2_generate_schema.py",
        "-- Tipos inferidos a partir dos valores observados em cada CSV (ver logica em ColumnProfile).",
        "-- Sem PRIMARY KEY / FOREIGN KEY: nao foram pedidos pela tarefa, apenas a criacao das tabelas.",
        "",
    ]

    for filename in csv_files:
        path = os.path.join(csv_dir, filename)
        header, profiles = profile_csv(path)
        if not header:
            continue
        table_name = table_name_from_filename(filename)
        statements.append(build_create_table(table_name, header, profiles))
        statements.append("")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(statements))

    print("Schema gerado: {} ({} tabelas)".format(output_path, len(csv_files)))


if __name__ == "__main__":
    csv_dir = sys.argv[1] if len(sys.argv) > 1 else "data/raw"
    output_path = sys.argv[2] if len(sys.argv) > 2 else "sql/q2_schema.sql"
    generate_schema(csv_dir, output_path)
