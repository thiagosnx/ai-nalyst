<div align="center">

# 📊 AI-nalyst

**Faça perguntas em português e obtenha gráficos interativos instantaneamente.**

Construído com LangGraph · dbt-DuckDB · Streamlit · GitHub Models (GPT-4o)

![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python)
![dbt](https://img.shields.io/badge/dbt-duckdb-orange?logo=dbt)
![Streamlit](https://img.shields.io/badge/Streamlit-1.43%2B-red?logo=streamlit)
![License](https://img.shields.io/badge/license-MIT-green)

</div>

---

## ✨ O que é isso?

Uma interface de Business Intelligence conversacional. Você digita uma pergunta em português, e o sistema:

1. Injeta o schema do dbt como contexto no LLM
2. Gera a query SQL automaticamente via GPT-4o (GitHub Models)
3. Executa no DuckDB local
4. Renderiza o gráfico Plotly mais adequado

Tudo sem nenhuma infraestrutura em nuvem — o banco roda localmente em um único arquivo `.duckdb`.

---

## 🏗️ Arquitetura

```
Kaggle CSV
  └── src/ingest.py          → data/raw/*.parquet
        └── dbt run          → database/bi_factory.duckdb
              └── LangGraph  → GPT-4o (GitHub Models)
                    └── app.py (Streamlit + Plotly)
```

**Grafo de agentes (LangGraph):**

```
schema_loader → sql_generator → query_executor
                     ↑               ↓ (erro)
                     └───────────────┘ (retry até 2×)
                                     ↓ (ok)
                                    END
```

---

## 🛠️ Stack

| Camada | Tecnologia | Função |
|---|---|---|
| Gerenciador | [`uv`](https://docs.astral.sh/uv/) | Ambiente e dependências |
| Ingestão | `kagglehub` + `pandas` | Download e conversão para Parquet |
| Transformação | `dbt-duckdb` | Modelos SQL, testes e documentação |
| Banco de dados | DuckDB | Arquivo `.duckdb` local, zero configuração |
| Agente IA | LangGraph + LangChain | Orquestração do fluxo de análise |
| LLM | GitHub Models (GPT-4o) | Geração de SQL e escolha de gráfico |
| Interface | Streamlit + Plotly | Chat e visualizações interativas |

---

## ⚡ Pré-requisitos

| Requisito | Como obter |
|---|---|
| Python 3.11+ | [python.org](https://www.python.org/downloads/) |
| `uv` | `pip install uv` ou [docs.astral.sh/uv](https://docs.astral.sh/uv/getting-started/installation/) |
| Conta no Kaggle com `kaggle.json` | [kaggle.com/settings](https://www.kaggle.com/settings) → *Create New Token* → salvar em `~/.kaggle/kaggle.json` |
| GitHub Token com acesso ao GitHub Models | [github.com/settings/tokens](https://github.com/settings/tokens) → *Generate new token (classic)* — nenhuma permissão especial necessária |

---

## 🚀 Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/ai-bi.git
cd ai-bi
```

### 2. Instale as dependências

```bash
uv sync
```

### 3. Configure as variáveis de ambiente

```bash
cp .env.example .env
```

Abra o `.env` e preencha:

```dotenv
GITHUB_TOKEN=ghp_seu_token_aqui   # token do GitHub
MODEL_NAME=gpt-4o                 # ou outro modelo disponível no GitHub Models
```

> Os demais valores já têm defaults corretos e não precisam ser alterados.

### 4. Configure o Kaggle

Certifique-se de que o arquivo `~/.kaggle/kaggle.json` existe com seu token:

```json
{"username":"seu-usuario","key":"sua-api-key"}
```

No Windows, o caminho é `C:\Users\SeuUsuario\.kaggle\kaggle.json`.

---

## ▶️ Execução

### Passo 1 — Baixar e ingerir os dados

```bash
uv run python src/ingest.py
```

Baixa o dataset [Olist Brazilian E-commerce](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) do Kaggle (~100 MB) e converte cada CSV em Parquet snappy em `data/raw/`.

### Passo 2 — Rodar as transformações dbt

> ⚠️ Execute sempre da **raiz do projeto** (não de dentro de `dbt_layer/`).

```bash
uv run dbt run           --project-dir dbt_layer --profiles-dir dbt_layer
uv run dbt test          --project-dir dbt_layer --profiles-dir dbt_layer
uv run dbt docs generate --project-dir dbt_layer --profiles-dir dbt_layer
```

Isso cria o arquivo `database/bi_factory.duckdb` e o `dbt_layer/target/manifest.json` (usado como contexto pelo agente).

### Passo 3 — Subir a aplicação

```bash
uv run streamlit run app.py
```

Acesse [http://localhost:8501](http://localhost:8501) no navegador.

---

## 💬 Exemplos de Perguntas

Veja [EXEMPLOS.md](EXEMPLOS.md) para a lista completa. Alguns destaques:

| Pergunta | Gráfico gerado |
|---|---|
| Quais estados têm mais vendas? | Barras horizontais |
| Qual é a evolução mensal do faturamento em 2018? | Linha |
| Qual a distribuição de notas de avaliação? | Pizza |
| Qual a relação entre tempo de entrega e avaliação? | Scatter |
| Quais categorias têm maior ticket médio? | Barras |

---

## 📂 Estrutura do Projeto

```
├── app.py                      # Entry-point Streamlit
├── pyproject.toml              # Dependências (uv)
├── .env.example                # Variáveis sem secrets — commitar
├── EXEMPLOS.md                 # Perguntas de exemplo para o chat
│
├── data/raw/                   # Parquets gerados pelo ingest.py (não commitados)
├── database/                   # bi_factory.duckdb gerado pelo dbt (não commitado)
│
├── dbt_layer/
│   ├── dbt_project.yml         # Config do projeto dbt
│   ├── profiles.yml            # Conexão DuckDB via env_var()
│   ├── models/
│   │   ├── staging/            # Views 1:1 com os CSVs originais
│   │   │   ├── stg_orders.sql
│   │   │   ├── stg_order_items.sql
│   │   │   ├── stg_products.sql
│   │   │   ├── stg_customers.sql
│   │   │   ├── stg_sellers.sql
│   │   │   ├── stg_reviews.sql
│   │   │   └── schema.yml      # Descrições de colunas (PT-BR)
│   │   └── marts/
│   │       ├── fct_sales.sql   # Fato de vendas (pedidos + itens + produtos + clientes)
│   │       ├── fct_reviews.sql # Fato de avaliações
│   │       └── schema.yml      # Descrições de colunas (PT-BR)
│   └── target/
│       └── manifest.json       # Gerado pelo dbt docs generate — contexto do LLM
│
└── src/
    ├── ingest.py               # Download Kaggle + CSV → Parquet
    └── agent/
        ├── graph.py            # Grafo LangGraph (singleton)
        ├── nodes.py            # load_schema · generate_sql · execute_query
        ├── state.py            # AgentState TypedDict
        └── rate_limiter.py     # InMemoryRateLimiter (≈9 req/min)
```

---

## 🔐 Variáveis de Ambiente

| Variável | Obrigatória | Descrição | Padrão |
|---|---|---|---|
| `GITHUB_TOKEN` | ✅ | Token para GitHub Models | — |
| `MODEL_NAME` | | Modelo LLM | `gpt-4o` |
| `DB_PATH` | | Caminho do arquivo DuckDB | `database/bi_factory.duckdb` |
| `DBT_PROFILES_DIR` | | Diretório do `profiles.yml` | `./dbt_layer` |
| `DATA_RAW_PATH` | | Pasta dos Parquets brutos | `data/raw` |
| `DBT_MANIFEST_PATH` | | Caminho do `manifest.json` | `dbt_layer/target/manifest.json` |

---

## 🔄 Re-execução após Mudanças

| Situação | Comando necessário |
|---|---|
| Novos dados do Kaggle | `uv run python src/ingest.py` + `dbt run` + `dbt docs generate` |
| Alteração em modelos `.sql` | `dbt run` + `dbt docs generate` |
| Alteração em `schema.yml` | `dbt docs generate` (sem `dbt run`) |
| Só atualizar o agente/app | Basta reiniciar o Streamlit |

---

## ⚠️ Aviso de Segurança (Leia antes de usar)

> **Este projeto é uma prova de conceito para uso local e educacional.**

As seguintes proteções **ainda não estão implementadas** e entrarão em versões futuras:

| Vetor | Status |
|---|---|
| **Prompt injection** — um usuário mal-intencionado pode tentar manipular o LLM via a caixa de chat | 🔴 Sem proteção |
| **SQL injection via LLM** — o modelo pode ser induzido a gerar SQL destrutivo | 🟡 Mitigado parcialmente pelo `read_only=True`, mas sem validação da query |
| **Sanitização de entrada** — o input do usuário é enviado diretamente ao LLM sem filtros | 🔴 Sem proteção |
| **Rate limiting por usuário** — qualquer pessoa com acesso à URL pode esgotar sua cota do GitHub Models | 🔴 Sem proteção |
| **Autenticação** — a interface Streamlit não exige login | 🔴 Sem proteção |

**Recomendações para uso seguro hoje:**

- ✅ Rode apenas localmente (`localhost`) — nunca exponha a porta 8501 publicamente
- ✅ Implemente as etapas de segurança caso queira usar em produção ou entre em contato com o autor

---

## 🛡️ Segurança (Implementado)

- O `.env` está no `.gitignore` — nunca é commitado
- O token do GitHub nunca aparece em logs
- Queries geradas pelo LLM são executadas em **modo somente leitura** (`read_only=True`)
- Nenhum caminho ou credencial é hardcoded — tudo via `os.getenv()`

---

## 📚 Referências

- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [dbt-duckdb Adapter](https://github.com/duckdb/dbt-duckdb)
- [GitHub Models](https://docs.github.com/en/github-models)
- [Olist Brazilian E-commerce (Kaggle)](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
- [InMemoryRateLimiter (LangChain)](https://python.langchain.com/docs/how_to/chat_model_rate_limiting/)

---

## 📄 Licença

MIT — veja [LICENSE](LICENSE) para detalhes.
