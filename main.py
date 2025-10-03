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

from style import MOBILE_IFRAME_CHAT
from deepseek_theme import apply_deepseek_theme, create_usage_indicator, show_typing_animation, get_login_theme, get_chat_theme
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

# Aplica o tema DeepSeek escuro moderno (sem mostrar código)
st.markdown(get_chat_theme(), unsafe_allow_html=True)

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
                # Atualiza a animação existente em vez de criar nova
                typing_placeholder.markdown("<div style='padding: 8px 12px; color: #00d4ff; font-size: 14px; opacity: 0.8;'> Reutilizando dados anteriores...</div>", unsafe_allow_html=True)
                
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

                    # Remove animação de typing
                    typing_placeholder.empty()
                    
                    # Atualiza o histórico e força re-renderização
                    st.session_state.chat_history.append(
                        {
                            "role": "assistant",
                            "content": format_text_with_ia_highlighting(st.session_state.current_interaction["refined_response"]),
                            "tech_details": st.session_state.current_interaction["tech_details"],
                        }
                    )
                    
                    # Força atualização da UI
                    st.rerun()

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
                            
                            # Remove animação de typing
                            typing_placeholder.empty()
                            
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
                            
                            # Remove animação de typing
                            typing_placeholder.empty()
                            
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
                            
                            # Remove animação de typing
                            typing_placeholder.empty()
                            
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

                            # Remove animação de typing
                            typing_placeholder.empty()
                            
                            # Atualiza o histórico e força re-renderização
                            st.session_state.chat_history.append(
                                {
                                    "role": "assistant",
                                    "content": format_text_with_ia_highlighting(slugfy_response(st.session_state.current_interaction["refined_response"])),
                                    "tech_details": st.session_state.current_interaction["tech_details"],
                                }
                            )
                            
                            # Força atualização da UI
                            st.rerun()
                else:
                    # Resposta direta sem chamada de função
                    typing_placeholder.empty()
                    
                    # Atualiza histórico e força re-renderização
                    st.session_state.chat_history.append(
                        {"role": "assistant", "content": format_text_with_ia_highlighting(response.text)}
                    )
                    
                    # Força atualização da UI
                    st.rerun()
                
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
            # Removido st.rerun() para evitar comportamento estranho na UI

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
            
            # Remove animação de typing
            typing_placeholder.empty()
            
            st.session_state.chat_history.append(
                {"role": "assistant", "content": format_text_with_ia_highlighting(STANDARD_ERROR_MESSAGE)}
            )
            st.rerun()