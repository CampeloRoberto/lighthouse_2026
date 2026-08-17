# Como montar o dashboard no Power BI Desktop

O Power BI Desktop já está instalado nesta máquina. Toda a camada de dados já está pronta no PostgreSQL — o Power BI só precisa se conectar e consumir.

## 1. Conectar ao banco

1. Abra o **Power BI Desktop**.
2. `Página Inicial → Obter Dados → Banco de Dados PostgreSQL`.
3. Servidor: `localhost:5432` — Banco de dados: `lh_nautical`.
4. Modo de conectividade: **Import** (o volume é pequeno, ~430 mil linhas no total).
5. Na tela de credenciais, use: usuário `postgres`, senha `123456`.
6. Se pedir para instalar o driver Npgsql, aceite (é automático do próprio Power BI).

## 2. Tabelas/views para importar

Marque estas (todas já vêm prontas, sem precisar transformar nada no Power Query):

| Objeto | Conteúdo | Para qual página |
|---|---|---|
| `v_q4_clientes_fieis` | Top 10 clientes fiéis (ticket médio + diversidade) | Página Clientes Fiéis |
| `v_q5_calendario_vendas` | Calendário completo × vendas diárias (pos), zero nos dias sem venda | Página Vendas por Dia da Semana |
| `q6_previsao_demanda` | Série mensal real vs. prevista da Bússola de Bordo 702 | Página Previsão de Demanda |
| `q7_recomendacoes` | Top 5 produtos similares ao Motor de Popa 1949 | Página Recomendação |
| `orders`, `order_items`, `products`, `product_variants`, `categories`, `customers` | Tabelas brutas, para qualquer exploração extra | Página Visão Geral (opcional) |

## 3. Modelo de relacionamentos

As tabelas do Postgres **não têm foreign key** (decisão da Questão 2: o script só infere coluna+tipo, sem PK/FK — não foi pedido pela tarefa). Por isso o Power BI não autodetecta nada e você precisa criar os relacionamentos na mão em `Modelagem → Gerenciar relacionamentos → Nova relação`.

**As 4 tabelas de resultado não precisam de relacionamento com nada.** `v_q4_clientes_fieis`, `v_q5_calendario_vendas`, `q6_previsao_demanda` e `q7_recomendacoes` já vêm pré-agregadas/prontas — cada uma alimenta seu próprio visual sozinha (é assim que foram desenhadas). Deixe soltas no modelo.

Se você importou as tabelas brutas para a página extra (passo 6), monte esta cadeia (sempre "muitos" → "um", filtro fluindo da dimensão pro fato):

```
categories (1) ──< products (muitos)
products (1) ──< product_variants (muitos)
product_variants (1) ──< order_items (muitos)
orders (1) ──< order_items (muitos)
customers (1) ──< orders (muitos)
```

Ou seja, 5 relações no total:
| Tabela "um" (coluna) | Tabela "muitos" (coluna) |
|---|---|
| `categories.id` | `products.category_id` |
| `products.id` | `product_variants.product_id` |
| `product_variants.id` | `order_items.product_variant_id` |
| `orders.id` | `order_items.order_id` |
| `customers.id` | `orders.customer_id` |

`order_items` fica no centro (é a tabela "fato"), recebendo duas relações (de `orders` e de `product_variants`). Cardinalidade em todas: **um-para-muitos**, direção do filtro **única** (da tabela "um" para a "muitos" — o padrão do Power BI já vem assim, não precisa mexer).

## 4. Páginas sugeridas

### Página 1 — Diagnóstico da base (Q1)

Precisa da tabela `orders` importada (passo 2). Tudo aqui é sobre essa tabela sozinha, sem relacionamento com nada — mesma regra da Questão 1 (só `orders`, sem tratamento).

**1) Criar as medidas (recomendado, em vez de usar agregação automática do campo)**

No painel **Campos**, clique com o botão direito em `orders` → **Nova medida**, e crie uma de cada vez (cole o DAX, dê Enter):

```dax
Total de Pedidos = COUNTROWS(orders)
Data Mínima = MIN(orders[created_at])
Data Máxima = MAX(orders[created_at])
Total Mínimo (R$) = MIN(orders[total])
Total Médio (R$) = AVERAGE(orders[total])
Total Máximo (R$) = MAX(orders[total])
% Pedidos Pagos = DIVIDE(CALCULATE(COUNTROWS(orders), orders[status] = "paid"), COUNTROWS(orders))
% Sem Vendedor = DIVIDE(CALCULATE(COUNTROWS(orders), ISBLANK(orders[salesperson_id])), COUNTROWS(orders))
```

Formate as três medidas de `Total ... (R$)` como moeda: selecione a medida no painel Campos → aba **Ferramentas de Medida** → Formato → `Moeda`.

**2) Cartões (KPIs) no topo da página**

Para cada medida acima, insira um visual **Cartão** (ícone de retângulo com número, no painel Visualizações) e arraste a medida para o campo "Dados". Deixe 6 cartões lado a lado: Total de Pedidos, Data Mínima, Data Máxima, Total Mínimo, Total Médio, Total Máximo. Redimensione o texto se precisar (aba Formatar → Rótulo de Dados).

**3) Gráfico "Pedidos por Status" (mostra a mistura paid/confirmed/cancelled/draft)**

Visual **Gráfico de Colunas** (ou Rosca): Eixo X = `orders[status]`, Valores = `Total de Pedidos` (a medida de contagem). Isso ilustra visualmente por que `orders` sozinha não deve virar "receita" sem filtrar status.

**4) (Opcional) Distribuição de `total` — para visualizar os outliers**

No painel Campos, clique com botão direito em `orders[total]` → **Novo grupo** → Tipo de agrupamento: **Intervalo (bin)** → tamanho do intervalo (bin size): `10000`. Isso cria um campo `total (intervalos)`. Monte um **Gráfico de Colunas**: Eixo X = `total (intervalos)`, Valores = `Total de Pedidos`. Mostra a cauda longa da distribuição (poucos pedidos grandes, muitos pequenos/médios).

**5) Caixa de texto com o diagnóstico**

Insira uma **Caixa de Texto** (`Inserir → Elementos de Texto → Caixa de Texto`) e cole um resumo do diagnóstico (a versão completa está em `respostas/respostas_desafio.md`, Questão 1.3):

> "48.998 pedidos, 13 colunas, de 2020 a 2026. Total médio R$ 28.704,99, distribuição larga mas sem outlier absurdo isolado. `salesperson_id` nulo em ~49% dos casos (parcialmente ligado ao canal ecommerce). Só 70% dos pedidos estão `paid` — a tabela não deve virar métrica de receita sem filtrar status e sem relacionar com `order_items`/`payments`."

**Página 2 — Clientes Fiéis (Q4)**
Tabela ou gráfico de barras horizontais com `v_q4_clientes_fieis` (eixo Y = `customer_id`, eixo X = `ticket_medio`), mais um cartão com a categoria vencedora ("Hélices", 492 unidades).

**Página 3 — Vendas por Dia da Semana (Q5)**
Gráfico de colunas com `v_q5_calendario_vendas` agregado por `dia_semana` (média de `valor_venda`), ordenado por `dow` (Segunda→Domingo). Destaque visual no pior dia (quinta-feira).

**Página 4 — Previsão de Demanda (Q6)**
Gráfico de linhas com `q6_previsao_demanda`: eixo X = `mes`, duas séries (`quantidade_real` e `quantidade_prevista`). Cartão com o MAE (19,44) e a soma prevista vs. real do trimestre (149 vs. 207).

**Página 5 — Recomendação (Q7)**
Gráfico de barras com `q7_recomendacoes` (produto recomendado × similaridade), título mencionando o produto de referência.

**Página 6 — Extra (opcional)**
Qualquer exploração adicional que você quiser destacar (receita por canal/loja, devoluções etc.), usando as tabelas brutas.

## 5. Salvar

Salve o arquivo como `dashboard/lh_nautical.pbix` (já existe a pasta `dashboard/` no projeto).

## Referência rápida de conexão
```
host: localhost
porta: 5432
banco: lh_nautical
usuário: postgres
senha: 123456
```
