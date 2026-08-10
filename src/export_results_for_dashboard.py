"""
Script de apoio (NAO e um dos 7 entregaveis do desafio) para gravar os
resultados de Q6 (previsao de demanda) e Q7 (recomendacao) de volta no
Postgres, como tabelas simples que o Power BI pode consumir diretamente
junto com as views de Q4/Q5.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from db import get_connection  # noqa: E402
from q6_forecast_bussola import (  # noqa: E402
    TEST_MONTHS,
    TRAIN_END,
    fetch_monthly_series,
    moving_average_baseline,
)
from q7_recommend_similar import (  # noqa: E402
    TARGET_PRODUCT_NAME,
    TOP_N,
    load_interaction_matrix,
)


def export_q6(conn):
    series = fetch_monthly_series(conn)
    rows = []
    for month in sorted(series):
        real = series[month]
        prevista = None
        if month in TEST_MONTHS:
            prevista, _ = moving_average_baseline(series, month)
        conjunto = "teste" if month in TEST_MONTHS else ("treino" if month <= TRAIN_END else "fora_do_periodo")
        rows.append((month, real, prevista, conjunto))

    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS q6_previsao_demanda")
        cur.execute(
            """
            CREATE TABLE q6_previsao_demanda (
                mes DATE PRIMARY KEY,
                quantidade_real NUMERIC NOT NULL,
                quantidade_prevista NUMERIC,
                conjunto TEXT NOT NULL
            )
            """
        )
        cur.executemany(
            "INSERT INTO q6_previsao_demanda (mes, quantidade_real, quantidade_prevista, conjunto) "
            "VALUES (%s, %s, %s, %s)",
            rows,
        )
    conn.commit()
    print("q6_previsao_demanda: {} linhas".format(len(rows)))


def export_q7(conn):
    import pandas as pd
    from sklearn.metrics.pairwise import cosine_similarity

    matrix, products = load_interaction_matrix()
    product_names = products.set_index("id")["name"]

    product_matrix = matrix.T
    similarity = cosine_similarity(product_matrix.values)
    sim_df = pd.DataFrame(similarity, index=product_matrix.index, columns=product_matrix.index)

    target_id = int(products.loc[products["name"] == TARGET_PRODUCT_NAME, "id"].iloc[0])
    sims = sim_df.loc[target_id].drop(index=target_id).sort_values(ascending=False).head(TOP_N)

    rows = []
    for rank, (pid, score) in enumerate(sims.items(), start=1):
        rows.append((target_id, TARGET_PRODUCT_NAME, int(pid), product_names.get(pid), float(score), rank))

    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS q7_recomendacoes")
        cur.execute(
            """
            CREATE TABLE q7_recomendacoes (
                produto_referencia_id INTEGER NOT NULL,
                produto_referencia_nome TEXT NOT NULL,
                produto_recomendado_id INTEGER NOT NULL,
                produto_recomendado_nome TEXT NOT NULL,
                similaridade NUMERIC NOT NULL,
                rank INTEGER NOT NULL
            )
            """
        )
        cur.executemany(
            "INSERT INTO q7_recomendacoes VALUES (%s, %s, %s, %s, %s, %s)",
            rows,
        )
    conn.commit()
    print("q7_recomendacoes: {} linhas".format(len(rows)))


def main():
    conn = get_connection()
    try:
        export_q6(conn)
        export_q7(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
