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

## 3. Páginas sugeridas

**Página 1 — Diagnóstico da base (Q1)**
Cartões (KPI cards) com: quantidade de linhas de `orders`, total mínimo/máximo/médio, e um texto com o diagnóstico (copiar de `respostas/respostas_desafio.md`, Questão 1.3).

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

## 4. Salvar

Salve o arquivo como `dashboard/lh_nautical.pbix` (já existe a pasta `dashboard/` no projeto).

## Referência rápida de conexão
```
host: localhost
porta: 5432
banco: lh_nautical
usuário: postgres
senha: 123456
```
