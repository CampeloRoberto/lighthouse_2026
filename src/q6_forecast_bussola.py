"""
Questao 6 - Previsao de demanda mensal para o produto "Bussola de Bordo 702".

Premissas obrigatorias do desafio:
- Treino ate 31/12/2025, teste = 1o trimestre de 2026 (jan/fev/mar).
- Previsao mensal.
- Baseline: media movel dos ultimos 3 meses, usando apenas dados anteriores
  a data prevista (walk-forward, sem olhar o futuro).

Nota de qualidade de dados encontrada ao localizar o produto: existem DOIS
product_id com o nome exatamente "Bussola de Bordo 702" (ids 74 e 240) no
catalogo - aparenta ser uma duplicidade de cadastro do gerador de dados. Como
o enunciado se refere ao produto pelo NOME (e e assim que o Sr. Almir/Marina
enxergariam o catalogo), a demanda dos dois product_id foi somada. Um terceiro
produto, "Bussola de Bordo 7024" (id 303), tem nome parecido mas e outro SKU -
foi excluido por nao ser correspondencia exata.
"""

import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(__file__))
from db import get_connection  # noqa: E402

PRODUCT_IDS = (74, 240)  # ambos chamados "Bussola de Bordo 702"
TRAIN_END = date(2025, 12, 31)
TEST_MONTHS = [date(2026, 1, 1), date(2026, 2, 1), date(2026, 3, 1)]

MONTHLY_SERIES_SQL = """
WITH meses AS (
    SELECT generate_series(
        (SELECT date_trunc('month', MIN(placed_at)) FROM orders)::date,
        %s::date,
        interval '1 month'
    )::date AS mes
),
vendas_mensais AS (
    SELECT date_trunc('month', o.placed_at)::date AS mes, SUM(oi.quantity) AS qtd
    FROM order_items oi
    JOIN orders o             ON o.id = oi.order_id
    JOIN product_variants pv  ON pv.id = oi.product_variant_id
    WHERE pv.product_id = ANY(%s)
    GROUP BY mes
)
SELECT m.mes, COALESCE(v.qtd, 0)::float AS quantidade
FROM meses m
LEFT JOIN vendas_mensais v ON v.mes = m.mes
ORDER BY m.mes;
"""


def fetch_monthly_series(conn):
    with conn.cursor() as cur:
        cur.execute(MONTHLY_SERIES_SQL, (TEST_MONTHS[-1], list(PRODUCT_IDS)))
        rows = cur.fetchall()
    return {row[0]: row[1] for row in rows}


def month_before(d, n):
    """Retorna a data (dia 1) n meses antes de d."""
    month_index = (d.year * 12 + (d.month - 1)) - n
    year, month = divmod(month_index, 12)
    return date(year, month + 1, 1)


def moving_average_baseline(series, target_month):
    """Media dos 3 meses imediatamente anteriores a target_month (dados ja realizados)."""
    window = [month_before(target_month, n) for n in (1, 2, 3)]
    values = [series[m] for m in window]
    return sum(values) / len(values), window


def main():
    conn = get_connection()
    try:
        series = fetch_monthly_series(conn)
    finally:
        conn.close()

    print("Serie mensal (ultimos 12 meses ate o fim do teste):")
    for m in sorted(series)[-12:]:
        marker = " <- treino" if m <= TRAIN_END else " <- teste"
        print("  {}  {:>6.0f}{}".format(m, series[m], marker))

    print("\nPrevisao (media movel de 3 meses, walk-forward):")
    predictions = {}
    errors = []
    for month in TEST_MONTHS:
        pred, window = moving_average_baseline(series, month)
        actual = series[month]
        error = abs(actual - pred)
        predictions[month] = pred
        errors.append(error)
        print(
            "  {} -> previsto {:.2f} (media de {}) | real {:.0f} | erro abs {:.2f}".format(
                month, pred, ", ".join(str(w) for w in window), actual, error
            )
        )

    mae = sum(errors) / len(errors)
    total_previsto = round(sum(predictions.values()))
    total_real = sum(series[m] for m in TEST_MONTHS)

    print("\nMAE (jan-mar/2026): {:.2f}".format(mae))
    print("Soma da previsao Q1/2026 (arredondada): {}".format(total_previsto))
    print("Soma real Q1/2026: {:.0f}".format(total_real))


if __name__ == "__main__":
    main()
