
import json
import streamlit as st
from datetime import datetime
import uuid
import pandas as pd
from io import BytesIO
import base64, re
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
# Exibe uma tabela interativa com AgGrid, aplicando tema customizado

def show_aggrid_table(data: list, theme: str = "streamlit", height: int = 350, fit_columns: bool = True):
    # Detecta tema do Streamlit e aplica CSS específico
    if not data or not isinstance(data, list) or not isinstance(data[0], dict):
        st.info("Nenhum dado tabular disponível para exibir.")
        return
    df = pd.DataFrame(data)
    # Tabela principal customizada
    st.markdown("<div class='section-label'>dados</div>", unsafe_allow_html=True)
    st.markdown(_render_custom_table(df), unsafe_allow_html=True)

    # Se for numérico, mostra sumário analítico dentro de um expander fechado
    if not df.empty:
        numeric_cols = df.select_dtypes(include=["number"]).columns
        if len(numeric_cols) > 0:
            with st.expander("Resumo Analítico (abrir para ver detalhes)", expanded=False):
                resumo = df[numeric_cols].describe().T
                resumo = resumo.rename(columns={
                    "count": "Frequência",
                    "mean": "Média",
                    "std": "Desvio Padrão",
                    "min": "Mínimo",
                    "25%": "1º Quartil",
                    "50%": "Mediana",
                    "75%": "3º Quartil",
                    "max": "Máximo"
                })
                resumo.index.name = "Coluna"
                st.markdown(_render_custom_table(resumo, small=True, show_index=True, bar_columns=["Média", "Quantidade", "Máximo"]), unsafe_allow_html=True)

def _render_custom_table(df, small=False, show_index=False, bar_columns=None):
    """
    Renderiza um DataFrame como tabela HTML customizada, elegante e responsiva ao tema.
    show_index: se True, mostra o índice como primeira coluna.
    bar_columns: lista de colunas para exibir barra de volume proporcional.
    """
    if df.empty:
        return "<em>Nenhum dado disponível</em>"
    table_class = "custom-table small-table" if small else "custom-table"
    html = f'<div style="overflow-x:auto;"><table class="{table_class}">'
    # Cabeçalho
    html += "<thead><tr>"
    if show_index:
        html += f'<th>{df.index.name or ""}</th>'
    for col in df.columns:
        html += f'<th>{col}</th>'
    html += "</tr></thead>"
    # Prepara escala para barras
    bar_max = {}
    if bar_columns:
        for col in bar_columns:
            if col in df.columns:
                vals = pd.to_numeric(df[col], errors="coerce")
                bar_max[col] = vals.max() if vals.notnull().any() else 1
    # Corpo
    html += "<tbody>"
    for idx, row in df.iterrows():
        html += "<tr>"
        if show_index:
            html += f'<td style="font-weight:600;">{idx}</td>'
        for col, val in row.items():
            display_val = val
            if pd.notnull(val) and isinstance(val, (int, float)):
                if isinstance(val, int):
                    display_val = f"{val:,}".replace(",", ".")
                else:
                    display_val = f"{val:,.4f}".replace(",", "X").replace(".", ",").replace("X", ".")
            elif pd.isnull(val):
                display_val = ""
            if bar_columns and col in bar_max and pd.notnull(val):
                width = int(100 * float(val) / bar_max[col]) if bar_max[col] else 0
                bar_html = f'<div style="height:0.9em;width:{width}%;background:linear-gradient(90deg,var(--text-accent),var(--bg-tertiary));border-radius:4px;"></div>'
                html += f'<td style="position:relative;">{display_val}<div style="margin-top:0.15em;">{bar_html}</div></td>'
            else:
                html += f'<td>{display_val}</td>'
        html += "</tr>"
    html += "</tbody></table></div>"
    # CSS customizado responsivo ao tema
    css = '''
    <style>
    .custom-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        background: var(--bg-tertiary);
        border: 1.2px solid var(--border-primary);
        border-radius: 13px;
        font-size: 1.05em;
        margin-bottom: 1em;
        box-shadow: 0 4px 18px 0 rgba(0,0,0,0.10), 0 1.5px 0 0 var(--border-primary);
        overflow: hidden;
        /* Efeito de alto relevo sutil para padronizar com outros blocos */
        transition: box-shadow 0.2s;
    }
    .custom-table th, .custom-table td {
        text-align: center;
        vertical-align: middle;
        padding: 0.6em 0.7em;
        color: var(--text-primary);
        border-bottom: 1px solid var(--border-primary);
    }
    .custom-table th {
        background: var(--bg-secondary);
        font-weight: 600;
        border-bottom: 2px solid var(--border-primary);
    }
    .custom-table tr:last-child td {
        border-bottom: none;
    }
    .custom-table.small-table {
        font-size: 0.98em;
        margin-top: 0.2em;
        margin-bottom: 0.2em;
    }
    .custom-table tbody tr:nth-child(even) {
        background: rgba(0,0,0,0.03);
    }
    /* Borda e alto relevo sutil para tema escuro */
    html[data-theme="dark"] .custom-table,
    body[data-theme="dark"] .custom-table {
        border: 1.7px solid #353535;
        box-shadow: 0 4px 22px 0 rgba(0,0,0,0.18), 0 1.5px 0 0 #353535;
        background: var(--bg-tertiary);
    }
    html[data-theme="dark"] .custom-table th, html[data-theme="dark"] .custom-table td,
    body[data-theme="dark"] .custom-table th, body[data-theme="dark"] .custom-table td {
        border-bottom: 1.2px solid #444;
    }
    .section-label {
        font-size: 0.97em;
        color: var(--text-secondary);
        font-weight: 500;
        letter-spacing: 0.03em;
        margin-bottom: 0.18em;
        margin-top: 0.7em;
        text-transform: lowercase;
        opacity: 0.78;
    }
    </style>
    '''
    return css + html
    
def format_text_with_ia_highlighting(text: str) -> str:
    """
    Formata qualquer texto aplicando destaque laranja em variações de IA usando HTML.
    Funciona para: IA, ia, Ia, iA e garante máxima compatibilidade com Streamlit.
    
    Args:
        text (str): Texto a ser formatado
        
    Returns:
        str: Texto com IA destacado em laranja usando HTML spans
    """
    if not text or not isinstance(text, str):
        return text
    
    # Padrão regex que captura todas as variações de IA
    pattern = r'\b(IA|ia|Ia|iA)\b'
    
    # Substitui todas as variações por spans HTML com cor laranja e negrito
    def replace_ia(match):
        ia_text = match.group(1)
        return f'<span style="color: #ff6b35; font-weight: bold;">{ia_text}</span>'
    
    formatted_text = re.sub(pattern, replace_ia, text)
    
    return formatted_text

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
        # Aplica formatação IA ao conteúdo das mensagens
        formatted_content = format_text_with_ia_highlighting(content)
        st.markdown(formatted_content, unsafe_allow_html=True)
        
        # Exibe botões de download se disponíveis (UMA VEZ APENAS)
        if tech_details and tech_details.get("export_links"):
            export_text = format_text_with_ia_highlighting("**Exportar dados:**")
            st.markdown(export_text)
            # Criar uma string HTML com todos os botões juntos
            buttons_html = '<div style="display: flex">'
            for link in tech_details["export_links"]:
                buttons_html += link
            buttons_html += '</div>'
            st.markdown(buttons_html, unsafe_allow_html=True)
        
        # Exibe botões de download se disponíveis (UMA VEZ APENAS)
        if tech_details and tech_details.get("export_links"):
            export_text = format_text_with_ia_highlighting("**Exportar dados:**")
            st.markdown(export_text)
            
            # Criar uma string HTML com todos os botões juntos
            buttons_html = '<div style="display: flex">'
            for link in tech_details["export_links"]:
                buttons_html += link
            buttons_html += '</div>'
            
            st.markdown(buttons_html, unsafe_allow_html=True)
        
        # Exibir detalhes técnicos se habilitado (UMA VEZ APENAS)
        if tech_details and tech_flag:
            expander_title = format_text_with_ia_highlighting("🔍 Detalhes Técnicos")
            with st.expander(expander_title):
                tech_content = create_tech_details_spoiler(tech_details)
                st.markdown(tech_content, unsafe_allow_html=True)


# utils.py - Atualize esta função
def create_tech_details_spoiler(tech_details: dict) -> str:
    """Cria o conteúdo do spoiler com detalhes técnicos"""
    if not tech_details:
        return ""
    content = format_text_with_ia_highlighting("### Detalhes Técnicos\n\n")
    
    # Performance e Timing (NOVO - Primeira seção)
    if tech_details.get("timing_info") or tech_details.get("total_duration"):
        content += format_text_with_ia_highlighting("**⏱️ Performance:**\n")
        total_duration = tech_details.get("total_duration", 0)
        content += format_text_with_ia_highlighting(f"- **Duração Total: {total_duration:.2f}ms**\n\n")
        timing_info = tech_details.get("timing_info", {})
        if timing_info:
            content += format_text_with_ia_highlighting("**📊 Detalhamento por Etapa:**\n")
            content += "| Etapa | Início | Duração (ms) |\n"
            content += "|-------|--------|-------------|\n"
            sorted_timings = sorted(timing_info.items(), key=lambda x: x[1].get('start', 0))
            for step_name, timing_data in sorted_timings:
                timestamp = timing_data.get('timestamp', 'N/A')
                duration = timing_data.get('duration', 0)
                if duration is not None:
                    if duration < 1000:
                        duration_formatted = f"{duration:.1f}ms"
                    else:
                        duration_formatted = f"{duration/1000:.2f}s"
                else:
                    duration_formatted = "Em andamento..."
                step_display_name = {
                    'processo_completo': '🔄 Processo Completo',
                    'verificacao_reuso': '🔍 Verificação de Reuso',
                    'processamento_reuso': '♻️ Processamento Reuso',
                    'processamento_nova_consulta': '🆕 Nova Consulta',
                    'preparando_conversa_gemini': '💬 Preparando Conversa',
                    'envio_gemini_inicial': '🚀 Envio Inicial Gemini',
                    'validacao_resposta_gemini': '✅ Validação Resposta',
                    'analise_tipo_resposta': '🔍 Análise Tipo Resposta',
                    'preparacao_parametros': '⚙️ Preparação Parâmetros',
                    'validacao_table_id': '🔒 Validação Table ID',
                    'construcao_query': '🔧 Construção Query',
                    'execucao_sql': '💾 Execução SQL',
                    'serializacao_dados': '📦 Serialização Dados',
                    'refinamento_gemini_final': '✨ Refinamento Final',
                    'refinamento_gemini_reuso': '✨ Refinamento Reuso',
                    'preparando_tech_details': '📋 Preparando Detalhes',
                    'finalizacao_reuso': '🏁 Finalização Reuso',
                    'salvamento_interacao': '💾 Salvamento',
                    'finalizacao_nova_consulta': '🏁 Finalização',
                    'exibindo_feedback_reuso': '💬 Feedback Reuso',
                    'preparando_dados_reuso': '📦 Preparando Dados Reuso'
                }.get(step_name, step_name.replace('_', ' ').title())
                content += f"| {step_display_name} | {timestamp} | {duration_formatted} |\n"
            content += "\n"

    # Prompt principal do FunctionDeclaration (SQL/RAG)
    if tech_details.get("optimized_prompt") or tech_details.get("prompt_tokens"):
        content += format_text_with_ia_highlighting("**📝 Prompt SQL/RAG (FunctionCall):**\n")
        if tech_details.get("optimized_prompt"):
            content += (
                "<details style='margin-bottom:8px;'><summary style='outline:none; cursor:pointer; color:#888; font-size:0.98em; font-weight:400; padding:2px 0;'>"
                "<span style='color:#888;'>Ver prompt SQL/RAG enviado ao modelo</span>"
                "</summary>\n"
                f"<pre style='font-size:0.93em;background:#23272e;color:#fff;padding:8px 10px;border-radius:6px;white-space:pre-wrap;line-height:1.5;overflow-x:auto;'>{tech_details['optimized_prompt']}</pre>\n"
                "</details>\n"
            )
        # Expander para rag_context
        if tech_details.get("rag_context_sent") or tech_details.get("rag_context"):
            rag_val = tech_details.get("rag_context_sent") or tech_details.get("rag_context")
            if rag_val:
                content += (
                    "<details style='margin-bottom:8px;'><summary style='outline:none; cursor:pointer; color:#888; font-size:0.98em; font-weight:400; padding:2px 0;'>"
                    "<span style='color:#888;'>Ver contexto RAG enviado</span>"
                    "</summary>\n"
                    f"<pre style='font-size:0.93em;background:#23272e;color:#fff;padding:8px 10px;border-radius:6px;white-space:pre-wrap;line-height:1.5;overflow-x:auto;'>{rag_val}</pre>\n"
                    "</details>\n"
                )
        # Expander para sql_guidance
        if tech_details.get("sql_guidance_sent") or tech_details.get("sql_guidance"):
            sql_val = tech_details.get("sql_guidance_sent") or tech_details.get("sql_guidance")
            if sql_val:
                content += (
                    "<details style='margin-bottom:8px;'><summary style='outline:none; cursor:pointer; color:#888; font-size:0.98em; font-weight:400; padding:2px 0;'>"
                    "<span style='color:#888;'>Ver orientações SQL enviadas</span>"
                    "</summary>\n"
                    f"<pre style='font-size:0.93em;background:#23272e;color:#fff;padding:8px 10px;border-radius:6px;white-space:pre-wrap;line-height:1.5;overflow-x:auto;'>{sql_val}</pre>\n"
                    "</details>\n"
                )
        # Tokens do FunctionCall
        prompt_tokens = tech_details.get("prompt_tokens")
        completion_tokens = tech_details.get("completion_tokens")
        total_tokens = tech_details.get("total_tokens")
        if prompt_tokens is not None or completion_tokens is not None or total_tokens is not None:
            content += format_text_with_ia_highlighting("**🔢 Tokens FunctionCall:**\n")
            if prompt_tokens is not None:
                content += f"- Prompt tokens: {prompt_tokens}\n"
            if completion_tokens is not None:
                content += f"- Completion tokens: {completion_tokens}\n"
            if total_tokens is not None:
                content += f"- Total tokens: {total_tokens}\n"
            content += "\n"

    # Prompt do refino/análise (analyze_data_with_gemini)
    if tech_details.get("analyze_prompt"):
        content += format_text_with_ia_highlighting("**📝 Prompt de Refino/Análise:**\n")
        content += (
            "<details style='margin-bottom:8px;'><summary style='outline:none; cursor:pointer; color:#888; font-size:0.98em; font-weight:400; padding:2px 0;'>"
            "<span style='color:#888;'>Ver prompt de análise/refino enviado ao modelo</span>"
            "</summary>\n"
            f"<pre style='font-size:0.93em;background:#23272e;color:#fff;padding:8px 10px;border-radius:6px;white-space:pre-wrap;line-height:1.5;overflow-x:auto;'>{tech_details['analyze_prompt']}</pre>\n"
            "</details>\n"
        )
        # Tokens do analyze/refino
        analyze_prompt_tokens = tech_details.get("analyze_prompt_tokens")
        analyze_completion_tokens = tech_details.get("analyze_completion_tokens")
        analyze_total_tokens = tech_details.get("analyze_total_tokens")
        if analyze_prompt_tokens is not None or analyze_completion_tokens is not None or analyze_total_tokens is not None:
            content += format_text_with_ia_highlighting("**🔢 Tokens Refino/Análise:**\n")
            if analyze_prompt_tokens is not None:
                content += f"- Prompt tokens: {analyze_prompt_tokens}\n"
            if analyze_completion_tokens is not None:
                content += f"- Completion tokens: {analyze_completion_tokens}\n"
            if analyze_total_tokens is not None:
                content += f"- Total tokens: {analyze_total_tokens}\n"
            content += "\n"
    
    # Árvore de decisão horizontal (caminho do fluxo)
    if tech_details.get("flow_path"):
        content += format_text_with_ia_highlighting("**🌳 Caminho de Decisão:**\n")
        content += f"```\n{tech_details['flow_path']}\n```\n\n"
    
    # Informações sobre reutilização de dados
    if tech_details.get("reuse_info"):
        reuse_info = tech_details["reuse_info"]
        if reuse_info.get("reused"):
            content += format_text_with_ia_highlighting("**🔄 Dados Reutilizados:**\n")
            content += format_text_with_ia_highlighting(f"- Motivo: {reuse_info.get('reason', 'N/A')}\n")
            content += format_text_with_ia_highlighting(f"- Consulta original: {reuse_info.get('original_prompt', 'N/A')}\n\n")
        else:
            content += format_text_with_ia_highlighting("**🆕 Nova Consulta Realizada**\n\n")
    
    if tech_details.get("function_params"):
        content += format_text_with_ia_highlighting("**Parâmetros da Função:**\n```json\n")
        serialized_params = serialize_params(tech_details["function_params"])
        content += json.dumps(serialized_params, indent=2, default=str)
        content += "\n```\n\n"
    
    if tech_details.get("query"):
        content += format_text_with_ia_highlighting("**Query SQL Executada:**\n```sql\n")
        content += tech_details["query"]
        content += "\n```\n\n"
    
    if tech_details.get("raw_data"):
        content += format_text_with_ia_highlighting("**Dados Brutos Recebidos:**\n")
        content += dict_to_markdown_table(tech_details["raw_data"][:5])  # Mostrar apenas 5 linhas
    
    if tech_details.get("chart_info"):
        content += format_text_with_ia_highlighting("\n**Informações do Gráfico:**\n")
        content += format_text_with_ia_highlighting(f"- Tipo: {tech_details['chart_info']['type']}\n")
        content += f"- Eixo X: {tech_details['chart_info']['x']}\n"
        content += f"- Eixo Y: {tech_details['chart_info']['y']}\n"
    
    # Adicionar informações de exportação
    if tech_details.get("export_info"):
        content += "\n**Informações de Exportação:**\n"
        for fmt, filename in tech_details["export_info"].items():
            content += f"- {fmt.upper()}: {filename}\n"
    
    # Aplica formatação IA para o conteúdo dos detalhes técnicos
    return format_text_with_ia_highlighting(content)


def safe_serialize_gemini_params(params):
    """
    Serializa parâmetros do Gemini para JSON, lidando com tipos complexos.
    """
    if params is None:
        return None
    
    # Handle FunctionCall objects specifically  
    if hasattr(params, 'name') and hasattr(params, 'args'):
        # É um FunctionCall, extrair apenas os args
        params = params.args
    
    if hasattr(params, "_values"):
        params = {k: v for k, v in params.items()}
    elif not isinstance(params, dict):
        try:
            params = dict(params)
        except:
            return {"serialized": str(params)}
    
    serializable = {}
    for k, v in params.items():
        try:
            json.dumps(v)
            serializable[k] = v
        except (TypeError, ValueError):
            serializable[k] = str(v)
    return serializable


def safe_serialize_data(data):
    """
    Serializa dados para JSON, convertendo tipos problemáticos.
    """
    if data is None:
        return None
    if isinstance(data, list):
        return [safe_serialize_data(item) for item in data]
    if isinstance(data, dict):
        serializable = {}
        for k, v in data.items():
            try:
                json.dumps(v)
                serializable[k] = v
            except (TypeError, ValueError):
                serializable[k] = str(v)
        return serializable
    try:
        json.dumps(data)
        return data
    except (TypeError, ValueError):
        return str(data)


def safe_serialize_tech_details(tech_details):
    """
    Serializa detalhes técnicos removendo objetos não serializáveis como Figure.
    """
    if not tech_details:
        return None
    
    # Copia o dicionário para não modificar o original
    safe_details = tech_details.copy()
    
    # Remove a figura do Plotly se existir (não é serializável)
    if safe_details.get("chart_info") and safe_details["chart_info"].get("fig"):
        # Mantém apenas os metadados do gráfico, remove a figura
        safe_details["chart_info"] = {
            "type": safe_details["chart_info"].get("type"),
            "x": safe_details["chart_info"].get("x"),
            "y": safe_details["chart_info"].get("y"),
            "color": safe_details["chart_info"].get("color")
        }
    
    # Serializa recursivamente outros campos
    return safe_serialize_data(safe_details)