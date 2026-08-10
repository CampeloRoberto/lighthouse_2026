-- Questao 4 - Clientes fieis (ticket medio alto + diversidade de categorias)
-- Cadeia de chaves: orders.customer_id -> order_items.order_id -> order_items.product_variant_id
--                    -> product_variants.product_id -> products.category_id -> categories.id
-- Premissas: faturamento = SUM(orders.total) por cliente; frequencia = COUNT(orders.id) por cliente;
-- ticket medio = faturamento/frequencia; diversidade = COUNT(DISTINCT category_id) via a cadeia acima;
-- filtro de elite = diversidade >= 13; desempate no ticket medio por customer_id ASC.

-- 1) Metricas por cliente (todos os clientes, sem filtro ainda)
DROP VIEW IF EXISTS v_q4_metricas_cliente CASCADE;
CREATE VIEW v_q4_metricas_cliente AS
WITH pedidos_cliente AS (
    SELECT
        customer_id,
        COUNT(*)   AS frequencia,
        SUM(total) AS faturamento_total
    FROM orders
    GROUP BY customer_id
),
categorias_cliente AS (
    SELECT
        o.customer_id,
        COUNT(DISTINCT p.category_id) AS diversidade_categorias
    FROM orders o
    JOIN order_items oi      ON oi.order_id = o.id
    JOIN product_variants pv ON pv.id = oi.product_variant_id
    JOIN products p          ON p.id = pv.product_id
    GROUP BY o.customer_id
)
SELECT
    pc.customer_id,
    pc.frequencia,
    pc.faturamento_total,
    pc.faturamento_total / pc.frequencia AS ticket_medio,
    cc.diversidade_categorias
FROM pedidos_cliente pc
JOIN categorias_cliente cc ON cc.customer_id = pc.customer_id;

-- 2) Filtro de elite (diversidade >= 13) + top 10 por ticket medio, desempate por customer_id ASC
DROP VIEW IF EXISTS v_q4_clientes_fieis CASCADE;
CREATE VIEW v_q4_clientes_fieis AS
SELECT *
FROM v_q4_metricas_cliente
WHERE diversidade_categorias >= 13
ORDER BY ticket_medio DESC, customer_id ASC
LIMIT 10;

SELECT * FROM v_q4_clientes_fieis;

-- 3) Dentro desse grupo de 10, a categoria que concentra mais itens comprados (SUM(quantity))
SELECT
    p.category_id,
    c.name AS category_name,
    SUM(oi.quantity) AS quantidade_total
FROM v_q4_clientes_fieis cf
JOIN orders o             ON o.customer_id = cf.customer_id
JOIN order_items oi       ON oi.order_id = o.id
JOIN product_variants pv  ON pv.id = oi.product_variant_id
JOIN products p           ON p.id = pv.product_id
JOIN categories c         ON c.id = p.category_id
GROUP BY p.category_id, c.name
ORDER BY quantidade_total DESC
LIMIT 1;
