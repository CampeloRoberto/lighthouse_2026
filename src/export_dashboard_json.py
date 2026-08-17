"""
Exporta os resultados das questoes do desafio como JSON estatico, para o
dashboard web em docs/ (GitHub Pages nao serve nada dinamico, so arquivos).

Nao e um dos 7 entregaveis do desafio - e a ponte entre o Postgres (onde
Q1/Q4/Q5/Q6/Q7 ja foram calculadas e validadas) e a pagina estatica.
"""

import json
import os
import sys
from datetime import date, datetime
from decimal import Decimal

sys.path.insert(0, os.path.dirname(__file__))
from db import get_connection  # noqa: E402

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "docs", "data")

Q1_SQL = """
SELECT
    (SELECT COUNT(*) FROM orders) AS total_pedidos,
    13 AS total_colunas,
    (SELECT MIN(created_at) FROM orders) AS data_min,
    (SELECT MAX(created_at) FROM orders) AS data_max,
    (SELECT MIN(total) FROM orders) AS total_min,
    (SELECT MAX(total) FROM orders) AS total_max,
    (SELECT AVG(total) FROM orders) AS total_medio
"""

Q1_STATUS_SQL = """
SELECT status, COUNT(*) AS quantidade
FROM orders
GROUP BY status
ORDER BY quantidade DESC
"""

Q4_SQL = "SELECT * FROM v_q4_clientes_fieis ORDER BY ticket_medio DESC, customer_id ASC"

Q4_TOP_CATEGORY_SQL = """
SELECT p.category_id, c.name AS category_name, SUM(oi.quantity) AS quantidade_total
FROM v_q4_clientes_fieis cf
JOIN orders o             ON o.customer_id = cf.customer_id
JOIN order_items oi       ON oi.order_id = o.id
JOIN product_variants pv  ON pv.id = oi.product_variant_id
JOIN products p           ON p.id = pv.product_id
JOIN categories c         ON c.id = p.category_id
GROUP BY p.category_id, c.name
ORDER BY quantidade_total DESC
LIMIT 1
"""

Q5_SQL = """
SELECT dow, dia_semana, COUNT(*) AS qtd_dias_no_calendario,
       SUM(valor_venda) AS soma_vendas, AVG(valor_venda) AS media_vendas
FROM v_q5_calendario_vendas
GROUP BY dow, dia_semana
ORDER BY dow
"""

Q6_SQL = "SELECT mes, quantidade_real, quantidade_prevista, conjunto FROM q6_previsao_demanda ORDER BY mes"

Q7_SQL = """
SELECT produto_referencia_nome, produto_recomendado_nome, similaridade, rank
FROM q7_recomendacoes
ORDER BY rank
"""


def rows_as_dicts(cur):
    columns = [c.name for c in cur.description]
    return [dict(zip(columns, row)) for row in cur.fetchall()]


def json_default(obj):
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError("Tipo nao serializavel: {}".format(type(obj)))


def write_json(filename, data):
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=json_default)
    print("  {} escrito ({} objeto(s) de topo)".format(filename, len(data) if isinstance(data, list) else 1))


def main():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(Q1_SQL)
            q1 = rows_as_dicts(cur)[0]
            cur.execute(Q1_STATUS_SQL)
            q1["status_breakdown"] = rows_as_dicts(cur)
            write_json("q1_diagnostico.json", q1)

            cur.execute(Q4_SQL)
            clientes = rows_as_dicts(cur)
            cur.execute(Q4_TOP_CATEGORY_SQL)
            top_categoria = rows_as_dicts(cur)[0]
            write_json("q4_clientes_fieis.json", {"clientes": clientes, "categoria_top": top_categoria})

            cur.execute(Q5_SQL)
            write_json("q5_vendas_dia_semana.json", rows_as_dicts(cur))

            cur.execute(Q6_SQL)
            write_json("q6_previsao_demanda.json", rows_as_dicts(cur))

            cur.execute(Q7_SQL)
            write_json("q7_recomendacoes.json", rows_as_dicts(cur))
    finally:
        conn.close()

    print("Exportacao concluida em {}".format(os.path.abspath(OUT_DIR)))


if __name__ == "__main__":
    main()
