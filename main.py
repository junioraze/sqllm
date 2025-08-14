import streamlit as st
import os
import json
import traceback
from cache_db import save_interaction, log_error, get_user_history, get_interaction_full_data
from config import MAX_RATE_LIMIT, DATASET_ID, PROJECT_ID, TABLES_CONFIG, CLIENT_CONFIG  # Importa a configuração do assistente

# Mensagem padrão para erros (nunca mostrar detalhes técnicos ao usuário)
STANDARD_ERROR_MESSAGE = CLIENT_CONFIG.get("error_message", "Não foi possível processar sua solicitação no momento. Nossa equipe técnica foi notificada e está analisando a situação. Tente reformular sua pergunta ou entre em contato conosco.")

# DEVE SER O PRIMEIRO COMANDO STREAMLIT (após importações)
st.set_page_config(
    page_title=CLIENT_CONFIG.get("app_title", "Sistema de Análise de Dados"), 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# FORÇA TEMA LIGHT SEMPRE (equivalente ao menu hambúrguer > Settings > Theme > Light)
st.markdown("""
<script>
    // Força o tema light programaticamente
    setTimeout(function() {
        const iframe = window.parent.document.querySelector('iframe[title="streamlit_app"]');
        const doc = iframe ? iframe.contentDocument || iframe.contentWindow.document : document;
        
        // Remove o tema dark se estiver aplicado
        const stApp = doc.querySelector('.stApp');
        if (stApp) {
            stApp.classList.remove('dark');
            stApp.classList.add('light');
        }
        
        // Força as variáveis CSS do tema light
        const root = doc.documentElement;
        if (root) {
            root.style.setProperty('--primary-color', '#ff6b35');
            root.style.setProperty('--background-color', '#ffffff');
            root.style.setProperty('--secondary-background-color', '#f0f2f6');
            root.style.setProperty('--text-color', '#093374');
        }
    }, 100);
</script>
""", unsafe_allow_html=True)

from style import MOBILE_IFRAME_BASE  # Importa o módulo de estilos
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
    # Aplica estilos específicos para a tela de login
    st.markdown(get_login_background_style(), unsafe_allow_html=True)
    
    # Adiciona a imagem de logo/descrição
    try:
        st.image("etc/desc_logo.jpg", use_container_width=True, output_format="auto")
    except:
        # Se não conseguir carregar a imagem, continua sem ela
        pass
    
    # Título de login com IA destacado - USANDO MARKDOWN PURO
    login_title = f"Login {CLIENT_CONFIG.get('app_subtitle', 'Sistema de Análise')}"
    formatted_login_title = format_text_with_ia_highlighting(login_title)
    st.markdown(f"# {formatted_login_title}", unsafe_allow_html=True)
    
    # CSS para campos de login e preservação de cores IA
    st.markdown("""
    <style>
    /* TÍTULO DE LOGIN CENTRALIZADO */
    .stApp h1 {
        text-align: center !important;
        color: #093374 !important;
    }
    
    /* Labels dos campos de login */
    .stTextInput > label {
        color: #093374 !important;
        font-weight: 600 !important;
    }
    
    /* Campos de input */
    .stTextInput > div > div > input {
        border-color: #093374 !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #ff6b35 !important;
        box-shadow: 0 0 0 1px #ff6b35 !important;
    }
    
    /* FORÇA TEXTO AZUL EM TÍTULOS E CORPO */
    h1, p, div, body {
        color: #093374 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    login = st.text_input(format_text_with_ia_highlighting("E-mail"), value="", key="login_input")
    password = st.text_input(format_text_with_ia_highlighting("Senha"), type="password", key="password_input")
    if st.button("Entrar"):
        if login == creds["login"] and password == creds["password"]:
            st.session_state.authenticated = True
            st.rerun()
        else:
            error_msg = format_text_with_ia_highlighting("Usuário ou senha inválidos.")
            st.error(error_msg)
    st.stop()

# Aplica o fundo personalizado para o chatbot (somente após login)
st.markdown(MOBILE_IFRAME_BASE, unsafe_allow_html=True)
st.markdown(get_background_style(), unsafe_allow_html=True)

# CSS FINAL - DEPOIS DE TODOS OS OUTROS CSS PARA GARANTIR PRIORIDADE ABSOLUTA
st.markdown("""
<style>
/* CORES FINAIS COM MÁXIMA ESPECIFICIDADE - FORÇA AZUL */
.stApp h1, .stApp h2, .stApp h3, .stApp p, .stApp div, 
.stApp span, .stApp li, .stApp ul, .stApp ol, .stApp strong, .stApp em,
.main h1, .main h2, .main h3, .main p, .main div,
.main span, .main li, .main ul, .main ol, .main strong, .main em {
    color: #093374 !important;
}

/* CHAT - USUÁRIO LARANJA, ASSISTENTE AZUL COM ESPECIFICIDADE MÁXIMA */
.stApp .stChatMessage[data-testid="chat-message-user"] *,
.stApp .stChatMessage[data-testid="chat-message-user"] p,
.stApp .stChatMessage[data-testid="chat-message-user"] div,
.stApp .stChatMessage[data-testid="chat-message-user"] span {
    color: #ff6b35 !important;
}

.stApp .stChatMessage[data-testid="chat-message-assistant"] *,
.stApp .stChatMessage[data-testid="chat-message-assistant"] p,
.stApp .stChatMessage[data-testid="chat-message-assistant"] div,
.stApp .stChatMessage[data-testid="chat-message-assistant"] span {
    color: #093374 !important;
}

/* EXPANSORES COM ESPECIFICIDADE MÁXIMA */
.stApp .streamlit-expanderHeader *,
.stApp .streamlit-expanderContent *,
.stApp .stExpander * {
    color: #093374 !important;
}

/* CÓDIGO COM ESPECIFICIDADE MÁXIMA */
.stApp .stCode *,
.stApp .stCode pre,
.stApp .stCode code {
    color: #093374 !important;
}

/* PRESERVA SPANS IA EM LARANJA COM ESPECIFICIDADE MÁXIMA */
.stApp h1 span[style*="color: #ff6b35"],
.stApp h1 span[style*="color:#ff6b35"],
.stApp h2 span[style*="color: #ff6b35"],
.stApp h2 span[style*="color:#ff6b35"],
.stApp h3 span[style*="color: #ff6b35"],
.stApp h3 span[style*="color:#ff6b35"],
.stApp p span[style*="color: #ff6b35"],
.stApp p span[style*="color:#ff6b35"],
.stApp div span[style*="color: #ff6b35"],
.stApp div span[style*="color:#ff6b35"],
.stApp .streamlit-expanderContent span[style*="color: #ff6b35"],
.stApp .streamlit-expanderContent span[style*="color:#ff6b35"],
.stApp .streamlit-expanderHeader span[style*="color: #ff6b35"],
.stApp .streamlit-expanderHeader span[style*="color:#ff6b35"],
.stApp .stExpander span[style*="color: #ff6b35"],
.stApp .stExpander span[style*="color:#ff6b35"],
.stApp .stCode span[style*="color: #ff6b35"],
.stApp .stCode span[style*="color:#ff6b35"],
.stApp .stChatMessage[data-testid="chat-message-assistant"] span[style*="color: #ff6b35"],
.stApp .stChatMessage[data-testid="chat-message-assistant"] span[style*="color:#ff6b35"],
.stApp .stChatMessage[data-testid="chat-message-user"] span[style*="color: #ff6b35"],
.stApp .stChatMessage[data-testid="chat-message-user"] span[style*="color:#ff6b35"],
.main h1 span[style*="color: #ff6b35"],
.main h1 span[style*="color:#ff6b35"],
.main h2 span[style*="color: #ff6b35"],
.main h2 span[style*="color:#ff6b35"],
.main h3 span[style*="color: #ff6b35"],
.main h3 span[style*="color:#ff6b35"],
.main p span[style*="color: #ff6b35"],
.main p span[style*="color:#ff6b35"],
.main div span[style*="color: #ff6b35"],
.main div span[style*="color:#ff6b35"],
/* FORÇA SPANS IA COM MAIS ESPECIFICIDADE AINDA */
span[style*="color: #ff6b35; font-weight: bold;"],
span[style*="color:#ff6b35;font-weight:bold;"],
*[style*="color: #ff6b35; font-weight: bold;"],
*[style*="color:#ff6b35;font-weight:bold;"] {
    color: #ff6b35 !important;
    font-weight: bold !important;
}

/* CHAT INPUT - COR VERMELHA COMBINANDO COM O TEMA */
.stApp .stChatInput > div > div {
    background-color: #d32f2f !important; /* Vermelho que combina com as cores */
    border: 1px solid #b71c1c !important;
    border-radius: 8px !important;
}

.stApp .stChatInput textarea {
    background-color: #d32f2f !important;
    border: none !important;
    color: #ffffff !important; /* Texto branco que o usuário digita */
    font-weight: 500 !important;
}

.stApp .stChatInput textarea::placeholder {
    color: #ffffff !important; /* Placeholder branco */
    opacity: 0.9 !important;
}

.stApp .stChatInput textarea:focus {
    border: none !important;
    outline: none !important;
    box-shadow: 0 0 0 2px #ff6b35 !important; /* Foco laranja */
}

/* BOTÃO ENVIAR DO CHAT */
.stApp .stChatInput button {
    background-color: #ff6b35 !important;
    border: none !important;
    color: #ffffff !important;
}

.stApp .stChatInput button:hover {
    background-color: #e55a2b !important;
}
</style>
""", unsafe_allow_html=True)

# Container principal para todo o conteúdo
with st.container():
    
    # Título principal com IA destacado - USANDO MARKDOWN PURO
    title_text = CLIENT_CONFIG.get("app_title", "Sistema de Análise de Dados")
    formatted_title = format_text_with_ia_highlighting(title_text)
    st.markdown(f"# {formatted_title}", unsafe_allow_html=True)

    # CSS FINAL - DEPOIS DE TODOS OS OUTROS CSS PARA GARANTIR PRIORIDADE ABSOLUTA
    st.markdown("""
    <style>
    /* TÍTULO CENTRALIZADO */
    .stApp h1 {
        text-align: center !important;
        margin-bottom: 2rem !important;
    }
    
    /* CORES FINAIS COM MÁXIMA ESPECIFICIDADE - FORÇA AZUL */
    .stApp h1, .stApp h2, .stApp h3, .stApp p, .stApp div, 
    .stApp span, .stApp li, .stApp ul, .stApp ol, .stApp strong, .stApp em,
    .main h1, .main h2, .main h3, .main p, .main div,
    .main span, .main li, .main ul, .main ol, .main strong, .main em {
        color: #093374 !important;
    }

    /* CHAT - USUÁRIO LARANJA, ASSISTENTE AZUL COM ESPECIFICIDADE MÁXIMA */
    .stApp .stChatMessage[data-testid="chat-message-user"] *,
    .stApp .stChatMessage[data-testid="chat-message-user"] p,
    .stApp .stChatMessage[data-testid="chat-message-user"] div,
    .stApp .stChatMessage[data-testid="chat-message-user"] span {
        color: #ff6b35 !important;
    }

    .stApp .stChatMessage[data-testid="chat-message-assistant"] *,
    .stApp .stChatMessage[data-testid="chat-message-assistant"] p,
    .stApp .stChatMessage[data-testid="chat-message-assistant"] div,
    .stApp .stChatMessage[data-testid="chat-message-assistant"] span {
        color: #093374 !important;
    }

    /* EXPANSORES COM ESPECIFICIDADE MÁXIMA */
    .stApp .streamlit-expanderHeader *,
    .stApp .streamlit-expanderContent *,
    .stApp .stExpander * {
        color: #093374 !important;
    }

    /* CÓDIGO COM ESPECIFICIDADE MÁXIMA */
    .stApp .stCode *,
    .stApp .stCode pre,
    .stApp .stCode code {
        color: #093374 !important;
    }
    
    /* PRESERVA SPANS IA EM LARANJA - SEGUNDO BLOCO */
    .stApp h1 span[style*="color: #ff6b35"],
    .stApp h1 span[style*="color:#ff6b35"],
    .stApp h2 span[style*="color: #ff6b35"],
    .stApp h2 span[style*="color:#ff6b35"],
    .stApp h3 span[style*="color: #ff6b35"],
    .stApp h3 span[style*="color:#ff6b35"],
    .stApp p span[style*="color: #ff6b35"],
    .stApp p span[style*="color:#ff6b35"],
    .stApp div span[style*="color: #ff6b35"],
    .stApp div span[style*="color:#ff6b35"],
    .stApp .streamlit-expanderContent span[style*="color: #ff6b35"],
    .stApp .streamlit-expanderContent span[style*="color:#ff6b35"],
    .stApp .streamlit-expanderHeader span[style*="color: #ff6b35"],
    .stApp .streamlit-expanderHeader span[style*="color:#ff6b35"],
    .stApp .stExpander span[style*="color: #ff6b35"],
    .stApp .stExpander span[style*="color:#ff6b35"],
    .stApp .stCode span[style*="color: #ff6b35"],
    .stApp .stCode span[style*="color:#ff6b35"],
    .stApp .stChatMessage span[style*="color: #ff6b35"],
    .stApp .stChatMessage span[style*="color:#ff6b35"],
    span[style*="color: #ff6b35; font-weight: bold;"],
    span[style*="color:#ff6b35;font-weight:bold;"],
    *[style*="color: #ff6b35; font-weight: bold;"],
    *[style*="color:#ff6b35;font-weight:bold;"] {
        color: #ff6b35 !important;
        font-weight: bold !important;
    }

    /* CHAT INPUT - REPETIDO PARA GARANTIA */
    .stApp .stChatInput > div > div {
        background-color: #d32f2f !important;
        border: 1px solid #b71c1c !important;
        border-radius: 8px !important;
    }

    .stApp .stChatInput textarea {
        background-color: #d32f2f !important;
        border: none !important;
        color: #ffffff !important;
        font-weight: 500 !important;
    }

    .stApp .stChatInput textarea::placeholder {
        color: #ffffff !important;
        opacity: 0.9 !important;
    }

    .stApp .stChatInput textarea:focus {
        border: none !important;
        outline: none !important;
        box-shadow: 0 0 0 2px #ff6b35 !important;
    }

    .stApp .stChatInput button {
        background-color: #ff6b35 !important;
        border: none !important;
        color: #ffffff !important;
    }

    .stApp .stChatInput button:hover {
        background-color: #e55a2b !important;
    }
    </style>
    """, unsafe_allow_html=True)

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

        try:
            # Limpa o estado da interação anterior para evitar contaminação
            st.session_state.current_interaction = {
                "refined_response": None,
                "serializable_params": None,
                "serializable_data": None,
                "tech_details": None,
                "query": None,
                "raw_response": None
            }
            
            # Busca histórico do usuário para contexto na decisão de reutilização
            user_history = get_user_history(creds["login"])
            
            # Verifica se deve reutilizar dados usando inteligência do Gemini
            # O Gemini analisa o contexto completo e decide se os dados existentes são suficientes
            should_reuse = False
            if user_history:  # Só verifica reutilização se houver histórico
                reuse_decision = should_reuse_data(
                    st.session_state.model,
                    prompt,
                    user_history
                )
                should_reuse = reuse_decision.get("should_reuse", False)
            
            if should_reuse:
                # Reutiliza dados baseado na decisão do Gemini - busca dados completos pelo ID
                with st.spinner("Processando com dados anteriores..."):
                    # Busca o ID da interação a ser reutilizada
                    interaction_id = reuse_decision.get("interaction_id")
                    
                    if interaction_id:
                        # Busca os dados completos da interação específica
                        full_data = get_interaction_full_data(interaction_id)
                        if full_data:
                            st.session_state.current_interaction["serializable_data"] = safe_serialize_data(full_data)
                            # Busca metadados da interação para o refine_with_gemini
                            reused_interaction = next((item for item in user_history if item.get('id') == interaction_id), None)
                            reused_params = reused_interaction.get('function_params') if reused_interaction else None
                            reused_query = reused_interaction.get('query_sql') if reused_interaction else None
                        else:
                            # Se não encontrar dados, força nova consulta
                            should_reuse = False
                    else:
                        # Se não tiver ID, força nova consulta
                        should_reuse = False
                    
                    if should_reuse:  # Verifica novamente após validações
                        st.session_state.current_interaction["refined_response"], st.session_state.current_interaction["tech_details"] = refine_with_gemini(
                            prompt,
                            st.session_state.current_interaction["serializable_data"],
                            reused_params,
                            reused_query,
                        )
                        
                        # Adiciona informação sobre reutilização nos detalhes técnicos
                        if st.session_state.current_interaction["tech_details"]:
                            st.session_state.current_interaction["tech_details"]["reuse_info"] = {
                                "reused": True,
                                "reason": reuse_decision.get("reason", "Decisão inteligente do Gemini"),
                                "original_prompt": reused_interaction.get('user_prompt') if reused_interaction else "N/A",
                                "interaction_id": interaction_id
                            }

                        # Atualiza o histórico
                        st.session_state.chat_history.append(
                            {
                                "role": "assistant",
                                "content": format_text_with_ia_highlighting(st.session_state.current_interaction["refined_response"]),
                                "tech_details": st.session_state.current_interaction["tech_details"],
                            }
                        )

                        # Salva a interação de reutilização no cache
                        try:
                            save_interaction(
                                user_id=creds["login"],
                                question=prompt,
                                function_params=safe_serialize_gemini_params(reused_params),
                                query_sql=reused_query,
                                raw_data=st.session_state.current_interaction["serializable_data"],
                                raw_response=None,
                                refined_response=st.session_state.current_interaction["refined_response"],
                                tech_details=safe_serialize_tech_details(st.session_state.current_interaction["tech_details"]),
                                status="OK",
                                reused_from=reused_interaction.get('user_prompt') if reused_interaction else "N/A"
                            )
                        except Exception as cache_error:
                            print(f"Erro ao salvar no cache (reutilização): {cache_error}")
                            
            if not should_reuse:
                # Processa uma nova consulta
                convo = st.session_state.model.start_chat(
                    history=[
                        {"role": m["role"], "parts": [m["content"]]}
                        for m in st.session_state.chat_history
                        if m["role"] != "assistant" or not m.get("tech_details")
                    ]
                )

                # Mostra que está processando
                processing_msg = st.empty()
                processing_msg.chat_message("assistant").markdown(
                    format_text_with_ia_highlighting("Processando sua solicitação...")
                )

                response = convo.send_message(prompt)

                # Verifica se há chamada de função
                if (
                    response.candidates
                    and response.candidates[0].content.parts[0].function_call
                ):
                        function_call = response.candidates[0].content.parts[0].function_call
                        params = function_call.args

                        # Serialização SEGURA dos parâmetros usando função especializada
                        st.session_state.current_interaction["serializable_params"] = safe_serialize_gemini_params(params)

                        # Obter e validar o full_table_id
                        full_table_id = st.session_state.current_interaction["serializable_params"].get("full_table_id")
                        if not full_table_id:
                            # NUNCA mostrar erro técnico ao usuário - salvar no BigQuery e DuckDB para análise
                            error_details = f"Missing full_table_id in parameters: {st.session_state.current_interaction['serializable_params']}"
                            
                            # Log no BigQuery (para controle geral)
                            log_interaction(
                                user_input=prompt,
                                function_params=st.session_state.current_interaction["serializable_params"],
                                query=None,
                                raw_data=None,
                                raw_response=None,
                                refined_response=STANDARD_ERROR_MESSAGE,
                                first_ten_table_lines=None,
                                graph_data=None,
                                export_data=None,
                                status="ERROR",
                                status_msg=error_details,
                                client_request_count=rate_limiter.state["count"],
                                custom_fields={
                                    "error_type": "missing_full_table_id",
                                    "function_params": st.session_state.current_interaction["serializable_params"]
                                }
                            )
                            
                            # Log específico de erro no DuckDB (para análise detalhada)
                            log_error(
                                user_id=creds["login"],
                                error_type="missing_full_table_id",
                                error_message=error_details,
                                context=f"User request: {prompt} | Function params: {json.dumps(st.session_state.current_interaction['serializable_params'])}",
                                traceback=None
                            )
                            
                            st.session_state.chat_history.append(
                                {"role": "assistant", "content": format_text_with_ia_highlighting(STANDARD_ERROR_MESSAGE)}
                            )
                            st.rerun()

                        # Validar se o full_table_id é válido (formato correto)
                        expected_full_table_ids = [f"{PROJECT_ID}.{DATASET_ID}.{table_name}" for table_name in TABLES_CONFIG.keys()]
                        if full_table_id not in expected_full_table_ids:
                            # NUNCA mostrar erro técnico ao usuário - salvar no BigQuery e DuckDB para análise
                            error_details = f"Invalid full_table_id: {full_table_id} | Available tables: {expected_full_table_ids}"
                            
                            # Log no BigQuery (para controle geral)
                            log_interaction(
                                user_input=prompt,
                                function_params=st.session_state.current_interaction["serializable_params"],
                                query=None,
                                raw_data=None,
                                raw_response=None,
                                refined_response=STANDARD_ERROR_MESSAGE,
                                first_ten_table_lines=None,
                                graph_data=None,
                                export_data=None,
                                status="ERROR",
                                status_msg=error_details,
                                client_request_count=rate_limiter.state["count"],
                                custom_fields={
                                    "error_type": "invalid_full_table_id",
                                    "requested_full_table_id": full_table_id,
                                    "available_full_table_ids": expected_full_table_ids
                                }
                            )
                            
                            # Log específico de erro no DuckDB (para análise detalhada)
                            log_error(
                                user_id=creds["login"],
                                error_type="invalid_full_table_id",
                                error_message=error_details,
                                context=f"User request: {prompt} | Function params: {json.dumps(st.session_state.current_interaction['serializable_params'])}",
                                traceback=None
                            )
                            
                            st.session_state.chat_history.append(
                                {"role": "assistant", "content": format_text_with_ia_highlighting(STANDARD_ERROR_MESSAGE)}
                            )
                            st.rerun()
                        
                        # Construir e executar query
                        st.session_state.current_interaction["query"] = build_query(st.session_state.current_interaction["serializable_params"])
                        raw_data = execute_query(st.session_state.current_interaction["query"])

                        if "error" in raw_data:
                            # NUNCA mostrar erro técnico ao usuário - salvar no BigQuery e DuckDB para análise
                            error_details = f"Query Error: {raw_data['error']}"
                            failed_query = raw_data.get('query', 'N/A')
                            
                            # Log no BigQuery (para controle geral)
                            log_interaction(
                                user_input=prompt,
                                function_params=st.session_state.current_interaction["serializable_params"],
                                query=st.session_state.current_interaction["query"] if st.session_state.current_interaction["query"] else None,
                                raw_data=None,
                                raw_response=None,
                                refined_response=STANDARD_ERROR_MESSAGE,
                                first_ten_table_lines=None,
                                graph_data=None,
                                export_data=None,
                                status="ERROR",
                                status_msg=f"{error_details} | Query: {failed_query}",
                                client_request_count=rate_limiter.state["count"],
                                custom_fields={
                                    "error_type": "query_execution_error",
                                    "error_details": raw_data['error'],
                                    "failed_query": failed_query
                                }
                            )
                            
                            # Log específico de erro no DuckDB (para análise detalhada)
                            log_error(
                                user_id=creds["login"],
                                error_type="query_execution_error",
                                error_message=error_details,
                                context=f"User request: {prompt} | Failed Query: {failed_query} | Function params: {json.dumps(st.session_state.current_interaction['serializable_params'])}",
                                traceback=raw_data['error']
                            )
                            
                            st.session_state.chat_history.append(
                                {
                                    "role": "assistant",
                                    "content": format_text_with_ia_highlighting(STANDARD_ERROR_MESSAGE),
                                }
                            )
                            # Força atualização da tela e PARA o processamento aqui para evitar reutilização
                            st.rerun()
                        else:
                            # Converte os dados de retorno para um formato serializável SEGURO
                            st.session_state.current_interaction["serializable_data"] = safe_serialize_data(raw_data)

                            # Atualiza a mensagem de processamento
                            processing_msg.chat_message("assistant").markdown(
                                format_text_with_ia_highlighting("Dados recebidos. Calculando resultados...")
                            )

                            # Refina a resposta com o Gemini
                            st.session_state.current_interaction["refined_response"], st.session_state.current_interaction["tech_details"] = refine_with_gemini(
                                prompt, st.session_state.current_interaction["serializable_data"], st.session_state.current_interaction["serializable_params"], st.session_state.current_interaction["query"]
                            )

                            # Salva a interação no cache
                            try:
                                save_interaction(
                                    user_id=creds["login"],
                                    question=prompt,
                                    function_params=st.session_state.current_interaction["serializable_params"],
                                    query_sql=st.session_state.current_interaction["query"],
                                    raw_data=st.session_state.current_interaction["serializable_data"],
                                    raw_response=None,  # Será definido abaixo
                                    refined_response=st.session_state.current_interaction["refined_response"],
                                    tech_details=safe_serialize_tech_details(st.session_state.current_interaction["tech_details"]),
                                    status="OK"
                                )
                            except Exception as cache_error:
                                print(f"Erro ao salvar no cache (nova consulta): {cache_error}")

                            # Remove a mensagem de processamento e adiciona a resposta final
                            processing_msg.empty()
                            st.session_state.chat_history.append(
                                {
                                    "role": "assistant",
                                    "content": format_text_with_ia_highlighting(slugfy_response(st.session_state.current_interaction["refined_response"])),
                                    "tech_details": st.session_state.current_interaction["tech_details"],
                                }
                            )
                else:
                    # Resposta direta sem chamada de função
                    processing_msg.empty()
                    st.session_state.chat_history.append(
                        {"role": "assistant", "content": format_text_with_ia_highlighting(response.text)}
                    )
                
            # Inicializa variáveis para o log (caso de nova consulta sem function call)
            # Usa session state para garantir isolamento multi-usuário
            current_serializable_params = st.session_state.current_interaction.get("serializable_params")
            current_query = st.session_state.current_interaction.get("query")
            current_serializable_data = st.session_state.current_interaction.get("serializable_data")
            current_refined_response = st.session_state.current_interaction.get("refined_response")
            current_tech_details = st.session_state.current_interaction.get("tech_details")
                    
            # Regra para a estranha manipulação de response por parte do gemini
            try:
                if 'response' in locals():
                    current_raw_response = response.text
                else:
                    current_raw_response = None
            except (AttributeError, ValueError):
                current_raw_response = None

            # Log apenas para casos de sucesso (não duplicar logs de erro)
            if current_refined_response and current_serializable_data:
                log_interaction(
                    user_input=prompt,
                    function_params=current_serializable_params,
                    query=current_query if current_query else None,
                    raw_data=current_serializable_data if current_serializable_data else None,
                    raw_response=current_raw_response,
                    refined_response=current_refined_response,
                    first_ten_table_lines=current_serializable_data[:10] if current_serializable_data else None,
                    graph_data=current_tech_details.get("chart_info") if current_tech_details and current_tech_details.get("chart_info") else None,
                    export_data=current_tech_details.get("export_info") if current_tech_details and current_tech_details.get("export_info") else None,
                    status="OK",
                    status_msg=f"Consulta processada com sucesso.",
                    client_request_count=rate_limiter.state["count"],
                    custom_fields=None,
                )
            st.rerun()

        except Exception as e:
            # Usa session state para garantir isolamento multi-usuário
            current_serializable_params = st.session_state.current_interaction.get("serializable_params")
            current_query = st.session_state.current_interaction.get("query")
            current_serializable_data = st.session_state.current_interaction.get("serializable_data")
            current_refined_response = st.session_state.current_interaction.get("refined_response")
            current_tech_details = st.session_state.current_interaction.get("tech_details")
            current_raw_response = st.session_state.current_interaction.get("raw_response")
                
            error_details = f"Exception: {str(e)} | Type: {type(e).__name__}"
            
            # Log no BigQuery (para controle geral)
            log_interaction(
                user_input=prompt,
                function_params=current_serializable_params,
                query=current_query if current_query else None,
                raw_data=current_serializable_data if current_serializable_data else None,
                raw_response=current_raw_response,
                refined_response=STANDARD_ERROR_MESSAGE,
                first_ten_table_lines=None,
                graph_data=current_tech_details.get("chart_info") if current_tech_details and current_tech_details.get("chart_info") else None,
                export_data=current_tech_details.get("export_info") if current_tech_details and current_tech_details.get("export_info") else None,
                status="ERROR",
                status_msg=error_details,
                client_request_count=rate_limiter.state["count"],
                custom_fields={
                    "error_type": "general_exception",
                    "error_details": str(e),
                    "exception_type": type(e).__name__
                }
            )
            
            # Log específico de erro no DuckDB (para análise detalhada)
            log_error(
                user_id=creds["login"],
                error_type="general_exception",
                error_message=str(e),
                context=f"User request: {prompt} | Exception type: {type(e).__name__}",
                traceback=traceback.format_exc()
            )
            
            st.session_state.chat_history.append(
                {"role": "assistant", "content": format_text_with_ia_highlighting(STANDARD_ERROR_MESSAGE)}
            )
            st.rerun()