import streamlit as st
import plotly.express as px
from src.agent.graph import get_graph

st.set_page_config(page_title="AI-nalyst", layout="wide")
st.title("📊 AI-nalyst")

# Inicializar histórico de chat na sessão
if "messages" not in st.session_state:
    st.session_state.messages = []

# Exibir histórico
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("figure"):
            st.plotly_chart(msg["figure"], use_container_width=True)
        if msg.get("dataframe") is not None:
            st.dataframe(msg["dataframe"], use_container_width=True)

# Input do usuário
if prompt := st.chat_input("Faça uma pergunta sobre os dados (ex: Quais estados têm mais vendas?)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analisando sua pergunta..."):
            graph = get_graph()
            result = graph.invoke({
                "question": prompt,
                "retry_count": 0,
                "error": None,
            })

        if result.get("error"):
            st.error(f"❌ {result['error']}")
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"❌ {result['error']}",
            })
        else:
            df = result["dataframe"]
            cfg = result.get("chart_config", {})
            chart_type = result.get("chart_type", "table")

            # Renderização dinâmica de gráfico
            fig = None
            chart_fns = {
                "bar":       px.bar,
                "line":      px.line,
                "pie":       px.pie,
                "scatter":   px.scatter,
                "histogram": px.histogram,
                "heatmap":   px.density_heatmap,
            }
            if chart_type in chart_fns and df is not None and not df.empty:
                # Filtrar apenas parâmetros cujas colunas existem no DataFrame
                valid_cfg = {
                    k: v for k, v in cfg.items()
                    if k in ["x", "y", "color", "title", "names", "values"]
                    and (k == "title" or v in df.columns)
                }
                # Fallback de título usando a pergunta do usuário
                if "title" not in valid_cfg:
                    valid_cfg["title"] = prompt
                try:
                    fig = chart_fns[chart_type](df, **valid_cfg)
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as chart_err:
                    st.warning(f"⚠️ Não foi possível renderizar o gráfico: {chart_err}")

            if df is not None and not df.empty:
                st.dataframe(df, use_container_width=True)

            sql_shown = result.get("sql_query", "")
            if sql_shown:
                with st.expander("Ver SQL gerado"):
                    st.code(sql_shown, language="sql")

            st.session_state.messages.append({
                "role": "assistant",
                "content": f"```sql\n{sql_shown}\n```",
                "figure": fig,
                "dataframe": df,
            })
