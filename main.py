import streamlit as st
import os
import json
import traceback
from cache_db import save_interaction, log_error, get_user_history, get_interaction_full_data
from config import MAX_RATE_LIMIT, DATASET_ID, PROJECT_ID, TABLES_CONFIG, CLIENT_CONFIG, STANDARD_ERROR_MESSAGE, is_empresarial_mode

# DEVE SER O PRIMEIRO COMANDO STREAMLIT (após importações)
st.set_page_config(
    page_title=CLIENT_CONFIG.get("app_title", "Sistema de Análise de Dados"), 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Configura nome da página no menu lateral
if hasattr(st, '_set_page_label'):
    st._set_page_label("🤖 Agente")
else:
    # Workaround para versões antigas do Streamlit
    if 'page_label' not in st.session_state:
        st.session_state.page_label = "🤖 Agente"

from deepseek_theme import apply_deepseek_theme, create_usage_indicator, show_typing_animation, get_login_theme, get_chat_theme, render_theme_selector, apply_selected_theme, get_enhanced_cards_theme, get_expert_login_theme
from image_utils import get_background_style, get_login_background_style  # Importa utilitários de imagem
from gemini_handler import initialize_model, refine_with_gemini, should_reuse_data, initialize_rag_system
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

# Importações do sistema de autenticação e assinaturas DuckDB
from auth_system import render_auth_system, get_current_user
from user_database import db
from subscription_system_db import SubscriptionSystem
from config_menu import apply_user_preferences, initialize_user_config, check_feature_access


# Inicialização do sistema RAG (uma vez ao carregar a aplicação)
try:
    from gemini_handler import initialize_rag_system
    print("🚀 Inicializando sistema RAG...")
    initialize_rag_system()
    print("✅ Sistema RAG pronto!")
    rag_initialized = True
except Exception as e:
    print(f"❌ Erro ao inicializar sistema RAG: {e}")
    rag_initialized = False

# Inicialização do cache de logs/erros (garante criação das tabelas)
try:
    from cache_db import init_cache_db
    print("🔄 Inicializando cache_db...")
    init_cache_db()
    print("✅ cache_db inicializado!")
except Exception as e:
    print(f"❌ Erro ao inicializar cache_db: {e}")

# Configuração do rate limit (100 requisições por dia)
rate_limiter = RateLimiter(max_requests_per_day=MAX_RATE_LIMIT)

# Configuração inicial
SHOW_TECHNICAL_SPOILER = True  # Defina como True para mostrar detalhes técnicos

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    # Aplica tema de login sem mostrar código CSS
    st.markdown(get_expert_login_theme(), unsafe_allow_html=True)
    st.markdown(get_enhanced_cards_theme(), unsafe_allow_html=True)
    
    # Título simples sem container gigante
# Sistema de Autenticação
from auth_system import render_auth_system, get_current_user
from user_database import db

# Verifica autenticação
if not render_auth_system():
    st.stop()

# Usuário autenticado - inicializa configurações
current_user = get_current_user()
if current_user:
    st.session_state.user_email = current_user['email']
    initialize_user_config()
else:
    st.error("❌ Erro na autenticação")
    st.stop()
initialize_user_config()

# Inicializa sistema de assinatura
# Aplica preferências do usuário (incluindo tema)
apply_user_preferences()

# MENU SIDEBAR ÚNICO E LIMPO - SEM REDUNDÂNCIAS
with st.sidebar:
    # 1. CONFIGURAÇÕES (apenas tema)
    st.markdown("### ⚙️ Configurações")
    st.markdown("**🎨 Tema Visual**")
    render_theme_selector()
    apply_selected_theme()
    current_theme = st.session_state.get('theme_mode', 'escuro')
    st.caption(f"💡 Tema {current_theme} ativo")
    
    # 2. ASSINATURA (só no modo não empresarial)
    if not is_empresarial_mode():
        st.markdown("---")
        st.markdown("### 💳 Assinatura")
        
        current_user = get_current_user()
        if current_user:
            subscription_info = SubscriptionSystem.get_user_subscription_info(current_user['id'])
            
            # Mostra plano atual
            col1, col2 = st.columns([2, 1])
            with col1:
                st.write(f"**{subscription_info['name']}**")
                st.write(f"R$ {subscription_info['price']:.2f}/mês")
            with col2:
                if st.button("⚙️", key="manage_plan", help="Gerenciar plano"):
                    st.switch_page("pages/planos.py")
            
            # Botão de upgrade/planos
            if subscription_info['plan_id'] == 'free':
                if st.button("🚀 Fazer Upgrade", key="sidebar_upgrade", use_container_width=True):
                    st.switch_page("pages/planos.py")
            else:
                if st.button("💎 Ver Planos", key="sidebar_plans", use_container_width=True):
                    st.switch_page("pages/planos.py")

            # 3. USO DIÁRIO (só no modo não empresarial)
            st.markdown("### 📊 Uso Diário")
            current_usage_count = SubscriptionSystem.get_daily_usage(current_user['id'])
            st.markdown(create_usage_indicator(
                current_usage_count, 
                subscription_info['daily_limit'], 
                subscription_info
            ), unsafe_allow_html=True)
        else:
            st.error("❌ Sessão expirada. Faça login novamente.")
            st.stop()
    else:
        # Modo empresarial: apenas indicador discreto de uso
        st.markdown("---")
        st.markdown("### 📊 Uso Diário")
        current_user = get_current_user()
        if current_user:
            current_usage_count = SubscriptionSystem.get_daily_usage(current_user['id'])
            subscription_info = SubscriptionSystem.get_user_subscription_info(current_user['id'])
            st.write(f"**{current_usage_count} / {subscription_info['daily_limit']} consultas**")
            progress = min(current_usage_count / subscription_info['daily_limit'], 1.0)
            st.progress(progress)
        else:
            st.error("❌ Sessão expirada. Faça login novamente.")
            st.stop()
    
    # 4. USUÁRIO E LOGOUT
    st.markdown("---")
    current_user = get_current_user()
    if current_user:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"👤 **{current_user['username']}**")
        with col2:
            from auth_system import logout_user
            if st.button("🚪", key="unique_logout", help="Sair"):
                logout_user()
    else:
        st.error("❌ Sessão expirada. Faça login novamente.")
        st.stop()

# Container principal para todo o conteúdo do CHAT
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
            - {limitations.get("data_freshness", "Resultados são baseados nos dados mais recentes disponíveis.")}"""
        
        # Adiciona limite apenas no modo não empresarial
        if not is_empresarial_mode():
            limitations_text += f"\n            - **Limite diário de {CLIENT_CONFIG.get('rate_limit_description', 'requisições')}: {MAX_RATE_LIMIT}**. Se atingido, você receberá uma mensagem de aviso."
        
        # Adiciona informação sobre sistema RAG se disponível
        if rag_initialized:
            limitations_text += "\n🧠 **Sistema RAG Ativo**: Otimização inteligente de tokens para reduzir custos em 80%+"
        
        limitations_text += "\n> Para detalhes técnicos, consulte a documentação ou o spoiler abaixo."
        
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
    from utils import show_aggrid_table
    for msg in st.session_state.chat_history:
        tech = msg.get("tech_details")
        with st.container():
            # Exibe o texto limpo primeiro (sem instruções técnicas, sem gráfico embutido)
            content = msg["content"]
            for marker in ["GRAPH-TYPE:", "EXPORT-INFO:", "dt:"]:
                if marker in content:
                    content = content.split(marker)[0].strip()
            display_message_with_spoiler(
                msg["role"], content, None, False
            )
            # Exibe AgGrid logo após o texto, se houver dados válidos
            if tech and tech.get("aggrid_data"):
                aggrid_data = tech["aggrid_data"]
                if isinstance(aggrid_data, list) and len(aggrid_data) > 0 and isinstance(aggrid_data[0], dict):
                    st.markdown("<div style='margin-top:0.5em; margin-bottom:0.5em;'></div>", unsafe_allow_html=True)
                    show_aggrid_table(aggrid_data, theme="balham", height=350, fit_columns=True)
            
            # Exibe gráfico após grid
            if tech and tech.get("chart_info") and tech["chart_info"].get("fig"):
                import plotly.graph_objs as go
                fig = go.Figure(tech["chart_info"]["fig"])
                st.markdown("<div style='margin-top:0.5em; margin-bottom:0.5em;'></div>", unsafe_allow_html=True)
                # Garante que o gráfico ocupe todo o espaço horizontal do container
                st.plotly_chart(
                    fig,
                    use_container_width=True,
                    key=f"fig_{id(fig)}",
                    config={
                        'displayModeBar': False,
                        'responsive': True,
                        'staticPlot': False
                    }
                )
            # Exibe detalhes técnicos por último, sempre após texto, grid e gráfico
            if tech and SHOW_TECHNICAL_SPOILER:
                from utils import create_tech_details_spoiler
                expander_title = format_text_with_ia_highlighting("🔍 Detalhes Técnicos")
                with st.expander(expander_title):
                    tech_content = create_tech_details_spoiler(tech)
                    st.markdown(tech_content, unsafe_allow_html=True)

# Container fixo para o input (fora do content-container)
prompt = st.chat_input(format_text_with_ia_highlighting("Faça sua pergunta..."), key="mobile_input")

# Captura novo input
if prompt:
    # Verifica permissão para nova query
    current_user = get_current_user()
    if current_user:
        if is_empresarial_mode():
            # Modo empresarial: verifica limite mas não mostra planos
            can_proceed, message = SubscriptionSystem.check_query_permission(current_user['id'])
            if not can_proceed:
                st.warning("⚠️ Limite diário de consultas atingido. Tente novamente amanhã.")
                st.stop()
            # Incrementa uso do usuário
            SubscriptionSystem.increment_user_usage(current_user['id'])
        else:
            # Modo normal: verifica limite e oferece upgrade
            can_proceed, message = SubscriptionSystem.check_query_permission(current_user['id'])
            
            if not can_proceed:
                st.warning(message)
                if st.button("💎 Ver Planos", key="upgrade_from_chat"):
                    st.switch_page("pages/planos.py")
                st.stop()
            
            # Incrementa uso do usuário
            SubscriptionSystem.increment_user_usage(current_user['id'])
    else:
        st.error("❌ Usuário não autenticado")
        st.stop()
    
    # Adiciona a pergunta ao histórico
    st.session_state.chat_history.append({"role": "user", "content": prompt})

    # Mostra animação de typing
    with st.chat_message("assistant"):
        typing_placeholder = st.empty()
        typing_placeholder.markdown(show_typing_animation(), unsafe_allow_html=True)

    # Processa a mensagem usando o handler limpo
    from message_handler import MessageHandler
    handler = MessageHandler(st.session_state.model, rate_limiter, current_user['email'])
    handler.process_message(prompt, typing_placeholder)

