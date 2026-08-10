"""
Questao 7 - Sistema de recomendacao por similaridade de cosseno.

Premissas obrigatorias do desafio:
- Matriz usuario (customer_id) x produto (product_id), valor = 1 se o cliente
  ja comprou o produto ao menos uma vez, 0 caso contrario (ignora quantidade).
- Similaridade de cosseno produto x produto.
- Ranking dos 5 produtos mais similares a "Motor de Popa 1949", excluindo ele mesmo.
- Bibliotecas permitidas: pandas, numpy, sklearn (opcional). Por isso este script
  le os CSVs originais diretamente com pandas, sem passar pelo Postgres.

A interacao e agregada em nivel de PRODUTO (nao de variante/SKU): o alvo
"Motor de Popa 1949" e um nome de produto em products.csv, entao um cliente
que comprou qualquer variante daquele produto conta como interacao com o
produto como um todo (product_variants.product_id).
"""

import os

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
TARGET_PRODUCT_NAME = "Motor de Popa 1949"
TOP_N = 5


def load_interaction_matrix():
    products = pd.read_csv(os.path.join(DATA_DIR, "products.csv"))
    variants = pd.read_csv(os.path.join(DATA_DIR, "product_variants.csv"))
    order_items = pd.read_csv(os.path.join(DATA_DIR, "order_items.csv"))
    orders = pd.read_csv(os.path.join(DATA_DIR, "orders.csv"))

    items_with_product = order_items.merge(
        variants[["id", "product_id"]],
        left_on="product_variant_id",
        right_on="id",
        suffixes=("", "_variant"),
    )
    items_with_customer = items_with_product.merge(
        orders[["id", "customer_id"]],
        left_on="order_id",
        right_on="id",
        suffixes=("", "_order"),
    )

    pairs = items_with_customer[["customer_id", "product_id"]].drop_duplicates()

    matrix = pd.crosstab(pairs["customer_id"], pairs["product_id"])
    matrix = (matrix > 0).astype(int)  # garante binario (presenca/ausencia), ignora quantidade

    return matrix, products


def main():
    matrix, products = load_interaction_matrix()
    product_names = products.set_index("id")["name"]

    product_matrix = matrix.T  # linhas = produtos, colunas = clientes
    similarity = cosine_similarity(product_matrix.values)
    sim_df = pd.DataFrame(similarity, index=product_matrix.index, columns=product_matrix.index)

    target_id = products.loc[products["name"] == TARGET_PRODUCT_NAME, "id"]
    if target_id.empty:
        raise SystemExit("Produto '{}' nao encontrado".format(TARGET_PRODUCT_NAME))
    target_id = int(target_id.iloc[0])

    sims = sim_df.loc[target_id].drop(index=target_id).sort_values(ascending=False)
    top5 = sims.head(TOP_N)

    print("Produto de referencia: {} (id={})".format(TARGET_PRODUCT_NAME, target_id))
    print("\nTop {} produtos mais similares (similaridade de cosseno):".format(TOP_N))
    for pid, score in top5.items():
        print("  {:<35} (id={:>4})  similaridade={:.4f}".format(product_names.get(pid, "?"), pid, score))

    print("\nMatriz de interacao: {} clientes x {} produtos".format(matrix.shape[0], matrix.shape[1]))


if __name__ == "__main__":
    main()
