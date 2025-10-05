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

from cache_db import get_user_history, get_interaction_full_data, save_interaction, log_error
from gemini_handler import should_reuse_data, refine_with_gemini
from database import build_query, execute_query
from utils import (
    safe_serialize_gemini_params, 
    safe_serialize_data, 
    safe_serialize_tech_details,
    format_text_with_ia_highlighting,
    slugfy_response
)
from config import STANDARD_ERROR_MESSAGE, PROJECT_ID, DATASET_ID, TABLES_CONFIG
from logger import log_interaction
from deepseek_theme import show_typing_animation, show_dynamic_processing_animation, get_step_display_info


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
        self.flow_path = []  # Para rastrear o caminho seguido
        self.timing_info = {}  # Para rastrear timing de cada etapa
        self.start_time = None
        
    def process_message(self, prompt: str, typing_placeholder) -> None:
        """
        Processa uma mensagem seguindo o fluxo definido:
        1. Verificar reutilização
        2. Se não reutilizar: converter para SQL
        3. Executar query no DB
        4. Processar resposta + gráficos/export
        """
        try:
            self.flow_path = ["início"]
            self._start_timing("processo_completo", typing_placeholder)
            
            # Etapa 1: Verificar oportunidade de reutilização
            self._start_timing("verificacao_reuso", typing_placeholder)
            should_reuse, reuse_data = self._check_reuse_opportunity(prompt)
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
            self.flow_path.append("erro_geral")
            self._handle_error(typing_placeholder, prompt, str(e), traceback.format_exc())

    def _check_reuse_opportunity(self, prompt: str) -> Tuple[bool, Dict]:
        """Etapa 1: Verificar se pode reutilizar dados anteriores"""
        self.flow_path.append("verificando_reuso")
        
        try:
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
            refined_response, tech_details = refine_with_gemini(
                prompt, serializable_data, reused_params, reused_query
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
            self.flow_path.append("erro_reuso_fallback")
            print(f"Erro na reutilização: {e}")
            typing_placeholder.markdown(
                "<div style='padding: 8px 12px; color: #f59e0b; font-size: 14px; opacity: 0.8;'>⚠️ Reutilização falhou, fazendo nova consulta...</div>", 
                unsafe_allow_html=True
            )
            self._process_new_query_flow(typing_placeholder, prompt)

    def _process_new_query_flow(self, typing_placeholder, prompt: str) -> None:
        """Etapa 2b: Processar nova consulta SQL"""
        self.flow_path.append("iniciando_nova_consulta")
        
        try:
            # Inicia conversa com histórico limpo
            self._start_timing("preparando_conversa_gemini", typing_placeholder)
            convo = self.model.start_chat(
                history=[
                    {"role": "model" if m["role"] == "assistant" else m["role"], "parts": [m["content"]]}
                    for m in st.session_state.chat_history
                    if m["role"] != "assistant" or not m.get("tech_details")
                ]
            )
            self._end_timing("preparando_conversa_gemini")
            
            self.flow_path.append("enviando_para_gemini")
            self._start_timing("envio_gemini_inicial", typing_placeholder)
            response = convo.send_message(prompt)
            self._end_timing("envio_gemini_inicial")
            
            self._handle_gemini_response(typing_placeholder, prompt, response)
            
        except Exception as e:
            self.flow_path.append("erro_nova_consulta")
            self._handle_error(typing_placeholder, prompt, f"Erro ao processar nova consulta: {str(e)}", traceback.format_exc())

    def _handle_gemini_response(self, typing_placeholder, prompt: str, response) -> None:
        """Etapa 3: Processar resposta do Gemini"""
        self.flow_path.append("processando_resposta_gemini")
        
        try:
            # Verificação defensiva da resposta
            self._start_timing("validacao_resposta_gemini")
            if not response or not response.candidates:
                raise ValueError("Resposta inválida do modelo - sem candidatos")
            
            candidate = response.candidates[0]
            if not candidate or not candidate.content or not candidate.content.parts:
                raise ValueError("Resposta inválida do modelo - estrutura incompleta")
            self._end_timing("validacao_resposta_gemini")

            # Verifica se há chamada de função
            self._start_timing("analise_tipo_resposta")
            first_part = candidate.content.parts[0]
            self._end_timing("analise_tipo_resposta")
            
            if hasattr(first_part, 'function_call') and first_part.function_call:
                self.flow_path.append("function_call_detectado")
                self._process_function_call(typing_placeholder, prompt, first_part.function_call)
            else:
                self.flow_path.append("resposta_direta")
                self._process_direct_response(typing_placeholder, response)
                
        except Exception as e:
            self.flow_path.append("erro_processamento_gemini")
            self._handle_error(typing_placeholder, prompt, f"Erro ao processar resposta Gemini: {str(e)}", traceback.format_exc())

    def _process_function_call(self, typing_placeholder, prompt: str, function_call) -> None:
        """Etapa 4: Processar chamada de função (SQL)"""
        self.flow_path.append("processando_function_call")
        
        try:
            self._start_timing("preparacao_parametros", typing_placeholder)
            params = function_call.args
            serializable_params = safe_serialize_gemini_params(params)
            self._end_timing("preparacao_parametros")
            
            # Validar full_table_id
            self._start_timing("validacao_table_id", typing_placeholder)
            full_table_id = serializable_params.get("full_table_id")
            if not self._validate_table_id(full_table_id, prompt, serializable_params):
                return
            self._end_timing("validacao_table_id")
            
            self.flow_path.append("construindo_query")
            
            # Construir e executar query
            self._start_timing("construcao_query", typing_placeholder)
            query = build_query(serializable_params)
            self._end_timing("construcao_query")
            
            self.flow_path.append("executando_query")
            self._start_timing("execucao_sql", typing_placeholder)
            raw_data = execute_query(query)
            self._end_timing("execucao_sql")

            if "error" in raw_data:
                self._handle_query_error(typing_placeholder, prompt, raw_data, query, serializable_params)
                return
            
            self.flow_path.append("processando_dados")
            
            # Converte os dados para formato serializável
            self._start_timing("serializacao_dados", typing_placeholder)
            serializable_data = safe_serialize_data(raw_data)
            self._end_timing("serializacao_dados")

            self.flow_path.append("refinando_resposta_final")
            
            # Refina a resposta com o Gemini
            self._start_timing("refinamento_gemini_final", typing_placeholder)
            refined_response, tech_details = refine_with_gemini(
                prompt, serializable_data, serializable_params, query
            )
            self._end_timing("refinamento_gemini_final")
            
            # Adiciona caminho de decisão aos detalhes técnicos
            self._start_timing("preparando_tech_details_final", typing_placeholder)
            if tech_details is None:
                tech_details = {}
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

    def _validate_table_id(self, full_table_id: str, prompt: str, serializable_params: Dict) -> bool:
        """Valida se o full_table_id é válido"""
        if not full_table_id:
            self.flow_path.append("erro_table_id_ausente")
            error_msg = f"full_table_id ausente nos parâmetros: {serializable_params}"
            self._log_validation_error(prompt, "missing_table_id", error_msg, serializable_params)
            return False
        
        expected_full_table_ids = [f"{PROJECT_ID}.{DATASET_ID}.{table_name}" for table_name in TABLES_CONFIG.keys()]
        if full_table_id not in expected_full_table_ids:
            self.flow_path.append("erro_table_id_invalido")
            error_msg = f"Invalid full_table_id: {full_table_id} | Available tables: {expected_full_table_ids}"
            self._log_validation_error(prompt, "invalid_full_table_id", error_msg, serializable_params, {"requested_full_table_id": full_table_id, "available_full_table_ids": expected_full_table_ids})
            return False
            
        return True

    def _handle_query_error(self, typing_placeholder, prompt: str, raw_data: Dict, query: str, serializable_params: Dict) -> None:
        """Trata erros de execução da query"""
        self.flow_path.append("erro_execucao_query")
        
        error_details = f"Query Error: {raw_data['error']}"
        failed_query = raw_data.get('query', 'N/A')
        
        # Log no BigQuery e DuckDB
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
                "error_details": raw_data['error'],
                "failed_query": failed_query,
                "flow_path": " → ".join(self.flow_path)
            }
        )
        
        log_error(
            user_id=self.user_id,
            error_type="query_execution_error",
            error_message=error_details,
            context=f"User request: {prompt} | Failed Query: {failed_query} | Function params: {serializable_params} | Flow: {' → '.join(self.flow_path)}",
            traceback=raw_data['error']
        )
        
        typing_placeholder.empty()
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": format_text_with_ia_highlighting(STANDARD_ERROR_MESSAGE),
        })
        st.rerun()

    def _process_direct_response(self, typing_placeholder, response) -> None:
        """Processa resposta direta sem função"""
        self.flow_path.append("extraindo_texto_resposta")
        
        typing_placeholder.empty()
        
        # Extração segura do texto da resposta
        response_text = self._extract_response_text(response)
        
        # Atualiza histórico
        st.session_state.chat_history.append({
            "role": "assistant", 
            "content": format_text_with_ia_highlighting(response_text),
            "tech_details": {"flow_path": " → ".join(self.flow_path)}
        })
        
        st.rerun()

    def _finalize_response(self, typing_placeholder, response_text: str, tech_details: Dict = None) -> None:
        """Finaliza resposta e atualiza interface"""
        typing_placeholder.empty()
        
        message_data = {
            "role": "assistant",
            "content": format_text_with_ia_highlighting(slugfy_response(response_text))
        }
        
        if tech_details:
            message_data["tech_details"] = tech_details
            
        st.session_state.chat_history.append(message_data)
        st.rerun()

    def _save_new_interaction(self, prompt: str, serializable_params: Dict, query: str, serializable_data: Any, refined_response: str, tech_details: Dict) -> None:
        """Salva nova interação no cache"""
        try:
            save_interaction(
                user_id=self.user_id,
                question=prompt,
                function_params=serializable_params,
                query_sql=query,
                raw_data=serializable_data,
                raw_response=None,
                refined_response=refined_response,
                tech_details=safe_serialize_tech_details(tech_details),
                status="OK"
            )
        except Exception as e:
            print(f"Erro ao salvar nova interação: {e}")

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