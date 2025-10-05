import streamlit as st
import os
import json
import traceback
from cache_db import save_interaction, log_error, get_user_history, get_interaction_full_data
from config import MAX_RATE_LIMIT, DATASET_ID, PROJECT_ID, TABLES_CONFIG, CLIENT_CONFIG, STANDARD_ERROR_MESSAGE

# DEVE SER O PRIMEIRO COMANDO STREAMLIT (após importações)
st.set_page_config(
    page_title=CLIENT_CONFIG.get("app_title", "Sistema de Análise de Dados"), 
    layout="wide",
    initial_sidebar_state="expanded"
)

from style import MOBILE_IFRAME_CHAT
from deepseek_theme import apply_deepseek_theme, create_usage_indicator, show_typing_animation, get_login_theme, get_chat_theme, render_theme_selector, apply_selected_theme
from image_utils import get_background_style, get_login_background_style  # Importa utilitários de imagem
from gemini_handler import initialize_model, refine_with_gemini, should_reuse_data
from database import build_query, execute_query
from utils import (
    display_message_with_spoiler, 
    slugfy_response, 
    safe_serialize_gemini_params, 
    safe_serialize_data, 
    safe_serialize_tech_details,
    format_text_with_ia_highlighting
)
from rate_limit import RateLimiter
from logger import log_interaction

# Configuração do rate limit (100 requisições por dia)
rate_limiter = RateLimiter(max_requests_per_day=MAX_RATE_LIMIT)

# Configuração inicial
SHOW_TECHNICAL_SPOILER = True  # Defina como True para mostrar detalhes técnicos

# Carrega as credenciais do arquivo
with open(os.path.join(os.path.dirname(__file__), "credentials.json"), "r") as f:
    creds = json.load(f)

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    # Aplica tema de login sem mostrar código CSS
    st.markdown(get_login_theme(), unsafe_allow_html=True)
    
    # Título simples sem container gigante
    st.markdown("<h1 style='text-align: center; color: #00d4ff; font-size: 2.5rem; margin: 2rem 0;'>ViaQuest</h1>", unsafe_allow_html=True)
    
    st.markdown("### 🔐 Acesso ao Sistema")
    st.markdown("Faça login para acessar o sistema de análise de dados inteligente.")
    
    login = st.text_input("📧 E-mail", value="", key="login_input")
    password = st.text_input("🔑 Senha", type="password", key="password_input")
    
    if st.button("🚀 Entrar", use_container_width=True):
        if login == creds["login"] and password == creds["password"]:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("❌ Usuário ou senha inválidos.")
    st.stop()

# Seletor de tema no sidebar
theme_mode = render_theme_selector()

# Aplica o tema
apply_selected_theme(theme_mode)

# Indicador de uso no estilo DeepSeek
usage_data = rate_limiter.get_current_usage()
st.markdown(create_usage_indicator(usage_data['current'], usage_data['max']), unsafe_allow_html=True)

# Container principal para todo o conteúdo
with st.container():
    
    # Título principal com tema DeepSeek
    title_text = CLIENT_CONFIG.get("app_title", "Sistema de Análise de Dados")
    formatted_title = format_text_with_ia_highlighting(title_text)
    st.markdown(f"# {formatted_title}", unsafe_allow_html=True)

    with st.expander("⚠️ Limitações e Regras do Assistente (clique para ver)", expanded=False):
        limitations = CLIENT_CONFIG.get("limitations", {})
        limitations_text = f"""
            - {limitations.get("data_access", "Este assistente só pode consultar as tabelas configuradas no sistema.")}
            - {limitations.get("cross_reference", "Não é possível acessar ou cruzar dados de outras tabelas ou fontes externas.")}
            - {limitations.get("single_query", "Apenas uma consulta por vez é permitida.")}
            - {limitations.get("temporal_comparisons", "Para comparações temporais, utilize perguntas claras.")}
            - {limitations.get("model_understanding", "O modelo pode não compreender perguntas muito vagas.")}
            - {limitations.get("data_freshness", "Resultados são baseados nos dados mais recentes disponíveis.")}
            - **Limite diário de {CLIENT_CONFIG.get('rate_limit_description', 'requisições')}: {MAX_RATE_LIMIT}**. Se atingido, você receberá uma mensagem de aviso.
            > Para detalhes técnicos, consulte a documentação ou o spoiler abaixo.
            """
        # Aplica formatação IA para as limitações
        formatted_limitations = format_text_with_ia_highlighting(limitations_text)
        st.markdown(formatted_limitations, unsafe_allow_html=True)

    # Exemplos de perguntas (configuráveis)
    if "chat_history" not in st.session_state or len(st.session_state.chat_history) == 0:
        business_domain = CLIENT_CONFIG.get("business_domain", "dados")
        examples_intro = f"Faça perguntas sobre {business_domain}. Exemplos:"
        # Aplica formatação IA para a introdução dos exemplos
        formatted_intro = format_text_with_ia_highlighting(examples_intro)
        st.markdown(formatted_intro, unsafe_allow_html=True)
        
        examples = CLIENT_CONFIG.get("examples", ["- Exemplo de pergunta"])
        examples_text = "\n".join(examples)
        # Aplica formatação IA também nos exemplos
        formatted_examples = format_text_with_ia_highlighting(examples_text)
        st.code(formatted_examples)

    # Inicialização do modelo e estado da sessão
    if "model" not in st.session_state:
        st.session_state.model = initialize_model()

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Inicializa variáveis de sessão para armazenar os dados (isolamento multi-usuário)
    if "current_interaction" not in st.session_state:
        st.session_state.current_interaction = {
            "refined_response": None,
            "serializable_params": None,
            "serializable_data": None,
            "tech_details": None,
            "query": None,
            "raw_response": None
        }

    # Exibe o histórico de chat
    for msg in st.session_state.chat_history:
        display_message_with_spoiler(
            msg["role"], msg["content"], msg.get("tech_details"), SHOW_TECHNICAL_SPOILER
        )

# Container fixo para o input (fora do content-container)
st.markdown('<div class="fixed-bottom">', unsafe_allow_html=True)
prompt = st.chat_input(format_text_with_ia_highlighting("Faça sua pergunta..."), key="mobile_input")
st.markdown('</div>', unsafe_allow_html=True)

# Captura novo input
if prompt:
    # Verifica o rate limit antes de processar
    if rate_limiter.check_limit():
        limit_msg = format_text_with_ia_highlighting("Limite diário de requisições atingido. Tente novamente amanhã.")
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": limit_msg
        })
        st.rerun()
    else:
        # Incrementa o contador
        rate_limiter.increment()
        # Adiciona a pergunta ao histórico
        st.session_state.chat_history.append({"role": "user", "content": prompt})

        # Mostra animação de typing
        with st.chat_message("assistant"):
            typing_placeholder = st.empty()
            typing_placeholder.markdown(show_typing_animation(), unsafe_allow_html=True)

        # Processa a mensagem usando o handler limpo
        from message_handler import MessageHandler
        handler = MessageHandler(st.session_state.model, rate_limiter, creds["login"])
        handler.process_message(prompt, typing_placeholder)

