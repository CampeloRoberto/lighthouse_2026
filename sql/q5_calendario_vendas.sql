-- Questao 5 - Dimensao de calendario + vendas medias por dia da semana (lojas fisicas)
-- Premissas: periodo = MIN a MAX de orders.placed_at ("data da venda") presentes no arquivo;
-- loja considerada aberta todos os dias do periodo; somente canal = 'pos' (lojas fisicas);
-- dias sem pedido = venda R$ 0,00; media por dia da semana considera TODOS os dias do
-- calendario, inclusive os sem venda; nomes dos dias em portugues.

DROP VIEW IF EXISTS v_q5_calendario_vendas CASCADE;
CREATE VIEW v_q5_calendario_vendas AS
WITH calendario AS (
    SELECT generate_series(
        (SELECT MIN(placed_at)::date FROM orders),
        (SELECT MAX(placed_at)::date FROM orders),
        interval '1 day'
    )::date AS data
),
vendas_diarias_pos AS (
    -- agregacao de vendas por dia (soma de valor_venda), somente lojas fisicas
    SELECT placed_at::date AS data, SUM(total) AS valor_venda
    FROM orders
    WHERE channel = 'pos'
    GROUP BY placed_at::date
)
SELECT
    c.data,
    EXTRACT(ISODOW FROM c.data)::int AS dow,           -- 1=Segunda ... 7=Domingo (evita depender de locale do servidor)
    CASE EXTRACT(ISODOW FROM c.data)
        WHEN 1 THEN 'Segunda-feira'
        WHEN 2 THEN 'Terça-feira'
        WHEN 3 THEN 'Quarta-feira'
        WHEN 4 THEN 'Quinta-feira'
        WHEN 5 THEN 'Sexta-feira'
        WHEN 6 THEN 'Sábado'
        WHEN 7 THEN 'Domingo'
    END AS dia_semana,
    COALESCE(v.valor_venda, 0) AS valor_venda          -- substitui NULL (dia sem venda) por zero
FROM calendario c
LEFT JOIN vendas_diarias_pos v ON v.data = c.data;

-- Media de vendas por dia da semana, considerando TODOS os dias do calendario (inclusive sem venda)
SELECT
    dow,
    dia_semana,
    COUNT(*)          AS qtd_dias_no_calendario,
    SUM(valor_venda)  AS soma_vendas,
    AVG(valor_venda)  AS media_vendas_correta
FROM v_q5_calendario_vendas
GROUP BY dow, dia_semana
ORDER BY dow;

-- Apoio para a Questao 5.2 (comparacao): a media "ingenua" do estagiario, que so
-- agrupa orders/pos direto (sem calendario) e por isso ignora silenciosamente os
-- dias sem nenhum pedido.
WITH vendas_diarias_pos AS (
    SELECT placed_at::date AS data, SUM(total) AS valor_venda
    FROM orders
    WHERE channel = 'pos'
    GROUP BY placed_at::date
)
SELECT
    EXTRACT(ISODOW FROM data)::int AS dow,
    CASE EXTRACT(ISODOW FROM data)
        WHEN 1 THEN 'Segunda-feira' WHEN 2 THEN 'Terça-feira' WHEN 3 THEN 'Quarta-feira'
        WHEN 4 THEN 'Quinta-feira' WHEN 5 THEN 'Sexta-feira' WHEN 6 THEN 'Sábado' WHEN 7 THEN 'Domingo'
    END AS dia_semana,
    COUNT(*)         AS dias_com_venda,
    AVG(valor_venda) AS media_vendas_ingenua
FROM vendas_diarias_pos
GROUP BY dow, dia_semana
ORDER BY dow;
