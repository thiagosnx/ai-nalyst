from typing import TypedDict, Optional, Any


class AgentState(TypedDict):
    question: str           # pergunta original do usuário
    schema_context: str     # metadados extraídos do manifest.json
    sql_query: str          # SQL gerado pelo LLM
    chart_type: str         # tipo de gráfico sugerido pelo LLM
    chart_config: dict      # configuração extra do gráfico (eixos, título)
    dataframe: Optional[Any]  # resultado da query como DataFrame
    error: Optional[str]    # mensagem de erro, se houver
    retry_count: int        # contador de tentativas (para retry automático)
