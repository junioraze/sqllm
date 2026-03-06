"""
Message Handler - Fluxo limpo e organizado para processamento de mensagens
Fluxo: pergunta → verificar reuso → SQL → query DB → processar resposta → gráfico/export
"""

import streamlit as st
import traceback
import json
import time
from typing import Tuple, Dict, Optional, Any
from datetime import datetime


from utils.cache import get_user_history, get_interaction_full_data, save_interaction, log_error
from llm_handlers.gemini_handler import should_reuse_data, refine_with_gemini_rag, initialize_rag_system
from database.query_builder import build_query, execute_query
from utils.helpers import (
    safe_serialize_gemini_params, 
    safe_serialize_data, 
    safe_serialize_tech_details,
    format_text_with_ia_highlighting,
    slugfy_response
)
from config.settings import STANDARD_ERROR_MESSAGE, PROJECT_ID, DATASET_ID, TABLES_CONFIG
from utils.logger import log_interaction
from ui.deepseek_theme import show_typing_animation, show_dynamic_processing_animation, get_step_display_info
from llm_handlers.prompt_rules import get_adaptation_prompt
# Sistema RAG obrigatório
from rag_system.business_metadata_rag import get_business_rag_instance
from utils.metrics import ai_metrics
# Conversational Analytics Handler
from conversational_analytics_handler import ConversationalAnalyticsHandler


class MessageHandler:
    """Classe responsável pelo fluxo completo de processamento de mensagens"""
    
    def _start_timing(self, step_name: str, typing_placeholder=None) -> None:
        """Inicia medição de tempo para uma etapa e atualiza indicador visual"""
        current_time = time.time()
        if self.start_time is None:
            self.start_time = current_time
        
        self.timing_info[step_name] = {
            'start': current_time,
            'end': None,
            'duration': None,
            'timestamp': datetime.fromtimestamp(current_time).strftime('%H:%M:%S.%f')[:-3]
        }
        
        # Atualiza indicador visual se placeholder fornecido
        if typing_placeholder:
            self._update_dynamic_indicator(typing_placeholder, step_name)
    
    def _end_timing(self, step_name: str) -> None:
        """Finaliza medição de tempo para uma etapa"""
        if step_name in self.timing_info:
            end_time = time.time()
            self.timing_info[step_name]['end'] = end_time
            duration = end_time - self.timing_info[step_name]['start']
            self.timing_info[step_name]['duration'] = round(duration * 1000, 2)  # em ms
    
    def _get_total_duration(self) -> float:
        """Calcula duração total do processamento"""
        if self.start_time:
            return round((time.time() - self.start_time) * 1000, 2)  # em ms
        return 0
    
    def _update_dynamic_indicator(self, typing_placeholder, step_name: str) -> None:
        """Atualiza o indicador visual com a etapa atual"""
        step_display, emoji = get_step_display_info(step_name)
        typing_placeholder.markdown(
            show_dynamic_processing_animation(step_display, emoji), 
            unsafe_allow_html=True
        )
    
    def __init__(self, model, rate_limiter, user_id: str):
        self.model = model
        self.rate_limiter = rate_limiter
        self.user_id = user_id
        self.project_id = PROJECT_ID  # Para detecção de CA
        self.dataset_id = DATASET_ID
        self.flow_path = []  # Para rastrear o caminho seguido
        self.timing_info = {}  # Para rastrear timing de cada etapa
        self.start_time = None
        
    def process_message(self, prompt: str, typing_placeholder) -> None:
        """
        Processa uma mensagem seguindo o fluxo definido:
        1️⃣ Verificar Conversational Analytics para perguntas sobre glinhares
        2️⃣ Se CA: Detecta tabela → Processa → Retorna (summary, tech_details) com tabela + gráfico
        3️⃣ Se não CA: Fluxo SQL tradicional (verificar reuso, build query, execute)
        """
        try:
            self.flow_path = ["início"]
            self._start_timing("processo_completo", typing_placeholder)
            
            # Etapa 0: Verificar se deve usar Conversational Analytics para glinhares
            if self._should_use_conversational_analytics(prompt):
                self.flow_path.append("conversational_analytics")
                self._process_conversational_analytics(typing_placeholder, prompt)
                self._end_timing("processo_completo")
                return  # ✅ FIM DO FLUXO CA - NÃO CONTINUA PARA O ANTIGO
            
            # Se não for CA, segue fluxo SQL tradicional
            # Etapa 1: Verificar oportunidade de reutilização
            self._start_timing("verificacao_reuso", typing_placeholder)
            should_reuse, reuse_data = self._check_reuse_opportunity(prompt)
            should_reuse, reuse_data = False, False # REVER
            self._end_timing("verificacao_reuso")
            
            if should_reuse and reuse_data:
                self.flow_path.append("reuso_detectado")
                self._start_timing("processamento_reuso", typing_placeholder)
                self._process_reuse_flow(typing_placeholder, prompt, reuse_data)
                self._end_timing("processamento_reuso")
            else:
                self.flow_path.append("nova_consulta")
                self._start_timing("processamento_nova_consulta", typing_placeholder)
                self._process_new_query_flow(typing_placeholder, prompt)
                self._end_timing("processamento_nova_consulta")
                
            self._end_timing("processo_completo")
                
        except Exception as e:
            print(f"🔥 HANDLER - ERRO CAPTURADO: {e}")
            import traceback
            print(f"🔥 HANDLER - TRACEBACK: {traceback.format_exc()}")
            self.flow_path.append("erro_geral")
            self._handle_error(typing_placeholder, prompt, str(e), traceback.format_exc())

    def _should_use_conversational_analytics(self, prompt: str) -> bool:
        """
        Detecta se deve usar Conversational Analytics.
        
        Regra: Se o projeto for um projeto CA (superacessovip, glinhares, etc),
        TODAS as perguntas usam CA. Não usa fluxo SQL tradicional.
        """
        # Projetos que SEMPRE usam Conversational Analytics
        ca_projects = [
            'superacessovip',
            'glinhares',
            'dw_superacesso',
            'dw-superacesso'
        ]
        
        # Verifica se projeto atual é um projeto CA
        project_lower = self.project_id.lower() if hasattr(self, 'project_id') else PROJECT_ID.lower()
        is_ca_project = any(ca_proj in project_lower for ca_proj in ca_projects)
        
        # Se for projeto CA, SEMPRE usa CA (ignora fluxo SQL tradicional)
        if is_ca_project:
            return True
        
        # Se for outro projeto, usa keywords para detectar CA
        prompt_lower = prompt.lower()
        ca_keywords = [
            'glinhares',
            'veículo',
            'veiculo',
            'consórcio',
            'consorcio',
            'cota',
            'plano',
            'moto',
            'carro',
            'car',
            'modelo',
            'fandi',
            'vendedor',
            'loja',
            'venda de',
            'top',
            'ranking'
        ]
        
        return any(keyword in prompt_lower for keyword in ca_keywords)
    
    def _process_conversational_analytics(self, typing_placeholder, prompt: str) -> None:
        """
        Processa pergunta usando Conversational Analytics Handler.
        
        Fluxo:
        1. Mostra indicador "Analisando..."
        2. Chama ConversationalAnalyticsHandler.process(prompt)
        3. Handler retorna: (summary: str, tech_details: Dict)
           - summary: Texto da resposta com insights
           - tech_details: Dict com:
             * aggrid_data: Lista de dicts para tabela
             * chart_info.fig: Figura Plotly em formato dict
             * query: SQL executado
             * data_source: Nome da tabela detectada
        4. UI exibe: Texto → Tabela AgGrid → Gráfico Plotly
        """
        try:
            self._start_timing("processamento_ca", typing_placeholder)
            self.flow_path.append("processamento_ca")
            
            typing_placeholder.markdown(
                "🔍 **Analisando com Conversational Analytics...**",
                unsafe_allow_html=True
            )
            
            # Executa CA: pergunta → (summary, tech_details)
            ca_handler = ConversationalAnalyticsHandler(
                project_id=PROJECT_ID,
                dataset_id=DATASET_ID,
                user_id=self.user_id
            )
            refined_response, tech_details = ca_handler.process(prompt)
            
            self._end_timing("processamento_ca")
            
            # Log de sucesso
            self._log_success(
                prompt=prompt,
                serializable_params={
                    "type": "conversational_analytics",
                    "agent_id": tech_details.get("agent_id"),
                    "dataset": tech_details.get("dataset")
                },
                query=tech_details.get("sql_query", ""),
                serializable_data=tech_details.get("aggrid_data", []),
                refined_response=refined_response,
                tech_details=tech_details
            )
            
            # Salva interação
            try:
                save_interaction(
                    user_id=self.user_id,
                    question=prompt,
                    function_params={"type": "conversational_analytics", "agent_id": tech_details.get("agent_id")},
                    query_sql=tech_details.get("sql_query", ""),
                    raw_data=tech_details.get("aggrid_data", []),
                    raw_response=None,
                    refined_response=refined_response,
                    tech_details=tech_details,
                    status="OK"
                )
            except Exception as e:
                print(f"⚠️ Erro salvando interação CA: {e}")
            
            # Atualiza UI: limpa indicator
            typing_placeholder.empty()
            
            # Finaliza a resposta com tabelas e gráficos
            self._finalize_response(
                typing_placeholder=typing_placeholder,
                response_text=refined_response,
                tech_details=tech_details
            )
        
        except Exception as e:
            print(f"❌ Erro Conversational Analytics: {e}")
            self.flow_path.append("erro_ca")
            import traceback
            traceback.print_exc()
            self._handle_error(typing_placeholder, prompt, f"Erro CA: {str(e)}", traceback.format_exc())

    def _check_reuse_opportunity(self, prompt: str) -> Tuple[bool, Dict]:
        """Etapa 1: Verificar se pode reutilizar dados anteriores - OTIMIZADO COM DETECÇÃO INTELIGENTE"""
        self.flow_path.append("verificando_reuso")
        
        try:
            # 🚀 OTIMIZAÇÃO CRÍTICA: Verificação inteligente antes de consultar Gemini
            
            # Palavras-chave que SEMPRE indicam reuso (referências explícitas)
            EXPLICIT_REUSE_KEYWORDS = [
                'mesmos dados', 'dados anteriores', 'última consulta', 'último resultado', 
                'consulta anterior', 'resultado anterior', 'tabela anterior',
                'anterior', 'ultimo', 'última', 'mesmo', 'mesma',
                'agora', 'agr', 'então', 'entao', 'e agora', 'e agr',
                'com isso', 'com esse', 'com esses', 'com os dados'
            ]
            
            # Palavras-chave que podem indicar reuso MAS precisam de contexto
            POTENTIAL_REUSE_KEYWORDS = [
                'gráfico', 'grafico', 'chart', 'visualização', 'visualizacao', 
                'plotar', 'plot', 'curva', 'linha',
                'exportar', 'excel', 'planilha', 'csv', 'baixar', 'download'
            ]
            
            prompt_lower = prompt.lower()
            
            # Verifica reuso explícito (sempre procede com verificação)
            has_explicit_reuse = any(keyword in prompt_lower for keyword in EXPLICIT_REUSE_KEYWORDS)
            
            if has_explicit_reuse:
                self.flow_path.append("reuso_explicito_detectado")
                # Procede com verificação completa
            else:
                # Verifica se é pedido de gráfico/export MAS com nova consulta completa
                has_potential_reuse = any(keyword in prompt_lower for keyword in POTENTIAL_REUSE_KEYWORDS)
                
                if has_potential_reuse:
                    # ANÁLISE INTELIGENTE: verifica se é reuso real ou nova consulta com gráfico
                    
                    # Indicadores de NOVA CONSULTA (mesmo com palavra gráfico/export):
                    # - Menciona dados específicos (vendas, produtos, etc.)
                    # - Menciona filtros temporais (2024, janeiro, etc.)
                    # - Menciona agregações (top 5, total, soma, etc.)
                    # - Menciona dimensões (por região, por produto, etc.)
                    
                    NEW_QUERY_INDICATORS = [
                        # Dados/métricas específicas
                        'vendas', 'receita', 'faturamento', 'lucro', 'margem',
                        'produtos', 'clientes', 'pedidos', 'transações',
                        
                        # Filtros temporais
                        '2024', '2025', '2023', 'janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
                        'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro',
                        'trimestre', 'semestre', 'ano', 'mês', 'semana',
                        
                        # Agregações
                        'top', 'maior', 'menor', 'total', 'soma', 'média', 'contagem',
                        'ranking', 'melhor', 'pior', 'máximo', 'mínimo',
                        
                        # Dimensões
                        'por região', 'por estado', 'por cidade', 'por produto', 'por categoria',
                        'por vendedor', 'por cliente', 'por canal', 'por loja'
                    ]
                    
                    has_new_query_indicators = any(indicator in prompt_lower for indicator in NEW_QUERY_INDICATORS)
                    
                    if has_new_query_indicators:
                        # É uma nova consulta completa que inclui gráfico/export
                        self.flow_path.append("nova_consulta_com_grafico_detectada")
                        return False, {"reason": "Nova consulta completa detectada (inclui especificação de dados + visualização)"}
                    else:
                        # Pode ser reuso - palavra gráfico/export sem especificação de dados
                        self.flow_path.append("possivel_reuso_detectado")
                        # Procede com verificação
                else:
                    # Sem palavras-chave de reuso - claramente nova consulta
                    self.flow_path.append("nova_consulta_detectada")
                    return False, {"reason": "Nova consulta detectada - sem indicadores de reutilização"}
            
            # Se chegou aqui, há indicadores válidos - procede com verificação completa
            user_history = get_user_history(self.user_id)
            if not user_history:
                self.flow_path.append("sem_historico")
                return False, {}
            
            # Verificação adicional: se é pedido de gráfico após dados em formato wide
            if self._is_chart_request_incompatible(prompt, user_history):
                self.flow_path.append("formato_incompativel_para_grafico")
                return False, {}
            
            self.flow_path.append("consultando_gemini_reuso")
            reuse_decision = should_reuse_data(self.model, prompt, user_history)
            should_reuse = reuse_decision.get("should_reuse", False)
            
            if should_reuse:
                self.flow_path.append("reuso_aprovado")
                interaction_id = reuse_decision.get("interaction_id")
                if interaction_id:
                    full_data = get_interaction_full_data(interaction_id)
                    if full_data:
                        reused_interaction = next(
                            (item for item in user_history if item.get('id') == interaction_id), 
                            None
                        )
                        return True, {
                            "decision": reuse_decision,
                            "interaction": reused_interaction,
                            "full_data": full_data,
                            "interaction_id": interaction_id
                        }
            
            self.flow_path.append("reuso_negado")
            return False, {}
            
            
            
        except Exception as e:
            self.flow_path.append("erro_verificacao_reuso")
            print(f"Erro ao verificar reutilização: {e}")
            return False, {}

    def _is_chart_request_incompatible(self, prompt: str, user_history: list) -> bool:
        """Verifica se é um pedido de gráfico com dados em formato incompatível"""
        # Detecta se é pedido de gráfico
        chart_keywords = ['gráfico', 'grafico', 'chart', 'visualização', 'visualizacao', 'plotar', 'linha']
        is_chart_request = any(keyword in prompt.lower() for keyword in chart_keywords)
        
        if not is_chart_request:
            return False
        
        # Verifica se os dados mais recentes estão em formato wide (incompatível)
        if user_history:
            latest_interaction = user_history[0]  # Mais recente
            raw_data_count = latest_interaction.get('raw_data_count', 0)
            
            if raw_data_count > 0:
                # Tenta extrair informações das colunas dos dados
                try:
                    first_ten_str = latest_interaction.get('first_ten_table_lines', '[]')
                    first_ten = json.loads(first_ten_str) if isinstance(first_ten_str, str) else first_ten_str
                    
                    if first_ten and isinstance(first_ten, list) and len(first_ten) > 0:
                        columns = list(first_ten[0].keys())
                        
                        # Detecta padrão de formato wide: colunas com sufixos de ano
                        year_columns = [col for col in columns if any(year in col for year in ['2024', '2025', '_24', '_25'])]
                        
                        # Detecta formato temporal inadequado para comparação
                        temporal_columns = [col for col in columns if any(pattern in col.lower() for pattern in ['periodo_mes', 'data_mes', 'mes_ano'])]
                        
                        # Se tem múltiplas colunas com anos diferentes OU formato temporal inadequado, é incompatível
                        if len(year_columns) >= 2:
                            print(f"🔍 Detectado formato wide incompatível para gráfico: {columns}")
                            return True
                            
                        # Se tem formato temporal (YYYY-MM) mas é comparação de anos, também é incompatível
                        if temporal_columns and any(word in prompt.lower() for word in ['comparar', 'comparação', 'versus', 'vs']):
                            print(f"🔍 Detectado formato temporal inadequado para comparação: {columns}")
                            return True
                            
                except Exception as e:
                    print(f"Erro ao analisar formato de dados: {e}")
        
        return False

    def _process_reuse_flow(self, typing_placeholder, prompt: str, reuse_data: Dict) -> None:
        """Etapa 2a: Processar reutilização de dados"""
        self.flow_path.append("processando_reuso")
        
        try:
            self._start_timing("exibindo_feedback_reuso", typing_placeholder)
            # Remove a linha anterior que mostrava feedback estático
            self._end_timing("exibindo_feedback_reuso")
            
            # Prepara dados para reutilização
            self._start_timing("preparando_dados_reuso", typing_placeholder)
            serializable_data = safe_serialize_data(reuse_data["full_data"])
            reused_params = reuse_data["interaction"].get('function_params') if reuse_data["interaction"] else None
            self._end_timing("preparando_dados_reuso")
            reused_query = reuse_data["interaction"].get('query_sql') if reuse_data["interaction"] else None
            
            self.flow_path.append("refinando_resposta_reuso")
            
            # Refina resposta com base nos dados existentes
            self._start_timing("refinamento_gemini_reuso", typing_placeholder)
            refined_response, tech_details = refine_with_gemini_rag(
                self.model, prompt
            )
            self._end_timing("refinamento_gemini_reuso")
            
            # Adiciona informações de reutilização e caminho de decisão
            self._start_timing("preparando_tech_details", typing_placeholder)
            if tech_details is None:
                tech_details = {}
                
            tech_details["reuse_info"] = {
                "reused": True,
                "reason": reuse_data["decision"].get("reason", "Decisão inteligente do Gemini"),
                "original_prompt": reuse_data["interaction"].get('user_prompt') if reuse_data["interaction"] else "N/A",
                "interaction_id": reuse_data["interaction_id"]
            }
            
            tech_details["flow_path"] = " → ".join(self.flow_path)
            tech_details["timing_info"] = self.timing_info.copy()
            tech_details["total_duration"] = self._get_total_duration()
            self._end_timing("preparando_tech_details")
            
            self.flow_path.append("finalizando_reuso")
            
            # Finaliza e salva
            self._start_timing("finalizacao_reuso", typing_placeholder)
            self._finalize_response(typing_placeholder, refined_response, tech_details)
            self._save_reuse_interaction(prompt, reused_params, reused_query, refined_response, tech_details, reuse_data["interaction"])
            self._end_timing("finalizacao_reuso")
            
        except Exception as e:
            self.flow_path.append("erro_reuso")
            print(f"Erro na reutilização: {e}")
            raise Exception(f"Falha na reutilização de dados: {e}")

    def _process_new_query_flow(self, typing_placeholder, prompt: str) -> None:
        """Etapa 2b: Processar nova consulta SQL usando sistema RAG otimizado, com adaptação inteligente via Gemini"""
        self.flow_path.append("iniciando_nova_consulta_rag")

        # Recupera histórico do usuário (última pergunta válida)
        user_history = get_user_history(self.user_id)
        last_question = None
        if user_history and len(user_history) > 0:
            # Garante que pega a última pergunta do usuário correto e que não deu erro
            for interaction in user_history:
                if interaction.get('status', 'OK') == 'OK' and interaction.get('question'):
                    last_question = interaction.get('question')
                    break

        # Importa o prompt de adaptação do prompt_rules
        
        adaptation_prompt_template = get_adaptation_prompt()

        # Monta prompt para Gemini adaptar/refinar
        if last_question:
            adaptation_prompt = adaptation_prompt_template.format(
                last_question=last_question,
                nova_pergunta=prompt
            )
            # Usa Gemini para adaptar/refinar
            model = getattr(st.session_state, "model", None)
            try:
                response = model.generate_content(adaptation_prompt)
                # Extrai texto da resposta
                adapted_prompt = prompt  # fallback
                if hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and candidate.content:
                        if hasattr(candidate.content, 'parts') and candidate.content.parts:
                            part = candidate.content.parts[0]
                            if hasattr(part, 'text') and part.text and part.text.strip():
                                adapted_prompt = part.text.strip()
                print(f"[DEBUG] Adapted query: {adapted_prompt}")
            except Exception as e:
                print(f"[ERROR] Falha ao adaptar prompt via Gemini: {e}")
                adapted_prompt = prompt
        else:
            adapted_prompt = prompt

        # Usa sistema RAG diretamente com a pergunta adaptada
        self._start_timing("processamento_rag", typing_placeholder)
        self.flow_path.append("usando_sistema_rag")
        response = refine_with_gemini_rag(self.model, adapted_prompt, self.user_id)
        if isinstance(response, tuple) and len(response) == 2:
            _, tech_details = response
            self._last_rag_tech_details = tech_details
        else:
            self._last_rag_tech_details = None
        self._end_timing("processamento_rag")
        self._handle_gemini_response(typing_placeholder, adapted_prompt, response)
        # Salva a interação apenas se não houve erro
        if self._last_rag_tech_details and self._last_rag_tech_details.get('response_type', '') != 'error':
            from utils.cache import save_interaction
            save_interaction(
                user_id=self.user_id,
                question=adapted_prompt,
                function_params=None,
                query_sql=None,
                raw_data=None,
                raw_response=None,
                refined_response=None,
                tech_details=None,
                status="OK"
            )

    def _handle_gemini_response(self, typing_placeholder, prompt: str, response) -> None:
    # Loga o objeto de retorno e seu tipo para diagnóstico
        """Etapa 3: Processar resposta do Gemini"""
        self.flow_path.append("processando_resposta_gemini")
        
        try:
            # Para resposta no formato tuple (text, tech_details) - novo formato RAG
            if isinstance(response, tuple):
                text_response, tech_details = response
                # Garante que prompt/token info esteja sempre em tech_details
                if tech_details is not None:
                    if ("optimized_prompt" not in tech_details or "prompt_tokens" not in tech_details):
                        last_interaction = None
                        if hasattr(st.session_state, "chat_history") and st.session_state.chat_history:
                            for msg in reversed(st.session_state.chat_history):
                                if "tech_details" in msg and "optimized_prompt" in msg["tech_details"]:
                                    last_interaction = msg["tech_details"]
                                    break
                        if last_interaction:
                            for k in ["optimized_prompt", "prompt_tokens", "completion_tokens", "total_tokens"]:
                                if k in last_interaction and k not in tech_details:
                                    tech_details[k] = last_interaction[k]
                # Se vier dict, processa normalmente
                if isinstance(text_response, dict):
                    class MockFunctionCall:
                        def __init__(self, args):
                            self.args = args
                    self._process_function_call(typing_placeholder, prompt, MockFunctionCall(text_response))
                    return
                # Se vier objeto com .args, processa normalmente
                elif hasattr(text_response, 'args'):
                    self._process_function_call(typing_placeholder, prompt, text_response)
                    return
                # Se vier string (mesmo dentro de tuple), tenta parsear como JSON removendo markdown
                elif isinstance(text_response, str):
                    cleaned = text_response.strip()
                    if cleaned.startswith('```json'):
                        cleaned = cleaned[len('```json'):].strip()
                    elif cleaned.startswith('```'):
                        cleaned = cleaned[len('```'):].strip()
                    if cleaned.endswith('```'):
                        cleaned = cleaned[:-3].strip()
                    try:
                        import json
                        params_dict = json.loads(cleaned)
                        class MockFunctionCall:
                            def __init__(self, args):
                                self.args = args
                        self._process_function_call(typing_placeholder, prompt, MockFunctionCall(params_dict))
                        return
                    except Exception as e:
                        print(f"[ERROR] Falha ao parsear string retornada pelo modelo como JSON: {repr(text_response)} (type={type(text_response)}) | Erro: {e}")
                        # Erro de parsing simples: loga, mas não reinicializa sistema RAG
                        self._handle_error(typing_placeholder, prompt, f"Resposta do modelo em string inválida para function_call: {type(text_response)}", None, critical=False)
                        return
                else:
                    print(f"[ERROR] Resposta do modelo em formato inválido para function_call: {repr(text_response)} (type={type(text_response)})")
                    self._handle_error(typing_placeholder, prompt, f"Resposta do modelo em formato inválido para function_call: {type(text_response)}", None, critical=True)
                    return
            elif isinstance(response, dict):
                class MockFunctionCall:
                    def __init__(self, args):
                        self.args = args
                self._process_function_call(typing_placeholder, prompt, MockFunctionCall(response))
                return
            elif hasattr(response, 'args'):
                self._process_function_call(typing_placeholder, prompt, response)
                return
            else:
                # Loga erro e aborta
                print(f"[ERROR] Resposta do modelo em formato inválido para function_call: {repr(response)} (type={type(response)})")
                self._handle_error(typing_placeholder, prompt, f"Resposta do modelo em formato inválido para function_call: {type(response)}", None)
                return
                
        except Exception as e:
            self.flow_path.append("erro_processamento_gemini")
            self._handle_error(typing_placeholder, prompt, f"Erro ao processar resposta Gemini: {str(e)}", traceback.format_exc())
            traceback.print_exc()

    def _process_function_call(self, typing_placeholder, prompt: str, function_call) -> None:
        """Etapa 4: Processar chamada de função (SQL)"""
        self.flow_path.append("processando_function_call")
        
        try:
            self._start_timing("preparacao_parametros", typing_placeholder)
            params = function_call.args

            # Dupla serialização para garantir que não há FunctionCall
            serializable_params = safe_serialize_gemini_params(params)
            serializable_params = safe_serialize_gemini_params(serializable_params)

            self._end_timing("preparacao_parametros")


            self.flow_path.append("construindo_query")

            self._start_timing("construcao_query", typing_placeholder)
            try:
                query = build_query(serializable_params)
            except ValueError as ve:
                # Erro específico de CTE sem from_table correto
                error_msg = str(ve)
                if "CTE" in error_msg and "from_table" in error_msg:
                    typing_placeholder.empty()
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": f"❌ Erro crítico: {error_msg}"
                    })
                    st.rerun()
                    return
                else:
                    raise
            self._end_timing("construcao_query")

            self.flow_path.append("executando_query")
            self._start_timing("execucao_sql", typing_placeholder)
            raw_data = execute_query(query)
            self._end_timing("execucao_sql")

            if isinstance(raw_data, dict) and "error" in raw_data:
                self._handle_query_error(typing_placeholder, prompt, raw_data, query, serializable_params)
                return

            self.flow_path.append("processando_dados")

            # Converte os dados para formato serializável
            self._start_timing("serializacao_dados", typing_placeholder)
            serializable_data = safe_serialize_data(raw_data)
            self._end_timing("serializacao_dados")

            self.flow_path.append("refinando_resposta_final")

            # Chama Gemini para análise final dos dados
            self._start_timing("refinamento_gemini_final", typing_placeholder)


            from llm_handlers.gemini_handler import analyze_data_with_gemini

            # Salva prompt/token info do refine_with_gemini_rag (se disponível)
            initial_prompt_info = {}
            if hasattr(self, "_last_rag_tech_details") and self._last_rag_tech_details:
                for k in ["optimized_prompt", "prompt_tokens", "completion_tokens", "total_tokens", "rag_context", "sql_guidance", "model_used", "prompt_type", "function_call_name"]:
                    if k in self._last_rag_tech_details:
                        initial_prompt_info[k] = self._last_rag_tech_details[k]

            refined_response, tech_details = analyze_data_with_gemini(
                prompt=prompt,
                data=serializable_data,
                function_params=function_call.args if hasattr(function_call, 'args') else {},
                query=query
            )

            self._end_timing("refinamento_gemini_final")

            # Adiciona caminho de decisão aos detalhes técnicos
            self._start_timing("preparando_tech_details_final", typing_placeholder)
            if tech_details is None:
                tech_details = {}
            # Merge prompt/token info if not present
            for k, v in initial_prompt_info.items():
                if k not in tech_details:
                    tech_details[k] = v
            tech_details["flow_path"] = " → ".join(self.flow_path)
            tech_details["timing_info"] = self.timing_info.copy()
            tech_details["total_duration"] = self._get_total_duration()
            self._end_timing("preparando_tech_details_final")

            self.flow_path.append("salvando_interacao")

            # Salva a interação no cache
            self._start_timing("salvamento_interacao", typing_placeholder)
            self._save_new_interaction(prompt, serializable_params, query, serializable_data, refined_response, tech_details)
            self._end_timing("salvamento_interacao")

            self.flow_path.append("finalizando_nova_consulta")

            # Finaliza resposta
            self._start_timing("finalizacao_nova_consulta", typing_placeholder)
            self._finalize_response(typing_placeholder, refined_response, tech_details)
            self._end_timing("finalizacao_nova_consulta")

            # Log de sucesso
            self._log_success(prompt, serializable_params, query, serializable_data, refined_response, tech_details)

        except Exception as e:
            self.flow_path.append("erro_function_call")
            self._handle_error(typing_placeholder, prompt, f"Erro no processamento da função: {str(e)}", traceback.format_exc())


    def _handle_query_error(self, typing_placeholder, prompt: str, raw_data: Dict, query: str, serializable_params: Dict) -> None:
        """Trata erros de execução da query - tenta refinar com Gemini antes de falhar"""
        self.flow_path.append("erro_execucao_query")
        
        error_message = raw_data['error']
        error_details = f"Query Error: {error_message}"
        failed_query = raw_data.get('query', 'N/A')
        
        print(f"\n❌ Erro SQL detectado: {error_message}")
        print(f"📋 Query que falhou: {failed_query}")
        
        # TENTA REFINAR COM GEMINI ANTES DE FALHAR
        print(f"🔄 [REFINAMENTO] Tentando refinar SQL com Gemini...")
        self.flow_path.append("tentando_refinar_erro_sql")
        self._start_timing("refinamento_erro_gemini", typing_placeholder)
        
        try:
            from llm_handlers.gemini_handler import refine_sql_with_error
            
            # Tenta refinar - passa prompt original, erro, e SQL que falhou
            refined_result, refined_tech_details = refine_sql_with_error(
                model=self.model,
                user_question=prompt,
                error_message=error_message,
                previous_sql=failed_query,
                table_name="unknown"  # Não sabemos a tabela em produção, mas Gemini tem contexto
            )
            
            self._end_timing("refinamento_erro_gemini")
            
            if refined_result and isinstance(refined_result, dict):
                print(f"✅ Gemini retornou SQL refinada")
                self.flow_path.append("executando_sql_refinada")
                
                # Tenta executar a SQL refinada
                self._start_timing("execucao_sql_refinada", typing_placeholder)
                try:
                    from database.query_builder import build_query, execute_query
                    
                    refined_query = build_query(refined_result)
                    raw_data_retry = execute_query(refined_query)
                    
                    self._end_timing("execucao_sql_refinada")
                    
                    if isinstance(raw_data_retry, dict) and "error" not in raw_data_retry:
                        print(f"✅ SQL refinada PASSOU! Continuando com resultado...")
                        self.flow_path.append("sucesso_sql_refinada")
                        
                        # Converte dados para formato serializável
                        serializable_data = safe_serialize_data(raw_data_retry)
                        
                        # Refina resposta com Gemini
                        from llm_handlers.gemini_handler import analyze_data_with_gemini
                        refined_response, tech_details = analyze_data_with_gemini(
                            prompt=prompt,
                            data=serializable_data,
                            function_params=refined_result,
                            query=refined_query
                        )
                        
                        # Adiciona info de refinamento aos tech_details
                        if refined_tech_details:
                            tech_details.update(refined_tech_details)
                        tech_details["retry_successful"] = True
                        tech_details["original_error"] = error_message
                        tech_details["original_query"] = failed_query
                        
                        self._finalize_response(typing_placeholder, refined_response, tech_details)
                        self._save_new_interaction(prompt, refined_result, refined_query, serializable_data, refined_response, tech_details)
                        return
                    else:
                        # SQL refinada também falhou
                        retry_error = raw_data_retry.get("error", "Desconhecido") if isinstance(raw_data_retry, dict) else str(raw_data_retry)
                        print(f"❌ SQL refinada também falhou: {retry_error}")
                        self.flow_path.append("sql_refinada_tambem_falhou")
                except Exception as e:
                    print(f"❌ Erro ao executar SQL refinada: {e}")
                    self.flow_path.append("erro_executar_sql_refinada")
            
        except Exception as e:
            print(f"⚠️  Erro ao tentar refinar SQL: {e}")
            self.flow_path.append("erro_refinar_sql")
        
        # Se não conseguiu refinar ou refinar também falhou, loga e retorna erro
        print(f"❌ Falha final: não foi possível refinar ou SQL refinada também falhou")
        
        log_interaction(
            user_input=prompt,
            function_params=serializable_params,
            query=query,
            raw_data=None,
            raw_response=None,
            refined_response=STANDARD_ERROR_MESSAGE,
            first_ten_table_lines=None,
            graph_data=None,
            export_data=None,
            status="ERROR",
            status_msg=f"{error_details} | Query: {failed_query}",
            client_request_count=self.rate_limiter.state["count"],
            custom_fields={
                "error_type": "query_execution_error",
                "error_details": error_message,
                "failed_query": failed_query,
                "flow_path": " → ".join(self.flow_path)
            }
        )
        
        log_error(
            user_id=self.user_id,
            error_type="query_execution_error",
            error_message=error_details,
            context=f"User request: {prompt} | Failed Query: {failed_query} | Function params: {serializable_params} | Flow: {' → '.join(self.flow_path)}",
            traceback=error_message
        )
        
        typing_placeholder.empty()
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": format_text_with_ia_highlighting(STANDARD_ERROR_MESSAGE),
        })
        st.rerun()

    def _process_direct_response(self, typing_placeholder, response, tech_details=None) -> None:
        """Processa resposta direta sem função"""
        self.flow_path.append("extraindo_texto_resposta")
        typing_placeholder.empty()
        # Extração segura do texto da resposta
        response_text = self._extract_response_text(response)
        # Atualiza histórico
        message = {
            "role": "assistant",
            "content": format_text_with_ia_highlighting(response_text)
        }
        if tech_details:
            message["tech_details"] = tech_details
        else:
            message["tech_details"] = {"flow_path": " → ".join(self.flow_path)}
        st.session_state.chat_history.append(message)
        st.rerun()

    def _finalize_response(self, typing_placeholder, response_text: str, tech_details: Dict = None) -> None:
        """Finaliza resposta e atualiza interface"""
        typing_placeholder.empty()
        
        # Remove instruções técnicas do texto antes de salvar
        content = slugfy_response(response_text)
        for marker in ["GRAPH-TYPE:", "EXPORT-INFO:", "dt:"]:
            if marker in content:
                content = content.split(marker)[0].strip()
        
        message_data = {
            "role": "assistant",
            "content": format_text_with_ia_highlighting(content)
        }
        
        if tech_details:
            message_data["tech_details"] = tech_details
        
        st.session_state.chat_history.append(message_data)
        st.rerun()

    def _save_new_interaction(self, prompt: str, serializable_params: Dict, query: str, serializable_data: Any, refined_response: str, tech_details: Dict) -> None:
        """Salva nova interação no cache"""
        try:
            # Garantir serialização final antes de salvar
            final_params = safe_serialize_gemini_params(serializable_params)
            
            save_interaction(
                user_id=self.user_id,
                question=prompt,
                function_params=final_params,
                query_sql=query,
                raw_data=serializable_data,
                raw_response=None,
                refined_response=refined_response,
                tech_details=safe_serialize_tech_details(tech_details),
                status="OK"
            )
        except Exception as e:
            print(f"Erro ao salvar nova interação: {e}")
            print(f"Tipo de serializable_params: {type(serializable_params)}")
            if hasattr(serializable_params, '__dict__'):
                print(f"Conteúdo de serializable_params: {serializable_params.__dict__}")
            else:
                print(f"Conteúdo de serializable_params: {serializable_params}")
            import traceback
            traceback.print_exc()

    def _save_reuse_interaction(self, prompt: str, reused_params: Dict, reused_query: str, refined_response: str, tech_details: Dict, reused_interaction: Dict) -> None:
        """Salva interação de reutilização no cache"""
        try:
            save_interaction(
                user_id=self.user_id,
                question=prompt,
                function_params=safe_serialize_gemini_params(reused_params),
                query_sql=reused_query,
                raw_data=st.session_state.get("current_interaction", {}).get("serializable_data"),
                raw_response=None,
                refined_response=refined_response,
                tech_details=safe_serialize_tech_details(tech_details),
                status="OK",
                reused_from=reused_interaction.get('user_prompt') if reused_interaction else "N/A"
            )
        except Exception as e:
            print(f"Erro ao salvar interação de reutilização: {e}")

    def _log_success(self, prompt: str, serializable_params: Dict, query: str, serializable_data: Any, refined_response: str, tech_details: Dict) -> None:
        """Log de interação bem-sucedida"""
        log_interaction(
            user_input=prompt,
            function_params=serializable_params,
            query=query,
            raw_data=serializable_data,
            raw_response=None,
            refined_response=refined_response,
            first_ten_table_lines=serializable_data[:10] if serializable_data else None,
            graph_data=tech_details.get("chart_info") if tech_details and tech_details.get("chart_info") else None,
            export_data=tech_details.get("export_info") if tech_details and tech_details.get("export_info") else None,
            status="OK",
            status_msg="Consulta processada com sucesso.",
            client_request_count=self.rate_limiter.state["count"],
            custom_fields={"flow_path": " → ".join(self.flow_path)}
        )

    def _log_validation_error(self, prompt: str, error_type: str, error_msg: str, serializable_params: Dict, custom_fields: Dict = None) -> None:
        """Log de erro de validação"""
        base_custom_fields = {
            "error_type": error_type,
            "function_params": str(serializable_params),
            "flow_path": " → ".join(self.flow_path)
        }
        if custom_fields:
            base_custom_fields.update(custom_fields)
        
        log_interaction(
            user_input=prompt,
            function_params=serializable_params,
            query=None,
            raw_data=None,
            raw_response=None,
            refined_response=STANDARD_ERROR_MESSAGE,
            first_ten_table_lines=None,
            graph_data=None,
            export_data=None,
            status="ERROR",
            status_msg=error_msg,
            client_request_count=self.rate_limiter.state["count"],
            custom_fields=base_custom_fields
        )
        
        log_error(
            user_id=self.user_id,
            error_type=error_type,
            error_message=error_msg,
            context=f"User request: {prompt} | Function params: {serializable_params} | Flow: {' → '.join(self.flow_path)}",
            traceback="N/A - Validation error"
        )
        
        # Remove animação e mostra erro ao usuário
        st.session_state.chat_history.append({
            "role": "assistant", 
            "content": format_text_with_ia_highlighting(STANDARD_ERROR_MESSAGE)
        })
        st.rerun()

    def _handle_error(self, typing_placeholder, prompt: str, error_msg: str, tb: str) -> None:
        """Tratamento centralizado de erros"""
        self.flow_path.append("tratamento_erro")
        
        # Log no BigQuery e DuckDB
        log_interaction(
            user_input=prompt,
            function_params=None,
            query=None,
            raw_data=None,
            raw_response=None,
            refined_response=STANDARD_ERROR_MESSAGE,
            first_ten_table_lines=None,
            graph_data=None,
            export_data=None,
            status="ERROR",
            status_msg=error_msg,
            client_request_count=self.rate_limiter.state["count"],
            custom_fields={
                "error_type": "general_exception",
                "error_details": error_msg,
                "flow_path": " → ".join(self.flow_path)
            }
        )
        
        log_error(
            user_id=self.user_id,
            error_type="general_exception",
            error_message=error_msg,
            context=f"User request: {prompt} | Flow: {' → '.join(self.flow_path)}",
            traceback=tb
        )
        
        typing_placeholder.empty()
        st.session_state.chat_history.append({
            "role": "assistant", 
            "content": format_text_with_ia_highlighting(STANDARD_ERROR_MESSAGE)
        })
        st.rerun()

    def _extract_response_text(self, response) -> str:
        """Extrai texto de forma segura da resposta do Gemini"""
        try:
            if hasattr(response, 'text'):
                return response.text
            elif hasattr(response, 'parts') and response.parts:
                text_parts = []
                for part in response.parts:
                    if hasattr(part, 'text') and part.text:
                        text_parts.append(part.text)
                return ' '.join(text_parts) if text_parts else str(response)
            else:
                return str(response)
        except (ValueError, AttributeError) as e:
            print(f"Erro ao extrair texto da resposta: {e}")
            return "Resposta processada, mas não foi possível exibir o conteúdo completo."
    
    def _handle_text_response(self, typing_placeholder, prompt: str, text_response: str, tech_details: dict = None) -> None:
        """Processa resposta em texto do modelo (sem function call)"""
        self.flow_path.append("processando_resposta_texto")
        try:
            typing_placeholder.empty()
            td = tech_details if tech_details is not None else {"response_type": "text_only", "flow_path": " → ".join(self.flow_path)}
            save_interaction(
                user_id=self.user_id,
                question=prompt,
                function_params=None,
                query_sql=None,
                raw_data=None,
                raw_response=text_response,
                refined_response=text_response,
                tech_details=td,
                status="TEXT_RESPONSE"
            )
            formatted_response = format_text_with_ia_highlighting(text_response)
            td_hist = dict(td)
            td_hist["total_time_ms"] = self._get_total_duration()
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": formatted_response,
                "tech_details": td_hist
            })
            st.rerun()
        except Exception as e:
            self.flow_path.append("erro_resposta_texto")
            self._handle_error(typing_placeholder, prompt, f"Erro ao processar resposta texto: {str(e)}", traceback.format_exc())