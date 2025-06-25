import streamlit as st

# DEVE SER O PRIMEIRO COMANDO STREAMLIT
st.set_page_config(
    page_title="VIAQUEST Insights (Sales)", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Agora importe os outros módulos
from style import MOBILE_IFRAME_BASE  # Importa o módulo de estilos
from gemini_handler import initialize_model, refine_with_gemini
from database import build_query, execute_query
from utils import display_message_with_spoiler

SHOW_TECHNICAL_SPOILER = True  # Defina como True para mostrar detalhes técnicos

# Configuração de estilos para mobile
st.markdown(MOBILE_IFRAME_BASE, unsafe_allow_html=True)

# Container principal para todo o conteúdo
with st.container():
    st.title("VIAQUEST Insights (Sales) - Agentes de IA para a área Comercial")

    with st.expander("⚠️ Limitações e Regras do Assistente (clique para ver)", expanded=False):
        st.markdown(
            """
            - Este assistente **só pode consultar a tabela de vendas de veículos** configurada no sistema.
            - **Não é possível acessar ou cruzar dados de outras tabelas** ou fontes externas.
            - **Apenas uma consulta por vez** é permitida. Não é possível realizar múltiplas buscas simultâneas.
            - Para comparações temporais, utilize perguntas claras (ex: "Compare as vendas de 2023 e 2024 por mês").
            - O modelo pode não compreender perguntas muito vagas ou fora do escopo dos dados disponíveis.
            - Resultados são sempre baseados nos dados mais recentes disponíveis na tabela.

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
    # Adiciona a pergunta ao histórico
    st.session_state.chat_history.append({"role": "user", "content": prompt})

    # Verifica se é um comando para reutilizar os últimos dados
    reuse_keywords = [
        "usando os mesmos dados",
        "com os mesmos dados",
        "nos dados anteriores",
    ]
    should_reuse = any(keyword in prompt.lower() for keyword in reuse_keywords)

    try:
        if should_reuse and st.session_state.last_data["raw_data"]:
            # Reutiliza os dados da última consulta
            with st.spinner("Processando com os dados anteriores..."):
                # Converte os dados para um formato serializável
                serializable_data = [
                    {
                        k: str(v) if not isinstance(v, (str, int, float, bool)) else v
                        for k, v in item.items()
                    }
                    for item in st.session_state.last_data["raw_data"]
                ]

                refined_response, tech_details = refine_with_gemini(
                    prompt,
                    serializable_data,
                    st.session_state.last_data["params"],
                    st.session_state.last_data["query"],
                )

            # Atualiza o histórico
            st.session_state.chat_history.append(
                {
                    "role": "assistant",
                    "content": refined_response,
                    "tech_details": tech_details,
                }
            )

            # Atualiza o último prompt
            st.session_state.last_data["prompt"] = prompt

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

                # Serialização dos parâmetros
                serializable_params = {}
                for key, value in params.items():
                    if key == "select" and isinstance(value, str):
                        try:
                            # Remove colchetes e aspas extras, depois divide
                            cleaned = (
                                value.strip("[]").replace("'", "").replace('"', "")
                            )
                            serializable_params[key] = [
                                item.strip() for item in cleaned.split(",")
                            ]
                        except AttributeError:
                            serializable_params[key] = [value]
                    else:
                        serializable_params[key] = value

                # constrói a query
                query = build_query(serializable_params)
                raw_data = execute_query(query)

                if "error" in raw_data:
                    st.session_state.chat_history.append(
                        {
                            "role": "assistant",
                            "content": f"Erro na consulta:\n{raw_data['error']}\n\nQuery:\n```sql\n{raw_data['query']}\n```",
                        }
                    )
                else:
                    # Converte os dados de retorno para um formato serializável
                    serializable_data = [
                        {
                            k: (
                                str(v)
                                if not isinstance(v, (str, int, float, bool))
                                else v
                            )
                            for k, v in item.items()
                        }
                        for item in raw_data
                    ]

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

                    # Remove a mensagem de processamento e adiciona a resposta final
                    processing_msg.empty()
                    st.session_state.chat_history.append(
                        {
                            "role": "assistant",
                            "content": refined_response,
                            "tech_details": tech_details,
                        }
                    )
            else:
                # Resposta direta sem chamada de função
                processing_msg.empty()
                st.session_state.chat_history.append(
                    {"role": "assistant", "content": response.text}
                )

        # Força atualização da tela
        st.rerun()

    except Exception as e:
        st.session_state.chat_history.append(
            {"role": "assistant", "content": f"Ocorreu um erro: {str(e)}"}
        )
        st.rerun()