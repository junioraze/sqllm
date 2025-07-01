import json
import streamlit as st
from datetime import datetime
import uuid
from style import MOBILE_IFRAME_CHAT
import pandas as pd
from io import BytesIO
import base64, re
# Estilo adicional para o chat
st.markdown(MOBILE_IFRAME_CHAT, unsafe_allow_html=True)

def _generate_key():
    timestamp = datetime.now().strftime("%Y%m%d")
    unique_id = uuid.uuid4().hex[:6]  # Pega os primeiros 6 caracteres do UUID
    return f"graph_{timestamp}_{unique_id}"  # Ex: "graph_20231025_a3f5b2"

def slugfy_response(slug: str) -> str:
    """
    Converte uma resposta em um slug amigável para URLs.
    Remove caracteres especiais e substitui espaços por hífens.
    """
    if not slug:
        return ""
    # Remove caracteres especiais e substitui espaços por hífens
    response = re.sub(r"GRAPH-TYPE:.*", "", slug).strip()
    response = re.sub(r"EXPORT-INFO:.*", "", response).strip()
    return response

def generate_excel_bytes(data: list) -> bytes:
    """Converte dados para formato Excel em memória"""
    if not data:
        return None
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Dados')
    return output.getvalue()

def generate_csv_bytes(data: list) -> bytes:
    """Converte dados para formato CSV em memória"""
    if not data:
        return None
    df = pd.DataFrame(data)
    return df.to_csv(index=False).encode('utf-8')

# Adicione este novo método para gerar botões estilizados
def create_styled_download_button(bytes_data, filename, file_type):
    """Cria um botão de download estilizado com ícone"""
    if not bytes_data:
        return ""
    
    b64 = base64.b64encode(bytes_data).decode()
    icon = ""
    bg_color = ""
    
    if file_type == "Excel":
        icon = "📊"
        bg_color = "#0E4527"  # Verde do Excel
    else:  # CSV
        icon = "📋"
        bg_color = "#124280"  # Azul do Google
    
    # Corrigindo o fechamento da tag <a> e removendo quebras de linha
    return (
        f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}" '
        f'style="display: inline-flex; align-items: center; justify-content: center; '
        f'padding: 0.5rem 1rem; background: {bg_color}; color: white; border-radius: 6px; '
        f'text-decoration: none; font-weight: 500; margin: 0.5rem 0.5rem 0.5rem 0; '
        f'box-shadow: 0 2px 5px rgba(0,0,0,0.2); transition: all 0.2s ease; min-width: 50px;" '
        f'onmouseover="this.style.transform=\'scale(1.03)\'; this.style.boxShadow=\'0 4px 8px rgba(0,0,0,0.2)\'" '
        f'onmouseout="this.style.transform=\'\'; this.style.boxShadow=\'0 2px 5px rgba(0,0,0,0.2)\'">'
        f'<span style="font-size: 1.2rem; margin-right: 8px;">{icon}</span>'
        f'{file_type}'
        f'</a>'
    )

#somente links
def create_download_link(bytes_data, filename, file_type):
    """Cria link de download para Streamlit"""
    b64 = base64.b64encode(bytes_data).decode()
    return f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}">Clique para baixar {file_type}</a>'

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
    if hasattr(params, "_values"):
        params = {k: v for k, v in params.items()}
    serializable = {}
    for k, v in params.items():
        try:
            json.dumps(v)
            serializable[k] = v
        except (TypeError, ValueError):
            serializable[k] = str(v)
    return serializable


def display_message_with_spoiler(
    role: str, content: str, tech_details: dict = None, tech_flag: bool = False
):
    with st.chat_message(role):
        st.markdown(content, unsafe_allow_html=True)
        
        if (
            tech_details
            and tech_details.get("chart_info")
            and tech_details["chart_info"]["fig"]
        ):
            st.plotly_chart(
                tech_details["chart_info"]["fig"],
                use_container_width=True,
                key=_generate_key(),
            )
        
        # Atualização aqui: renderizar todos os botões em uma única linha
        if tech_details and tech_details.get("export_links"):
            st.markdown("**Exportar dados:**")
            
            # Criar uma string HTML com todos os botões juntos
            buttons_html = '<div style="display: flex">'
            for link in tech_details["export_links"]:
                buttons_html += link
            buttons_html += '</div>'
            
            st.markdown(buttons_html, unsafe_allow_html=True)
        
        # Exibir detalhes técnicos se habilitado
        if tech_details and tech_flag:
            with st.expander("🔍 Detalhes Técnicos"):
                st.markdown(create_tech_details_spoiler(tech_details))


# utils.py - Atualize esta função
def create_tech_details_spoiler(tech_details: dict) -> str:
    """Cria o conteúdo do spoiler com detalhes técnicos"""
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
        content += dict_to_markdown_table(tech_details["raw_data"][:5])  # Mostrar apenas 5 linhas
    
    if tech_details.get("chart_info"):
        content += "\n**Informações do Gráfico:**\n"
        content += f"- Tipo: {tech_details['chart_info']['type']}\n"
        content += f"- Eixo X: {tech_details['chart_info']['x']}\n"
        content += f"- Eixo Y: {tech_details['chart_info']['y']}\n"
    
    # Adicionar informações de exportação
    if tech_details.get("export_info"):
        content += "\n**Informações de Exportação:**\n"
        for fmt, filename in tech_details["export_info"].items():
            content += f"- {fmt.upper()}: {filename}\n"
    
    return content