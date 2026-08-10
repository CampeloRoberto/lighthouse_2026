-- Questão 1 — EDA da tabela "orders"
-- Premissas: usar apenas a tabela orders, sem nenhuma limpeza/tratamento, apenas observar/agregar/descrever.
-- Executado com DuckDB lendo orders.csv diretamente (nenhum banco/infra criada ainda nesta etapa do desafio).

-- Parte 1: quantidade de linhas e intervalo de datas (created_at)
SELECT
    COUNT(*)                       AS qtd_linhas,
    MIN(created_at)                AS data_min,
    MAX(created_at)                AS data_max
FROM read_csv_auto('data/raw/orders.csv');

-- Quantidade de colunas (introspecção do schema, não é uma agregação de linhas)
SELECT COUNT(*) AS qtd_colunas
FROM (DESCRIBE SELECT * FROM read_csv_auto('data/raw/orders.csv'));

-- Parte 2: valores mínimo, máximo e médio da coluna "total"
SELECT
    MIN(total) AS total_min,
    MAX(total) AS total_max,
    AVG(total) AS total_medio
FROM read_csv_auto('data/raw/orders.csv');
