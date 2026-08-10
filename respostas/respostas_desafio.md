# Respostas — Desafio de Dados LH Nautical

> Cada questão traz: o código/artefato entregável (referenciado por caminho), a validação numérica pedida e a explicação em linguagem de negócio, incluindo as premissas assumidas quando o enunciado deixava algo em aberto.

## Questão 1 — EDA da tabela `orders`

**Código**: [`sql/q1_eda_orders.sql`](../sql/q1_eda_orders.sql) — executado com DuckDB lendo `orders.csv` diretamente (nenhuma limpeza aplicada, apenas leitura/agregação, conforme a premissa obrigatória).

### Parte 1 — Visão geral
- Quantidade total de linhas: **48.998**
- Quantidade total de colunas: **13**
- Intervalo de datas (`created_at`): **2020-01-01** a **2026-12-31**

### Parte 2 — Coluna `total`
- Valor mínimo: **R$ 32,62**
- Valor máximo: **R$ 127.262,02**
- Valor médio: **R$ 28.704,99**

### Questão 1.2 — Validação
Valor médio registrado em `total`: **R$ 28.704,99**.

### Questão 1.3 — Interpretação
**Diagnóstico: os dados são utilizáveis, mas não estão prontos para virar métrica de negócio sem tratamento/relacionamento com outras tabelas.**

- **Outliers em `total`**: a distribuição é larga (desvio padrão ≈ R$ 19.426, mediana ≈ R$ 25.933, p99 ≈ R$ 81.912) e o valor máximo (R$ 127.262) fica só ~1,55× acima do p99 — não há um outlier absurdo isolado, é uma cauda longa plausível para um varejo que atende tanto PF (compras pequenas) quanto PJ/frota (compras grandes, ex. motores de popa). Não classificaria isso como erro de dado sem cruzar com `order_items`/`customers.person_type`.
- **Qualidade dos dados**: não há valores nulos em `order_number`, `customer_id`, `status` ou `total`. Já `salesperson_id` está nulo em 24.131 das 48.998 linhas (~49%) — parcialmente explicado pelo canal `ecommerce` (pedidos sem vendedor), mas não totalmente (nem todo pedido ecommerce está nulo, nem todo nulo é ecommerce), o que precisa ser investigado antes de qualquer análise por vendedor.
- **`status` está misturado**: 34.365 pedidos `paid`, mas também 7.335 `confirmed`, 4.847 `cancelled` e 2.451 `draft` somados na mesma tabela. A média de `total` fica parecida entre os status (~R$ 28k–29k em todos), então o valor médio calculado acima **não está estatisticamente distorcido por isso** — mas ele **está conceitualmente errado como "receita"**, porque inclui pedidos cancelados e rascunhos que nunca viraram venda.
- **Conclusão**: a tabela `orders` isolada é confiável para uma leitura operacional (volume de pedidos, ticket médio geral), mas **não deve ser usada como fonte de receita/faturamento sem filtrar por `status`** e, para qualquer análise de produto/categoria/margem, precisa ser relacionada com `order_items`, `product_variants` e `payments`/`fiscal_invoices` — que é exatamente o caminho que o desafio segue nas próximas questões.

## Questão 2 — Geração do schema PostgreSQL

**Código**: [`src/q2_generate_schema.py`](../src/q2_generate_schema.py) — Python 3 puro, só biblioteca padrão (`csv`, `os`, `datetime`, `decimal`). Validado rodando com o interpretador Python "limpo" (fora do venv do projeto, sem nenhum pacote de terceiros instalado) para garantir que não há nenhuma dependência externa.

**Entrega**: [`sql/q2_schema.sql`](../sql/q2_schema.sql) — 24 `CREATE TABLE`, um por CSV.

Lógica de inferência: para cada coluna, o script testa (em cascata, por valor) se ela é compatível com `BOOLEAN` → `BIGINT` → `NUMERIC` → `DATE` → `TIMESTAMP`, e cai em `TEXT` caso nenhum desses tipos sirva para todos os valores observados (ou se a coluna estiver sempre vazia, como `stock_levels.reorder_point`). Coluna com pelo menos um valor vazio vira nullable; sem nenhum valor vazio, `NOT NULL`. Não foram criadas `PRIMARY KEY`/`FOREIGN KEY` — a tarefa pede a criação de uma tabela por CSV com as colunas detectadas, não um modelo relacional com integridade referencial, e evitei adicionar uma regra de negócio não solicitada.

Um ajuste que precisou entrar durante a validação: `fiscal_invoices.nfe_access_key` tem 44 dígitos (chave de acesso de NF-e) — cabe como inteiro em Python (que não tem limite de tamanho), mas estoura o `BIGINT` do Postgres (limite de ~19 dígitos). O script checa explicitamente se o inteiro cabe no intervalo do `BIGINT` antes de classificar a coluna como tal; se não couber, ela é reclassificada como `NUMERIC` (que aceita inteiros arbitrariamente grandes). Isso foi pego rodando o `CREATE TABLE` de verdade contra o Postgres, não só lendo o CSV.

**Questão 2.1**: script em `src/q2_generate_schema.py` (acima).
**Questão 2.2**: arquivo em `sql/q2_schema.sql` (acima).

## Questão 3 — Carga dos dados no PostgreSQL

**Código**: [`src/q3_load_data.py`](../src/q3_load_data.py) — Python 3 + `psycopg2`. Recria as 24 tabelas a partir de `sql/q2_schema.sql` (idempotente: pode ser rodado várias vezes) e carrega cada CSV com `COPY "<tabela>" FROM STDIN WITH (FORMAT csv, HEADER true, NULL '')`. A única conversão aplicada é string vazia → `NULL`, exigida pelo próprio tipo de cada coluna (uma coluna `BIGINT`/`DATE` não aceita `''` literal) — isso é mecânica de carga do `COPY`, não uma decisão de limpeza (nenhum valor foi removido, corrigido ou reinterpretado).

### Questão 3.1
Script em `src/q3_load_data.py` (acima).

### Questão 3.2 — Validação
Soma de linhas de `customers + orders + order_items + payments`: **251.864** (2.000 + 48.998 + 147.320 + 53.546), confirmada com `SELECT COUNT(*)` direto no banco após a carga — bate exatamente com as linhas dos CSVs originais (nenhuma linha perdida ou duplicada na carga).

## Questão 4 — Clientes fiéis

**Código**: [`sql/q4_clientes_fieis.sql`](../sql/q4_clientes_fieis.sql) — cria as views `v_q4_metricas_cliente` (métricas de todos os clientes) e `v_q4_clientes_fieis` (top 10 filtrados), reutilizáveis depois no Power BI.

**Nota sobre premissa não especificada**: a questão não pede filtro por `orders.status`, então a query usa a tabela `orders` como carregada (inclui `draft`/`cancelled`), sem excluir nada — documentando aqui essa escolha explicitamente, para não injetar uma regra de negócio (ex.: "só pedidos pagos") que não foi solicitada.

**Resultado — Top 10 clientes fiéis** (diversidade ≥ 13 categorias, ordenado por ticket médio desc, empate por `customer_id` asc):

| customer_id | frequência | faturamento total | ticket médio | diversidade |
|---|---|---|---|---|
| 22 | 26 | 1.087.838,44 | 41.839,94 | 14 |
| 1477 | 22 | 916.262,58 | 41.648,30 | 14 |
| 929 | 26 | 1.082.775,89 | 41.645,23 | 14 |
| 1116 | 16 | 655.737,20 | 40.983,58 | 14 |
| 1691 | 20 | 815.471,30 | 40.773,57 | 14 |
| 774 | 18 | 726.127,99 | 40.340,44 | 14 |
| 1470 | 26 | 1.040.553,09 | 40.021,27 | 14 |
| 1599 | 25 | 997.616,46 | 39.904,66 | 14 |
| 965 | 17 | 677.297,78 | 39.841,05 | 14 |
| 1722 | 29 | 1.146.455,22 | 39.532,94 | 14 |

Curiosidade: o catálogo tem só **14 categorias no total** (`categories.csv`), então "diversidade ≥ 13" já é um filtro extremo — na prática, todos os 10 clientes retornados compraram de **todas as 14 categorias existentes**.

Categoria que mais concentra itens comprados (`SUM(quantity)`) entre esses 10 clientes: **Hélices** (category_id 8), com **492 unidades**.

### Questão 4.2 — Explicação
- **Mapeamento da cadeia de chaves**: `orders.customer_id` identifica o cliente; `order_items.order_id` liga o item ao pedido; `order_items.product_variant_id` liga ao SKU; `product_variants.product_id` liga ao produto; `products.category_id` liga à categoria. É essa cadeia de 4 joins que permite contar categorias distintas por cliente e, depois, somar quantidade por categoria.
- **Lógica de filtro de diversidade mínima**: `COUNT(DISTINCT p.category_id)` agrupado por cliente, depois `WHERE diversidade_categorias >= 13` sobre essa métrica já calculada (feito em uma CTE/view separada para não misturar a agregação de diversidade com a de faturamento/frequência, que vêm de uma granularidade diferente — `orders` vs. `order_items`).
- **Garantia de que a contagem de itens reflete só os Top 10**: a segunda consulta faz `JOIN` de `orders`/`order_items` partindo da view `v_q4_clientes_fieis` (que já contém exatamente os 10 clientes filtrados/ordenados/limitados) — ou seja, o `SUM(quantity)` só enxerga pedidos desses 10 `customer_id`, nunca da base inteira.

## Questão 5 — Dimensão de calendário e vendas por dia da semana

**Código**: [`sql/q5_calendario_vendas.sql`](../sql/q5_calendario_vendas.sql) — cria a view `v_q5_calendario_vendas` (calendário completo × vendas diárias das lojas físicas, com zero nos dias sem venda) e roda a agregação por dia da semana.

**Premissas assumidas e documentadas** (o enunciado deixava em aberto):
- Período do calendário: `MIN`/`MAX` de `orders.placed_at` ("data da venda") **presentes no arquivo** — interpretei "data atual da venda presentes no arquivo" como a data mais recente do dataset, não a data de hoje do sistema (não faria sentido gerar calendário até 2026-08-10 se o dataset vai até 2026-12-31).
- "Valor da venda" = `orders.total`; "lojas físicas" = `orders.channel = 'pos'`.
- Nome do dia da semana calculado com `EXTRACT(ISODOW ...)` + `CASE`, para não depender do locale configurado no servidor Postgres.

**Resultado — média de vendas por dia da semana (todos os dias do calendário, incl. sem venda)**:

| Dia da semana | Dias no calendário | Soma de vendas | Média correta |
|---|---|---|---|
| Segunda-feira | 365 | 57.758.021,43 | **158.241,15** |
| Terça-feira | 365 | 60.633.373,26 | 166.118,83 |
| Quarta-feira | 366 | 63.539.589,22 | **173.605,44** (melhor dia) |
| Quinta-feira | 366 | 57.518.480,61 | **157.154,32** (pior dia) |
| Sexta-feira | 365 | 62.120.694,25 | 170.193,68 |
| Sábado | 365 | 60.173.268,58 | 164.858,27 |
| Domingo | 365 | 57.529.887,95 | 157.616,13 |

O **pior dia da semana é quinta-feira** (R$ 157.154,32 em média), praticamente empatado com domingo (R$ 157.616,13) e segunda (R$ 158.241,15) — os três ficam a menos de 1% de diferença entre si. O melhor dia é quarta-feira.

Para comparação, a query final do arquivo reproduz o erro do estagiário (média só sobre dias com pedido, sem calendário): o resultado fica sistematicamente **mais alto** em todos os dias da semana (ex.: quinta-feira sobe de R$ 157.154 para R$ 166.238 — uma inflação de ~5,8%, porque só 346 das 366 quintas-feiras do período tiveram alguma venda registrada).

### Questão 5.2 — Explicação
- **Por que usar uma tabela de calendário em vez de agrupar direto**: agrupar direto em `orders` só enxerga os dias em que *existiu* pelo menos um pedido — dias com venda zero simplesmente não aparecem na tabela, e portanto não entram no denominador da média (`COUNT`) nem no numerador (`SUM`). O calendário garante um "spine" com todas as datas do período, para que o `LEFT JOIN` force esses dias a aparecerem com `COALESCE(valor_venda, 0)`.
- **O que aconteceria com a média sem calendário**: ela fica artificialmente mais alta quanto mais dias sem venda aquele dia da semana tiver — é exatamente o erro do estagiário. No nosso caso a distorção foi de ~2% a ~6% dependendo do dia (quinta-feira, com mais dias sem venda proporcionalmente, foi o mais afetado), mas em um cenário com mais dias parados (ex.: loja fechando aos domingos por um período) a distorção seria muito maior — poderia até inverter o ranking de "pior dia".

## Questão 6 — Previsão de demanda (Bússola de Bordo 702)

**Código**: [`src/q6_forecast_bussola.py`](../src/q6_forecast_bussola.py) — monta a série mensal via SQL (com spine de meses, garantindo que meses sem venda entrem como zero, não fiquem ausentes) e calcula o baseline em Python puro.

**Achado de qualidade de dados**: existem **dois `product_id` (74 e 240)** com o nome exatamente "Bússola de Bordo 702" no catálogo — aparenta ser uma duplicidade de cadastro. Como o enunciado se refere ao produto pelo **nome** (é assim que Marina/Sr. Almir enxergam o catálogo, não por ID interno), a demanda dos dois `product_id` foi somada. Um terceiro produto parecido, "Bússola de Bordo 7024" (id 303), foi excluído por não ser correspondência exata de nome.

**Série mensal (últimos meses de treino + teste)**:

| Mês | Quantidade | Conjunto |
|---|---|---|
| 2025-10 | 34 | treino |
| 2025-11 | 60 | treino |
| 2025-12 | 22 | treino |
| 2026-01 | 79 | teste |
| 2026-02 | 68 | teste |
| 2026-03 | 60 | teste |

**Previsão walk-forward (média móvel de 3 meses)**:

| Mês previsto | Janela usada | Previsto | Real | Erro absoluto |
|---|---|---|---|---|
| 2026-01 | out/nov/dez-2025 | 38,67 | 79 | 40,33 |
| 2026-02 | nov/dez-2025, jan-2026 | 53,67 | 68 | 14,33 |
| 2026-03 | dez-2025, jan/fev-2026 | 56,33 | 60 | 3,67 |

### Questão 6.2 — Validação
Soma da previsão para o 1º trimestre de 2026 (arredondada): **149 unidades** (real: 207 unidades). **MAE = 19,44**.

### Questão 6.3 — Explicação
- **Como o baseline foi construído**: para cada mês do teste, a previsão é a média aritmética simples da quantidade vendida nos 3 meses imediatamente anteriores àquele mês específico (não uma janela fixa de out/nov/dez para os três meses de teste).
- **Como evitou data leakage**: a previsão de fevereiro/2026 usa o valor **já realizado** de janeiro/2026 (que nesse ponto já é passado), e a de março/2026 usa janeiro e fevereiro já realizados — é um esquema *walk-forward*: em nenhum momento a previsão de um mês usa dados de um mês posterior a ele. A única informação usada em cada previsão é o que já teria acontecido até aquele ponto do calendário.
- **O baseline é adequado?** Parcialmente. Ele funciona bem quando a demanda é relativamente estável (erro caiu de 40,33 em janeiro para 3,67 em março, à medida que a média "aprendia" com os meses de alta recém-realizados). Mas ele **reage com atraso a uma mudança brusca de patamar**: a demanda saltou de ~22-34/mês no fim de 2025 para quase o dobro (79) em janeiro/2026, e o baseline — que só olha para trás — não tinha como antecipar esse salto, errando por 40 unidades no primeiro mês. Isso é literalmente o problema que tirou o sono do Sr. Almir com os coletes salva-vidas no verão: uma média móvel simples estrutural nunca vai prever a *virada* de uma temporada, só reage a ela depois que já aconteceu.
- **Limitação**: o método não captura sazonalidade (ex.: pico de verão) nem tendência — ele assume implicitamente que o próximo mês parece com a média recente, o que falha justamente nos períodos de maior risco de ruptura de estoque. Um próximo passo razoável seria um modelo com componente sazonal explícito (ex.: Holt-Winters) ou ao menos comparar o mesmo mês do ano anterior.

## Questão 7 — Sistema de recomendação (similaridade com "Motor de Popa 1949")

**Código**: [`src/q7_recommend_similar.py`](../src/q7_recommend_similar.py) — usa só `pandas`, `numpy` e `sklearn` (conforme a lista de bibliotecas permitidas), lendo os CSVs originais diretamente (sem passar pelo Postgres, para não depender de nenhuma biblioteca de conexão fora da lista permitida).

**Resultado — Top 5 produtos mais similares ao "Motor de Popa 1949"**:

| Produto | Similaridade de cosseno |
|---|---|
| Motor de Popa 5331 | 0,2566 |
| Cabo Náutico 2105 | 0,2562 |
| Vela Mestra 1913 | 0,2558 |
| Cabo Náutico 9048 | 0,2393 |
| GPS Plotter 6249 | 0,2377 |

Matriz de interação: 2.000 clientes × 500 produtos.

### Questão 7.2 — Validação
Produto com maior similaridade ao "Motor de Popa 1949": **Motor de Popa 5331** (similaridade ≈ 0,2566).

### Questão 7.3 — Explicação
- **Como a matriz foi construída**: a partir de `order_items` (item comprado) → `product_variants` (SKU → produto) → `orders` (pedido → cliente), gerando pares únicos `(customer_id, product_id)` — a quantidade comprada é descartada de propósito, a célula é `1` se o cliente já comprou o produto alguma vez e `0` caso contrário (`pd.crosstab` seguido de binarização).
- **O que significa a similaridade de cosseno aqui**: cada produto vira um vetor de 2.000 posições (uma por cliente), com 1 nos clientes que já o compraram. O cosseno entre dois vetores de produto mede o quanto os *conjuntos de clientes* que compraram cada um se sobrepõem, normalizado pelo tamanho de cada conjunto — dois produtos comprados quase sempre pelos mesmos clientes têm similaridade próxima de 1; produtos com bases de clientes totalmente distintas, próxima de 0. Não é sobre o produto em si (categoria, preço), é 100% sobre comportamento de compra.
- **Limitação**: como a matriz é binária e ignora quantidade/recência, um cliente que comprou o produto uma vez há 6 anos pesa exatamente igual a um que compra toda semana — e como a base tem só 2.000 clientes e 500 produtos, produtos de nicho com poucos compradores tendem a ter similaridades baixas e instáveis (poucas coincidências de clientes já mudam bastante o cosseno). Também não usa nenhuma informação de catálogo (categoria, marca) — a recomendação pode "acertar por coincidência" sem capturar complementaridade real de uso (o cenário da Marina era justamente sobre isso: lancha + defensa, itens de categorias diferentes usados juntos).

## Questões 18 e 19

O texto exato dessas duas questões (reflexão sobre o processo, ex. "qual foi a questão mais difícil") não foi incluído no enunciado que recebi — só as questões 1 a 7 com suas premissas obrigatórias. Espaço reservado para preencher quando o texto literal estiver disponível.

Como adiantamento, o ponto mais delicado do desafio foi a **Questão 2**: inferir tipos de coluna com Python puro (sem pandas) e só descobrir o estouro de `BIGINT` na `nfe_access_key` (44 dígitos) ao rodar o `CREATE TABLE` de verdade contra o Postgres — reforça por que "rodar contra o banco real" vale mais do que só ler o CSV na hora de validar um schema gerado automaticamente.

## Material complementar

Dashboard em `dashboard/lh_nautical.pbix` (Power BI Desktop, conectado ao Postgres) — guia de montagem em [`dashboard/COMO_MONTAR_DASHBOARD.md`](../dashboard/COMO_MONTAR_DASHBOARD.md). Instruções de reprodução ponta a ponta de todo o pipeline em [`README.md`](../README.md).
