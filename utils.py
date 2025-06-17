import json
import streamlit as st

def dict_to_markdown_table(data: list) -> str:
    """Converte uma lista de dicionários em tabela markdown."""
    if not data or not isinstance(data, list):
        return "Nenhum dado disponível"
    
    if isinstance(data, dict):  # Se for um único dict (erro, por exemplo)
        return "\n".join(f"**{k}**: {v}" for k, v in data.items())
    
    colunas = data[0].keys()
    linhas = [list(row.values()) for row in data]
    
    tabela = "| " + " | ".join(colunas) + " |\n"
    tabela += "| " + " | ".join("---" for _ in colunas) + " |\n"
    
    for linha in linhas:
        tabela += "| " + " | ".join(str(v) for v in linha) + " |\n"
    
    return tabela

def create_tech_details_spoiler(tech_details: dict) -> str:
    """Cria o conteúdo do spoiler com detalhes técnicos."""
    if not tech_details:
        return ""
    
    content = "### Detalhes Técnicos\n\n"
    
    if tech_details.get("function_params"):
        content += "**Parâmetros da Função:**\n```json\n"
        content += json.dumps(tech_details["function_params"], indent=2)
        content += "\n```\n\n"
    
    if tech_details.get("query"):
        content += "**Query SQL Executada:**\n```sql\n"
        content += tech_details["query"]
        content += "\n```\n\n"
    
    if tech_details.get("raw_data"):
        content += "**Dados Brutos Recebidos:**\n"
        content += dict_to_markdown_table(tech_details["raw_data"])
    
    return content

def display_message_with_spoiler(role: str, content: str, tech_details: dict = None):
    """Exibe uma mensagem no chat com spoiler para detalhes técnicos."""
    with st.chat_message(role):
        st.markdown(content)
        
        if tech_details:
            with st.expander("🔍 Detalhes Técnicos"):
                st.markdown(create_tech_details_spoiler(tech_details))