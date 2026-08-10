# Desafio de Dados LH Nautical

Pipeline completo do desafio: EDA → schema PostgreSQL → carga → análise de clientes → dimensão de calendário → previsão de demanda → recomendação → dashboard.

Todas as respostas escritas (validações numéricas + explicações) estão em [`respostas/respostas_desafio.md`](respostas/respostas_desafio.md).

## Estrutura

```
data/raw/              os 24 CSVs originais (imutáveis)
sql/                   SQL de cada questão (Q1, Q4, Q5) + schema gerado (Q2)
src/                   scripts Python de cada questão (Q2, Q3, Q6, Q7) + helper db.py
respostas/             respostas_desafio.md — validações e explicações de cada questão
dashboard/             lh_nautical.pbix (a montar) + guia de montagem
.venv/                 ambiente virtual Python do projeto
```

## Ambiente

- **PostgreSQL 17** nativo (Windows), banco `lh_nautical`, usuário `postgres` / senha `123456` (uso local de desenvolvimento).
- **Python 3.12** em `.venv/`, com `psycopg2-binary`, `duckdb`, `pandas`, `numpy`, `scikit-learn`.
- O script da Questão 2 (`src/q2_generate_schema.py`) roda com **qualquer** Python 3 (só biblioteca padrão) — não depende do venv.
- O script da Questão 7 (`src/q7_recommend_similar.py`) usa só `pandas`/`numpy`/`sklearn`, lendo os CSVs diretamente (não usa Postgres), conforme a lista de bibliotecas permitida na questão.

## Como reproduzir, do zero

```powershell
# 1. Gerar o schema (Q2) — funciona com qualquer Python 3, sem instalar nada
python src\q2_generate_schema.py            # gera sql\q2_schema.sql

# 2. Carregar os dados no Postgres (Q3) — recria as tabelas e faz a carga via COPY
.venv\Scripts\python.exe src\q3_load_data.py

# 3. Rodar as consultas SQL de Q4 e Q5 (cria views v_q4_* e v_q5_*)
$env:PGPASSWORD="123456"
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres -h 127.0.0.1 -d lh_nautical -f sql\q4_clientes_fieis.sql
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres -h 127.0.0.1 -d lh_nautical -f sql\q5_calendario_vendas.sql

# 4. Rodar a previsao de demanda (Q6) e a recomendacao (Q7)
.venv\Scripts\python.exe src\q6_forecast_bussola.py
.venv\Scripts\python.exe src\q7_recommend_similar.py

# 5. Exportar os resultados de Q6/Q7 como tabelas no Postgres, para o dashboard
.venv\Scripts\python.exe src\export_results_for_dashboard.py
```

A Questão 1 (`sql/q1_eda_orders.sql`) roda com DuckDB direto sobre `orders.csv`, sem precisar do Postgres — é anterior à criação do banco no fluxo do desafio.

## Dashboard

Ver [`dashboard/COMO_MONTAR_DASHBOARD.md`](dashboard/COMO_MONTAR_DASHBOARD.md) — guia passo a passo para conectar o Power BI Desktop (já instalado) ao Postgres e montar as páginas do painel a partir das views/tabelas já prontas (`v_q4_clientes_fieis`, `v_q5_calendario_vendas`, `q6_previsao_demanda`, `q7_recomendacoes`).

## Decisões e premissas documentadas

Sempre que uma questão deixava uma regra em aberto (ex.: filtrar `orders.status`, qual data usar como "data da venda", como tratar produtos com nome duplicado no catálogo), a escolha feita está documentada explicitamente em `respostas/respostas_desafio.md`, seção da questão correspondente — nenhuma decisão de negócio foi tomada "escondida" dentro do código.
