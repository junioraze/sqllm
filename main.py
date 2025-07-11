import streamlit as st

# DEVE SER O PRIMEIRO COMANDO STREAMLIT
st.set_page_config(
    page_title="VIAQUEST Insights (Sales)", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Agora importe os outros módulos
import json
import os
from cache_db import save_interaction, log_error, get_user_history
from config import MAX_RATE_LIMIT, DATASET_ID, PROJECT_ID, TABLES_CONFIG  # Importa a configuração do assistente
from style import MOBILE_IFRAME_BASE  # Importa o módulo de estilos
from gemini_handler import initialize_model, refine_with_gemini, should_reuse_data
from database import build_query, execute_query
from utils import display_message_with_spoiler, slugfy_response
from rate_limit import RateLimiter
from logger import log_interaction

def safe_serialize_gemini_params(params):
    """
    Serializa parâmetros do Gemini de forma segura, lidando com RepeatedComposite e outros tipos
    """
    if params is None:
        return None
        
    serializable = {}
    
    for key, value in params.items():
        try:
            # Tenta serializar diretamente primeiro
            json.dumps(value)
            serializable[key] = value
        except (TypeError, ValueError):
            # Se falhar, converte para tipos básicos
            if hasattr(value, '__iter__') and not isinstance(value, (str, bytes)):
                # É uma lista/sequência
                serializable[key] = list(value)
            else:
                # Converte para string como fallback
                serializable[key] = str(value)
    
    return serializable

def safe_serialize_data(data):
    """
    Serializa dados de forma segura para JSON
    """
    if data is None:
        return None
        
    if isinstance(data, list):
        return [
            {
                k: str(v) if not isinstance(v, (str, int, float, bool, type(None))) else v
                for k, v in item.items()
            }
            for item in data
        ]
    
    return data

# ====================================================================
# REUTILIZAÇÃO ULTRA-CONSERVADORA DE DADOS
# ====================================================================
# 
# DECISÃO BASEADA EM IA (Gemini) 🧠 - MODO CONSERVADOR:
# O Gemini analisa o contexto e decide se pode reutilizar dados, mas
# com uma abordagem EXTREMAMENTE conservadora para evitar problemas.
#
# ✅ REUTILIZAR APENAS (casos óbvios de exportação/visualização):
# - "gere um Excel desses dados" → REUTILIZA (exportação simples)
# - "criar gráfico desses dados" → REUTILIZA (visualização simples)  
# - "mostrar em tabela HTML" → REUTILIZA (formatação simples)
# - "mais detalhes sobre esses resultados" → REUTILIZA (elaboração simples)
#
# ❌ NOVA CONSULTA SEMPRE (casos que requerem SQL):
# - "compare com 2024" → NOVA CONSULTA (dados diferentes)
# - "mostre também SP" → NOVA CONSULTA (filtro adicional)
# - "calcule a porcentagem" → NOVA CONSULTA (deixa SQL calcular)
# - "qual modelo vendeu mais?" → NOVA CONSULTA (pode não estar nos dados)
# - "some com janeiro" → NOVA CONSULTA (agregação)
# - Qualquer manipulação, agregação, comparação, filtro adicional
#
# 🔴 FILOSOFIA: EM CASO DE DÚVIDA, SEMPRE NOVA CONSULTA!
# Melhor fazer SQL otimizado do que manipular dados localmente.
# Isso garante precisão e evita complexidade desnecessária.
# ====================================================================

# Configuração do rate limit (100 requisições por dia)
rate_limiter = RateLimiter(max_requests_per_day=MAX_RATE_LIMIT)
#Inicializa variáveis para armazenar os dados
refined_response = None
serializable_params = None
serializable_data = None
tech_details = None
query = None
# Variável para controlar a exibição de detalhes técnicos
SHOW_TECHNICAL_SPOILER = True  # Defina como True para mostrar detalhes técnicos

# Configuração de estilos para mobile
st.markdown(MOBILE_IFRAME_BASE, unsafe_allow_html=True)

if "last_data" not in st.session_state:
    st.session_state.last_data = {
        "raw_data": None,
        "params": None,
        "query": None,
        "tech_details": None,
        "prompt": None,
        "df": None  # Novo: DataFrame para exportação
    }

# Carrega as credenciais do arquivo
with open(os.path.join(os.path.dirname(__file__), "credentials.json"), "r") as f:
    creds = json.load(f)

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("Login VIAQUEST Insights")
    login = st.text_input("E-mail", value="", key="login_input")
    password = st.text_input("Senha", type="password", key="password_input")
    if st.button("Entrar"):
        if login == creds["login"] and password == creds["password"]:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos.")
    st.stop()

# Container principal para todo o conteúdo
with st.container():
    
    st.title("VIAQUEST Insights (Sales) - Agentes de IA para a área Comercial")

    with st.expander("⚠️ Limitações e Regras do Assistente (clique para ver)", expanded=False):
        st.markdown(
            f"""
            - Este assistente **só pode consultar a tabela de vendas de veículos** configurada no sistema.
            - **Não é possível acessar ou cruzar dados de outras tabelas** ou fontes externas.
            - **Apenas uma consulta por vez** é permitida. Não é possível realizar múltiplas buscas simultâneas.
            - Para comparações temporais, utilize perguntas claras (ex: "Compare as vendas de 2023 e 2024 por mês").
            - O modelo pode não compreender perguntas muito vagas ou fora do escopo dos dados disponíveis.
            - Resultados são sempre baseados nos dados mais recentes disponíveis na tabela.
            - **Limite diário de requisições: {MAX_RATE_LIMIT}**. Se atingido, você receberá uma mensagem de aviso.
            > Para detalhes técnicos, consulte a documentação ou o spoiler abaixo.
            """
        )

    # Exemplos de perguntas (restaurado)
    if "chat_history" not in st.session_state or len(st.session_state.chat_history) == 0:
        st.write("Faça perguntas sobre vendas de veículos. Exemplos:")
        st.code(
            """- Qual o total vendido em 2024?
- Compare as vendas entre os meses existentes de 2023 e 2024. 
- Demonstre os modelos vendidos no ceara em 2023?
"""
        )

    # Inicialização do modelo e estado da sessão
    if "model" not in st.session_state:
        st.session_state.model = initialize_model()

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if "last_data" not in st.session_state:
        st.session_state.last_data = {
            "raw_data": None,
            "params": None,
            "query": None,
            "tech_details": None,
            "prompt": None,
        }

    # Exibe o histórico de chat
    for msg in st.session_state.chat_history:
        display_message_with_spoiler(
            msg["role"], msg["content"], msg.get("tech_details"), SHOW_TECHNICAL_SPOILER
        )

# Container fixo para o input (fora do content-container)
st.markdown('<div class="fixed-bottom">', unsafe_allow_html=True)
prompt = st.chat_input("Faça sua pergunta...", key="mobile_input")
st.markdown('</div>', unsafe_allow_html=True)

# Captura novo input
if prompt:
    # Verifica o rate limit antes de processar
    if rate_limiter.check_limit():
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": "Limite diário de requisições atingido. Tente novamente amanhã."
        })
        st.rerun()
    else:
        # Incrementa o contador
        rate_limiter.increment()
        # Adiciona a pergunta ao histórico
        st.session_state.chat_history.append({"role": "user", "content": prompt})

        try:
            # Busca histórico do usuário para contexto na decisão de reutilização
            user_history = get_user_history(creds["login"])
            
            # Verifica se deve reutilizar dados usando inteligência do Gemini
            # O Gemini analisa o contexto completo e decide se os dados existentes são suficientes
            should_reuse = False
            if st.session_state.last_data["raw_data"] is not None:
                reuse_decision = should_reuse_data(
                    st.session_state.model,
                    prompt,
                    st.session_state.last_data,
                    user_history
                )
                should_reuse = reuse_decision.get("should_reuse", False)
            
            if should_reuse:
                # Reutiliza os dados da última consulta baseado na decisão do Gemini
                with st.spinner("Processando com dados anteriores..."):
                    # Usa os dados já disponíveis
                    serializable_data = safe_serialize_data(st.session_state.last_data["raw_data"])
                    
                    refined_response, tech_details = refine_with_gemini(
                        prompt,
                        serializable_data,
                        st.session_state.last_data["params"],
                        st.session_state.last_data["query"],
                    )
                    
                    # Adiciona informação sobre reutilização nos detalhes técnicos
                    if tech_details:
                        tech_details["reuse_info"] = {
                            "reused": True,
                            "reason": reuse_decision.get("reason", "Decisão inteligente do Gemini"),
                            "original_prompt": st.session_state.last_data["prompt"]
                        }

                # Atualiza o histórico
                st.session_state.chat_history.append(
                    {
                        "role": "assistant",
                        "content": refined_response,
                        "tech_details": tech_details,
                    }
                )

                # Salva a interação de reutilização no cache
                try:
                    save_interaction(
                        user_id=creds["login"],
                        question=prompt,
                        function_params=safe_serialize_gemini_params(st.session_state.last_data["params"]),
                        query_sql=st.session_state.last_data["query"],
                        raw_data=serializable_data,
                        raw_response=None,
                        refined_response=refined_response,
                        tech_details=tech_details,
                        status="OK",
                        reused_from=st.session_state.last_data.get("prompt")
                    )
                except Exception as cache_error:
                    print(f"Erro ao salvar no cache (reutilização): {cache_error}")
                    
            else:
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
                    "Processando sua solicitação..."
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
                        serializable_params = safe_serialize_gemini_params(params)

                        # Obter nome da tabela e construir full_table_id
                        table_name = serializable_params.get("table_name")
                        if table_name not in TABLES_CONFIG.keys():
                            st.error(f"Tabela {table_name} não configurada")
                            st.stop()
                            
                        full_table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
                        
                        # Construir e executar query
                        query = build_query(full_table_id, serializable_params)
                        raw_data = execute_query(query)

                        if "error" in raw_data:
                            st.session_state.chat_history.append(
                                {
                                    "role": "assistant",
                                    "content": f"Erro na consulta:\n{raw_data['error']}\n\nQuery:\n```sql\n{raw_data['query']}\n```",
                                }
                            )
                        else:
                            # Converte os dados de retorno para um formato serializável SEGURO
                            serializable_data = safe_serialize_data(raw_data)

                            # Atualiza a mensagem de processamento
                            processing_msg.chat_message("assistant").markdown(
                                "Dados recebidos. Calculando resultados..."
                            )

                            # Refina a resposta com o Gemini
                            refined_response, tech_details = refine_with_gemini(
                                prompt, serializable_data, serializable_params, query
                            )

                            # Atualiza o histórico e os últimos dados
                            st.session_state.last_data = {
                                "raw_data": serializable_data,
                                "params": serializable_params,
                                "query": query,
                                "tech_details": tech_details,
                                "prompt": prompt,
                            }

                            # Salva a interação no cache
                            try:
                                save_interaction(
                                    user_id=creds["login"],
                                    question=prompt,
                                    function_params=serializable_params,
                                    query_sql=query,
                                    raw_data=serializable_data,
                                    raw_response=None,  # Será definido abaixo
                                    refined_response=refined_response,
                                    tech_details=tech_details,
                                    status="OK"
                                )
                            except Exception as cache_error:
                                print(f"Erro ao salvar no cache (nova consulta): {cache_error}")

                            # Remove a mensagem de processamento e adiciona a resposta final
                            processing_msg.empty()
                            st.session_state.chat_history.append(
                                {
                                    "role": "assistant",
                                    "content": slugfy_response(refined_response),
                                    "tech_details": tech_details,
                                }
                            )
                else:
                    # Resposta direta sem chamada de função
                    processing_msg.empty()
                    st.session_state.chat_history.append(
                        {"role": "assistant", "content": response.text}
                    )
                
            # Inicializa variáveis para o log (caso de nova consulta sem function call)
            if 'serializable_params' not in locals():
                serializable_params = None
            if 'query' not in locals():
                query = None
            if 'serializable_data' not in locals():
                serializable_data = None
            if 'refined_response' not in locals():
                refined_response = None
            if 'tech_details' not in locals():
                tech_details = None
                    
            # Regra para a estranha manipulação de response por parte do gemini
            try:
                if 'response' in locals():
                    raw_response = response.text
                else:
                    raw_response = None
            except (AttributeError, ValueError):
                raw_response = None

            # Força atualização da tela
            log_interaction(
                user_input=prompt,
                function_params=serializable_params,
                query=query if query else None,
                raw_data=serializable_data if serializable_data else None,
                raw_response=raw_response,
                refined_response=refined_response,
                first_ten_table_lines=serializable_data[:10] if serializable_data else None,
                graph_data=tech_details.get("chart_info")  if tech_details and tech_details.get("chart_info") else None,
                export_data=tech_details.get("export_info") if tech_details and tech_details.get("export_info") else None,  # Preencha se houver exportação de dados
                status="OK",
                status_msg=f"Consulta processada com sucesso.",
                client_request_count=rate_limiter.state["count"],
                custom_fields=None,  # Use se quiser logar algo extra
            )
            st.rerun()

        except Exception as e:
            # Inicializa variáveis para o log em caso de erro
            if 'serializable_params' not in locals():
                serializable_params = None
            if 'query' not in locals():
                query = None
            if 'serializable_data' not in locals():
                serializable_data = None
            if 'raw_response' not in locals():
                raw_response = None
            if 'refined_response' not in locals():
                refined_response = None
            if 'tech_details' not in locals():
                tech_details = None
                
            log_interaction(
                user_input=prompt,
                function_params=serializable_params,
                query=query if query else None,
                raw_data=serializable_data if serializable_data else None,
                raw_response=raw_response,
                refined_response=refined_response if refined_response else None,
                first_ten_table_lines=None,
                graph_data=tech_details.get("chart_info") if tech_details and tech_details.get("chart_info") else None,
                export_data=tech_details.get("export_info") if tech_details and tech_details.get("export_info") else None,
                status="ERROR",
                status_msg=str(e),
                client_request_count=rate_limiter.state["count"],
                custom_fields=None,
            )
            st.session_state.chat_history.append(
                {"role": "assistant", "content": f"Ocorreu um erro: {str(e)}"}
            )
            st.rerun()