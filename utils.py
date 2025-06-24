import json
import streamlit as st

def dict_to_markdown_table(data: list) -> str:
    """
    Converte uma lista de dicionários em tabela markdown.
    """
    if not data or not isinstance(data, list):
        return "Nenhum dado disponível"
    if isinstance(data, dict):
        return "\n".join(f"**{k}**: {v}" for k, v in data.items())
    colunas = data[0].keys()
    linhas = [list(row.values()) for row in data]
    tabela = "| " + " | ".join(colunas) + " |\n"
    tabela += "| " + " | ".join("---" for _ in colunas) + " |\n"
    for linha in linhas:
        tabela += "| " + " | ".join(str(v) for v in linha) + " |\n"
    return tabela

def serialize_params(params):
    """
    Serializa parâmetros para JSON, lidando com tipos complexos.
    """
    if params is None:
        return None
    if hasattr(params, '_values'):
        params = {k: v for k, v in params.items()}
    serializable = {}
    for k, v in params.items():
        try:
            json.dumps(v)
            serializable[k] = v
        except (TypeError, ValueError):
            serializable[k] = str(v)
    return serializable

def display_message_with_spoiler(role: str, content: str, tech_details: dict = None, tech_flag: bool = False):
    with st.chat_message(role):
        st.markdown(content)
        if tech_details and tech_details.get("chart_info") and tech_details["chart_info"]["fig"]:
            st.plotly_chart(
                tech_details["chart_info"]["fig"],
                use_container_width=True
            )
        if tech_details and tech_flag:
            with st.expander("🔍 Detalhes Técnicos"):
                st.markdown(create_tech_details_spoiler(tech_details))

def create_tech_details_spoiler(tech_details: dict) -> str:
    """
    Cria o conteúdo do spoiler com detalhes técnicos.
    """
    if not tech_details:
        return ""
    content = "### Detalhes Técnicos\n\n"
    if tech_details.get("function_params"):
        content += "**Parâmetros da Função:**\n```json\n"
        serialized_params = serialize_params(tech_details["function_params"])
        content += json.dumps(serialized_params, indent=2, default=str)
        content += "\n```\n\n"
    if tech_details.get("query"):
        content += "**Query SQL Executada:**\n```sql\n"
        content += tech_details["query"]
        content += "\n```\n\n"
    if tech_details.get("raw_data"):
        content += "**Dados Brutos Recebidos:**\n"
        content += dict_to_markdown_table(tech_details["raw_data"])
    if tech_details.get("chart_info"):
        content += "**Informações do Gráfico:**\n"
        content += f"- Tipo: {tech_details['chart_info']['type']}\n"
        content += f"- Eixo X: {tech_details['chart_info']['x']}\n"
        content += f"- Eixo Y: {tech_details['chart_info']['y']}\n"
    return content