import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

from .state import AgentState
from .nodes import load_schema, generate_sql, execute_query, should_retry
from .rate_limiter import rate_limiter

load_dotenv()


def build_graph():
    """Instancia o LLM e compila o grafo LangGraph."""
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        raise EnvironmentError("❌ Variável GITHUB_TOKEN não definida no .env")

    llm = ChatOpenAI(
        model=os.getenv("MODEL_NAME", "gpt-4o"),
        api_key=github_token,
        base_url="https://models.inference.ai.azure.com",
        rate_limiter=rate_limiter,
    )

    graph = StateGraph(AgentState)

    graph.add_node("schema_loader",  lambda s: load_schema(s))
    graph.add_node("sql_generator",  lambda s: generate_sql(s, llm))
    graph.add_node("query_executor", lambda s: execute_query(s))

    graph.set_entry_point("schema_loader")
    graph.add_edge("schema_loader", "sql_generator")
    graph.add_edge("sql_generator",  "query_executor")
    graph.add_conditional_edges(
        "query_executor",
        should_retry,
        {
            "generate_sql": "sql_generator",  # retry com feedback de erro
            "render": END,
        },
    )

    compiled = graph.compile()
    return compiled


# ---------------------------------------------------------------------------
# Singleton — compilado uma única vez, reutilizado entre sessões Streamlit
# ---------------------------------------------------------------------------
_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph
