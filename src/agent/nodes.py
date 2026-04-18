import json
import os
import sys
import duckdb
import pandas as pd
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage

from .state import AgentState

load_dotenv()

# ---------------------------------------------------------------------------
# Validação de variáveis obrigatórias ao importar o módulo
# ---------------------------------------------------------------------------
_required = ["DB_PATH", "DBT_MANIFEST_PATH"]
for _var in _required:
    if not os.getenv(_var):
        print(f"❌ Variável de ambiente obrigatória ausente: {_var}", file=sys.stderr)

# ---------------------------------------------------------------------------
# Prompt System
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """Você é um analista de dados especializado em e-commerce brasileiro.
Você tem acesso ao seguinte schema de dados:

{schema_context}

Dado uma pergunta em português, você deve:
1. Gerar uma query SQL válida para DuckDB que responda à pergunta.
2. Escolher o tipo de gráfico Plotly mais adequado entre: bar, line, pie, scatter, histogram, heatmap, table.
3. Sugerir título e configuração de eixos quando relevante.

Responda SOMENTE em JSON com o formato:
{{
  "sql": "SELECT ...",
  "chart_type": "bar",
  "chart_config": {{
    "title": "...",
    "x": "coluna_x",
    "y": "coluna_y",
    "color": "coluna_opcional"
  }}
}}

Se a pergunta não puder ser respondida com o schema disponível, retorne:
{{"error": "Motivo pelo qual não é possível responder."}}
"""


# ---------------------------------------------------------------------------
# Nó 1: load_schema
# ---------------------------------------------------------------------------
def load_schema(state: AgentState) -> dict:
    """Lê o manifest.json do dbt e constrói o schema_context para o LLM."""
    manifest_path = os.getenv("DBT_MANIFEST_PATH", "dbt_layer/target/manifest.json")

    try:
        with open(manifest_path, encoding="utf-8") as f:
            manifest = json.load(f)
    except FileNotFoundError:
        return {
            "schema_context": (
                "⚠️ manifest.json não encontrado. "
                "Execute 'uv run dbt docs generate' dentro de dbt_layer/."
            )
        }

    lines: list[str] = []
    nodes = manifest.get("nodes", {})

    for node_id, node in nodes.items():
        # Apenas modelos do tipo 'model' pertencentes ao projeto bi_factory
        if node.get("resource_type") != "model":
            continue
        if node.get("package_name") != "bi_factory":
            continue

        model_name = node.get("name", "")
        model_desc = node.get("description", "")
        lines.append(f"\n## Tabela: {model_name}")
        if model_desc:
            lines.append(f"Descrição: {model_desc}")

        columns = node.get("columns", {})
        for col_name, col_meta in columns.items():
            col_desc = col_meta.get("description", "")
            col_type = col_meta.get("data_type", "")
            type_str = f" ({col_type})" if col_type else ""
            desc_str = f" — {col_desc}" if col_desc else ""
            lines.append(f"  - {col_name}{type_str}{desc_str}")

    schema_context = "\n".join(lines) if lines else "Schema não disponível."
    return {"schema_context": schema_context}


# ---------------------------------------------------------------------------
# Nó 2: generate_sql
# ---------------------------------------------------------------------------
def generate_sql(state: AgentState, llm) -> dict:
    """Chama o LLM para gerar SQL e tipo de gráfico com base na pergunta e no schema."""
    system_content = SYSTEM_PROMPT.format(
        schema_context=state.get("schema_context", "")
    )

    # Se há erro de tentativa anterior, adicionar como contexto de feedback
    user_content = state["question"]
    if state.get("error") and state.get("retry_count", 0) > 0:
        user_content = (
            f"{state['question']}\n\n"
            f"[FEEDBACK DA TENTATIVA ANTERIOR]\n"
            f"O SQL gerado causou o seguinte erro: {state['error']}\n"
            f"Por favor, corrija o SQL."
        )

    messages = [
        SystemMessage(content=system_content),
        HumanMessage(content=user_content),
    ]

    try:
        response = llm.invoke(messages)
        raw = response.content.strip()

        # Remover possíveis blocos markdown ```json ... ```
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        return {"error": f"Resposta do LLM não é JSON válido: {exc}", "sql_query": ""}
    except Exception as exc:
        err_str = str(exc)
        # Propaga erros de rate limit — se chegou aqui, o fallback Gemini
        # também falhou (ou não estava configurado). Deixa o app.py tratar.
        if "RateLimitReached" in err_str or "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
            raise
        return {"error": f"Erro ao chamar o LLM: {exc}", "sql_query": ""}

    if "error" in parsed:
        return {"error": parsed["error"], "sql_query": ""}

    return {
        "sql_query": parsed.get("sql", ""),
        "chart_type": parsed.get("chart_type", "table"),
        "chart_config": parsed.get("chart_config", {}),
        "error": None,
    }


# ---------------------------------------------------------------------------
# Nó 3: execute_query
# ---------------------------------------------------------------------------
def execute_query(state: AgentState) -> dict:
    """Executa a query SQL gerada no DuckDB em modo somente leitura."""
    sql = state.get("sql_query", "").strip()
    if not sql:
        return {"error": "Nenhuma query SQL foi gerada.", "dataframe": None}

    db_path = os.getenv("DB_PATH")
    if not db_path:
        return {"error": "Variável DB_PATH não definida.", "dataframe": None}

    try:
        # read_only=True para segurança — o mart já está construído pelo dbt
        conn = duckdb.connect(db_path, read_only=True)
        df: pd.DataFrame = conn.execute(sql).fetchdf()
        conn.close()
        return {"dataframe": df, "error": None}
    except Exception as exc:
        retry = state.get("retry_count", 0)
        return {
            "dataframe": None,
            "error": str(exc),
            "retry_count": retry + 1,
        }


# ---------------------------------------------------------------------------
# Função de routing condicional
# ---------------------------------------------------------------------------
def should_retry(state: AgentState) -> str:
    """Decide se deve tentar gerar o SQL novamente ou finalizar."""
    if state.get("error") and state.get("retry_count", 0) < 2:
        return "generate_sql"
    return "render"
