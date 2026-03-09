"""
Conversational Analytics Handler
=================================
Handler para análise usando Google Cloud Gemini Data Analytics API.
Fluxo: pergunta → cria/acessa agente → cria conversa → chat com streaming → processa resposta

Retorna: Tuple[str, Dict] = (summary, tech_details) compatível com MessageHandler
"""

from typing import Tuple, Dict, Any, List
from datetime import datetime
import os
import uuid
import re
from google.cloud import geminidataanalytics
import pandas as pd
import altair as alt
import json

# Config
from config.settings import PROJECT_ID, DATASET_ID


class ConversationalAnalyticsHandler:
    """Handler para Conversational Analytics usando Google Cloud SDK.
    
    Fluxo:
    1. Inicializa clients (DataAgentServiceClient, DataChatServiceClient)
    2. Cria ou acessa agente com instruções e datasources
    3. Cria ou acessa conversa
    4. Envia pergunta e processa resposta em streaming
    5. Retorna (summary, tech_details) com dados e gráficos
    """
    
    AGENT_ID = "agent_8f51992b-552c-4778-9790-b619f8196dc5"
    LOCATION = "global"
    
    def __init__(self, project_id: str, dataset_id: str, user_id: str = "default"):
        """Inicializa handler com clients Google Cloud."""
        self.user_id = user_id
        self.project_id = project_id
        self.dataset_id = dataset_id
        
        # Force project ID para cloudaicompanion
        os.environ['GOOGLE_CLOUD_PROJECT'] = project_id
        
        # Clients
        self.data_agent_client = geminidataanalytics.DataAgentServiceClient()
        self.data_chat_client = geminidataanalytics.DataChatServiceClient()
        
        # ID da conversa único por sessão
        self.conversation_id = f"conv_{uuid.uuid4().hex[:8]}"
        
        # Armazena mensagens de resposta
        self.response_messages = []
        self.response_data = {
            "text": "",
            "schema": None,
            "query": None,
            "generated_sql": "",
            "data": None,
            "chart": None,
            "rows": []
        }
        
        print(f"✅ Handler inicializado")
        print(f"   Project: {self.project_id}")
        print(f"   Dataset: {self.dataset_id}")
        print(f"   Agent: {self.AGENT_ID}")
        print(f"   Conversation: {self.conversation_id}")
    
    def _get_or_create_agent(self) -> str:
        """Obtém ou cria agente com contexto configurado."""
        agent_path = self.data_agent_client.data_agent_path(
            self.project_id, self.LOCATION, self.AGENT_ID
        )
        
        try:
            # Tenta acessar agente existente
            request = geminidataanalytics.GetDataAgentRequest(name=agent_path)
            agent = self.data_agent_client.get_data_agent(request=request)
            print(f"✅ Agente existente encontrado: {self.AGENT_ID}")
            return agent_path
        except Exception as e:
            print(f"⚠️ Agente não existe, tentando criar: {e}")
            return self._create_agent()
    
    def _create_agent(self) -> str:
        """Cria novo agente com system instructions e datasources."""
        # System instruction - em PT-BR para respostas em português
        system_instruction = f"""
Você é um analista de dados especializado no dataset {self.dataset_id}.
Seu papel é ajudar a analisar dados e responder perguntas sobre {self.dataset_id}.

IMPORTANTE - RESPONDA SEMPRE EM PORTUGUÊS BRASILEIRO:
- Seu pensamento deve ser em português-brasileiro
- Sua resposta deve ser em português-brasileiro
- Não use inglês em nenhuma parte da resposta

Forneça insights claros e acionáveis com base nos dados.
Quando apropriado, gere consultas SQL e visualizações.
Sempre explique sua análise e metodologia.
Seja conciso mas detalhado em suas explicações."""
        
        # BigQuery datasources
        bq_table = geminidataanalytics.BigQueryTableReference(
            project_id=self.project_id,
            dataset_id=self.dataset_id,
            table_id="*"  # Todas as tabelas do dataset
        )
        
        datasource_references = geminidataanalytics.DatasourceReferences(
            bq=geminidataanalytics.BigQueryTableReferences(
                table_references=[bq_table]
            )
        )
        
        # Context setup
        published_context = geminidataanalytics.Context(
            system_instruction=system_instruction,
            datasource_references=datasource_references,
            options=geminidataanalytics.ConversationOptions(
                analysis=geminidataanalytics.AnalysisOptions(
                    python=geminidataanalytics.AnalysisOptions.Python(
                        enabled=False
                    )
                )
            ),
        )
        
        # Data Agent
        data_agent = geminidataanalytics.DataAgent(
            data_analytics_agent=geminidataanalytics.DataAnalyticsAgent(
                published_context=published_context
            ),
        )
        
        # Cria agente
        request = geminidataanalytics.CreateDataAgentRequest(
            parent=f"projects/{self.project_id}/locations/{self.LOCATION}",
            data_agent_id=self.AGENT_ID,
            data_agent=data_agent,
        )
        
        response = self.data_agent_client.create_data_agent(request=request)
        print(f"✅ Agente criado: {self.AGENT_ID}")
        return self.data_agent_client.data_agent_path(
            self.project_id, self.LOCATION, self.AGENT_ID
        )
    
    def _setup_conversation(self) -> str:
        """Cria ou obtém conversa existente."""
        try:
            # Tenta acessar conversa existente
            conv_path = self.data_chat_client.conversation_path(
                self.project_id, self.LOCATION, self.conversation_id
            )
            self.data_chat_client.get_conversation(name=conv_path)
            print(f"✅ Conversa existente: {self.conversation_id}")
            return conv_path
        except Exception:
            # Cria nova conversa
            agent_path = self._get_or_create_agent()
            
            conversation = geminidataanalytics.Conversation(
                agents=[agent_path],
            )
            
            request = geminidataanalytics.CreateConversationRequest(
                parent=f"projects/{self.project_id}/locations/{self.LOCATION}",
                conversation_id=self.conversation_id,
                conversation=conversation,
            )
            
            self.data_chat_client.create_conversation(request=request)
            print(f"✅ Conversa criada: {self.conversation_id}")
            
            return self.data_chat_client.conversation_path(
                self.project_id, self.LOCATION, self.conversation_id
            )
    
    def _parse_thinking_and_response(self, text: str) -> Tuple[str, str]:
        """
        Separa pensamentos (thinking) de resposta final.
        Retorna: (thinking, response)
        
        IMPORTANTE: Se detectar pensamento em inglês, returna só a resposta
        """
        if not text.strip():
            return "", ""
        
        lines = text.split('\n')
        
        # Padrões de pensamento em português
        pt_thinking_patterns = [
            'analisando', 'calculando', 'pensando', 'verificando',
            'consultando', 'procurando', 'gerando', 'processando',
            'buscando', 'investigando', 'determinando', 'entendendo',
            'interpretando', 'extraindo', 'montando', 'criando',
            'executando', 'recuperando', 'identificando', 'detectando',
            'processados', 'extraído', 'gerado', 'criado'
        ]
        
        # Padrões em inglês (para ignorar)
        en_thinking_patterns = [
            'analyzing', 'calculating', 'thinking', 'checking',
            'consulting', 'searching', 'generating', 'processing',
            'finding', 'investigating', 'determining', 'understanding',
            'interpreting', 'extracting', 'building', 'creating',
            'executing', 'retrieving', 'identifying', 'detecting'
        ]
        
        thinking_lines = []
        response_lines = []
        
        # Limita a procura apenas nas primeiras 3 linhas
        max_thinking_lines = 2
        lines_found = 0
        found_english = False
        
        for i, line in enumerate(lines):
            lower_line = line.lower().strip()
            
            # Para se já encontrou thinking suficiente
            if lines_found >= max_thinking_lines:
                response_lines.append(line)
                continue
            
            # Detecta padrões em inglês
            if any(pattern in lower_line for pattern in en_thinking_patterns):
                found_english = True
                response_lines.append(line)
                continue
            
            # Detecta se é linha de pensamento em português
            is_thinking_line = (
                any(pattern in lower_line for pattern in pt_thinking_patterns) and
                len(lower_line) > 5  # Deve ter conteúdo
            )
            
            if is_thinking_line and i < 5:  # Apenas primeiras 5 linhas
                thinking_lines.append(line)
                lines_found += 1
            else:
                response_lines.append(line)
        
        thinking_text = '\n'.join(thinking_lines).strip()
        response_text = '\n'.join(response_lines).strip()
        
        # Se detectou inglês ou thinking muito curto, ignora
        if found_english or len(thinking_text) < 30:
            return "", text.strip()
        
        # Limita thinking a 250 caracteres max
        if len(thinking_text) > 250:
            thinking_text = thinking_text[:250]
        
        return thinking_text, response_text
    
    def _process_response_message(self, response: Any) -> None:
        """Processa cada mensagem do streaming da API."""
        try:
            if not hasattr(response, 'system_message'):
                return
            
            m = response.system_message
            
            # TEXT RESPONSE
            if hasattr(m, 'text') and m.text:
                text_response = m.text
                if hasattr(text_response, 'parts'):
                    # ✅ CORRIGE: Junta parts com quebra de linha para não concatenar perguntas
                    text = "\n".join(str(p) for p in text_response.parts)
                    
                    # 🔍 DEBUG: Se tiver múltiplas parts (pode ser perguntas), mostra
                    if len(text_response.parts) > 1:
                        print(f"\n   📝 Multiple parts detectadas ({len(text_response.parts)}):")
                        for idx, part in enumerate(text_response.parts):
                            part_str = str(part).strip()
                            print(f"      Part {idx}: {part_str[:80]}...")
                    
                    self.response_data["text"] += text + "\n"
            
            # DATA RESPONSE
            if hasattr(m, 'data') and m.data:
                data_response = m.data
                
                # SQL gerada
                if hasattr(data_response, 'generated_sql') and data_response.generated_sql:
                    self.response_data["generated_sql"] = str(data_response.generated_sql)
                
                # Result com dados
                if hasattr(data_response, 'result') and data_response.result:
                    result = data_response.result
                    
                    # Schema
                    if hasattr(result, 'schema') and hasattr(result.schema, 'fields'):
                        fields = [str(f.name) for f in result.schema.fields]
                    else:
                        fields = []
                    
                    # Data rows
                    if hasattr(result, 'data') and fields:
                        # Converte para lista
                        if hasattr(result.data, '__iter__') and not isinstance(result.data, (str, dict)):
                            data_list = list(result.data)
                        else:
                            data_list = [result.data] if result.data else []
                        
                        if len(data_list) > 0:
                            # Extrai campos
                            rows = []
                            for el in data_list:
                                row = {}
                                for field in fields:
                                    try:
                                        # MapComposite - tenta acessar como dicionário primeiro
                                        if field in el:
                                            row[field] = el[field]
                                        elif hasattr(el, field):
                                            row[field] = getattr(el, field)
                                        else:
                                            row[field] = None
                                    except:
                                        row[field] = None
                                rows.append(row)
                            
                            if rows:
                                self.response_data["rows"] = rows
                                self.response_data["data"] = rows
        
        except Exception as e:
            print(f"❌ Erro processando mensagem: {e}")

    def process_streaming(self, question: str):
        """
        Processa pergunta em modo STREAMING, gerando dados parciais.
        Yield de (tipo, dados) para renderização incremental na UI:
        - ('thinking_chunk', texto_pensamento_do_agente)
        - ('response_chunk', resposta_final_do_agente)
        - ('table_ready', dados_tabela_completa)
        - ('chart_ready', figura_gráfico)
        - ('complete', tech_details_final)
        
        ⭐ USA CAMPOS NATIVOS DA API:
        - text_type: 2 = THOUGHT (pensamento)
        - text_type: 1 = ANALYSIS (análise/resposta)
        - text_type: 0 = CONCLUSION (conclusão)
        """
        try:
            print(f"\n{'='*70}")
            print(f"📝 INICIANDO PROCESSO CA (STREAMING)")
            print(f"   Pergunta: {question}")
            print(f"{'='*70}")
            
            # Reset response data
            self.response_data = {
                "text": "",
                "schema": None,
                "query": None,
                "generated_sql": "",
                "data": None,
                "chart": None,
                "rows": []
            }
            
            # Setup conversa
            conversation_path = self._setup_conversation()
            agent_path = self._get_or_create_agent()
            
            # Monta request de chat
            messages = [
                geminidataanalytics.Message(
                    user_message=geminidataanalytics.UserMessage(text=question)
                )
            ]
            
            conversation_reference = geminidataanalytics.ConversationReference(
                conversation=conversation_path,
                data_agent_context=geminidataanalytics.DataAgentContext(
                    data_agent=agent_path,
                ),
            )
            
            request = geminidataanalytics.ChatRequest(
                parent=f"projects/{self.project_id}/locations/{self.LOCATION}",
                messages=messages,
                conversation_reference=conversation_reference,
            )
            
            print("🔄 Processando resposta em streaming...\n")
            
            # Chat streaming
            stream = self.data_chat_client.chat(request=request)
            
            last_text_length = 0
            rows_before = 0
            table_yielded = False
            chart_yielded = False
            
            # Rastreadores de tipo de texto (TEXT_TYPE enum values)
            TEXT_TYPE_THOUGHT = 2    # Pensamento do agente
            TEXT_TYPE_ANALYSIS = 1   # Análise/Resposta
            TEXT_TYPE_CONCLUSION = 0 # Conclusão
            
            # Acumula thinking e analysis separadamente
            accumulated_thinking = ""
            accumulated_analysis = ""
            last_text_type = None
            
            # ✅ RASTREAMENTO DO ÚLTIMO CHUNK (contém as perguntas)
            last_chunk_index = None
            last_chunk_text = ""
            
            # Lista para armazenar perguntas sugeridas (extraídas do texto final)
            example_queries = []
            
            for i, response in enumerate(stream):
                try:
                    # 🔍 DEBUG: Mostra cada objeto do streaming (especialmente os últimos)
                    print(f"\n{'='*80}")
                    print(f"📡 [CHUNK {i}] OBJETO COMPLETO DO STREAMING:")
                    print(f"{'='*80}")
                    print(repr(response))
                    print(f"{'='*80}\n")
                    
                    # Processa mensagem - atualiza self.response_data
                    self._process_response_message(response)
                    
                    # Extrai o tipo de texto se disponível
                    current_text_type = None
                    if hasattr(response, 'system_message') and response.system_message.text:
                        if hasattr(response.system_message.text, 'text_type'):
                            current_text_type = response.system_message.text.text_type
                    
                    # ✅ YIELD DE TEXTO: Separado por tipo nativo
                    current_text = self.response_data.get("text", "")
                    if len(current_text) > last_text_length:
                        new_text = current_text[last_text_length:]
                        if new_text.strip():
                            # ✅ RASTREIA O ÚLTIMO CHUNK COM TEXTO (para extrair perguntas depois)
                            last_chunk_index = i
                            last_chunk_text = new_text  # Armazena só o novo texto deste chunk
                            
                            # ✅ EXTRAI PERGUNTAS DO NOVO TEXTO ANTES DE FAZER YIELD
                            # Evita que as perguntas sejam entregues ao usuário em tempo real
                            import re as regex_module
                            text_to_yield = new_text
                            question_pattern = r'([^.!?]*\?)'
                            found_questions = regex_module.findall(question_pattern, new_text)
                            
                            if found_questions:
                                # Remove as perguntas do texto que vai ser enviado
                                for q in found_questions:
                                    q_clean = q.strip()
                                    if len(q_clean) > 15:  # Pergunta válida
                                        if q_clean not in example_queries:  # Evita duplicatas
                                            example_queries.append(q_clean)
                                        text_to_yield = text_to_yield.replace(q_clean, "").strip()
                                
                                print(f"🎯 [CHUNK {i}] {len(found_questions)} perguntas detectadas e REMOVIDAS do envio ao usuário")
                            
                            # Separa por text_type nativo
                            if text_to_yield.strip():  # Só faz yield se ainda houver texto
                                if current_text_type == TEXT_TYPE_THOUGHT:
                                    accumulated_thinking += text_to_yield
                                    print(f"💬 [CHUNK {i}] Pensamento (+{len(text_to_yield)} chars)")
                                    # Yield thinking
                                    yield ('thinking_chunk', text_to_yield)
                                elif current_text_type == TEXT_TYPE_ANALYSIS:
                                    accumulated_analysis += text_to_yield
                                    print(f"💬 [CHUNK {i}] Análise (+{len(text_to_yield)} chars)")
                                    # Yield analysis
                                    yield ('response_chunk', text_to_yield)
                                elif current_text_type == TEXT_TYPE_CONCLUSION:
                                    accumulated_analysis += text_to_yield
                                    print(f"💬 [CHUNK {i}] Conclusão (+{len(text_to_yield)} chars)")
                                    # Yield conclusion como parte da resposta
                                    yield ('response_chunk', text_to_yield)
                                else:
                                    # Fallback: trata como análise/resposta
                                    accumulated_analysis += text_to_yield
                                    print(f"💬 [CHUNK {i}] Novo texto (+{len(text_to_yield)} chars)")
                                    yield ('response_chunk', text_to_yield)
                        
                        last_text_length = len(current_text)
                    
                    # ✅ YIELD DE TABELA
                    rows = self.response_data.get("rows", [])
                    if rows and len(rows) > rows_before and not table_yielded:
                        print(f"📋 [CHUNK {i}] Tabela com {len(rows)} registros detectada")
                        yield ('table_ready', rows)
                        table_yielded = True
                        rows_before = len(rows)
                    
                except Exception as e:
                    print(f"❌ Erro no chunk {i+1}: {e}")
            
            print(f"\n✅ Streaming da API terminou (total de chunks: {i+1})")
            
            # ✅ YIELD FINAL: Tech details after all chunks processed
            rows = self.response_data.get("rows", [])
            
            # Gráfico final se houver dados
            chart_info = self._create_chart_info(rows)
            if chart_info and chart_info.get("fig") and not chart_yielded:
                print(f"📈 Gráfico criado")
                yield ('chart_ready', chart_info)
                chart_yielded = True
            
            # Monta resposta final completa
            full_text = self.response_data.get("text", "").strip()
            
            print(f"\n{'='*80}")
            print(f"🔍 TEXTO COMPLETO FINAL (antes de processar):")
            print(f"{'='*80}")
            print(f"{full_text}")
            print(f"{'='*80}\n")
            
            # ✅ EXTRAI PERGUNTAS DO ÚLTIMO CHUNK
            # O último chunk sempre contém as perguntas sugeridas
            # Procura por linhas que terminam com "?"
            if last_chunk_text:
                print(f"\n🔍 Analisando último chunk (CHUNK {last_chunk_index}) para extrair perguntas:")
                print(f"Texto: {last_chunk_text[:200]}...")
                
                import re as regex_module
                
                # Procura por linhas que terminam com "?" (perguntas sugeridas)
                # Pattern: qualquer coisa terminada com "?"
                question_pattern = r'([^.!?]*\?)'
                found_questions = regex_module.findall(question_pattern, last_chunk_text)
                
                if found_questions:
                    # Limpa e valida as perguntas
                    for q in found_questions:
                        q_clean = q.strip()
                        if len(q_clean) > 15:  # Pergunta válida
                            example_queries.append(q_clean)
                    
                    if example_queries:
                        print(f"\n✅ {len(example_queries)} PERGUNTAS SUGERIDAS ENCONTRADAS NO ÚLTIMO CHUNK:")
                        for q in example_queries:
                            print(f"   - {q}")
                        
                        # ✅ REMOVE as perguntas do texto final (resposta)
                        for q in example_queries:
                            full_text = full_text.replace(q, "").strip()
                        
                        # Remove espaços múltiplos
                        full_text = regex_module.sub(r'\s+', ' ', full_text)
                else:
                    print(f"⚠️ Nenhuma pergunta encontrada no último chunk")
            
            # ✅ Remove "example queries" / "suggested questions" do texto se forem mencionadas
            cleanup_patterns = [
                r"(?:here are some example|suggested)[^:]*:\s*", 
                r"(?:exemplo de|sugestões de) perguntas:?\s*",
                r"you might also want to ask:?\s*"
            ]
            for pattern in cleanup_patterns:
                # Encontra padrão e remove tudo depois dele se parecer ser uma lista
                match = regex_module.search(pattern, full_text, regex_module.IGNORECASE)
                if match:
                    full_text = full_text[:match.start()].strip()
            
            thinking, final_response = self._parse_thinking_and_response(full_text)
            
            summary = final_response if final_response else full_text
            if not summary:
                summary = "Análise concluída. Verifique a tabela de dados para os resultados."
            
            tech_details = {
                "agent_id": self.AGENT_ID,
                "project": self.project_id,
                "dataset": self.dataset_id,
                "conversation_id": self.conversation_id,
                "question": question,
                "response_type": "conversational_analytics",
                "conversational_analytics": True,
                "sql_query": self.response_data.get("generated_sql", ""),
                "aggrid_data": rows,
                "chart_info": chart_info,
                "example_queries": example_queries,  # ⭐ Exemplo de perguntas da API
                "data_extraction_status": {
                    "rows_extracted": len(rows),
                    "has_sql": bool(self.response_data.get("generated_sql")),
                    "response_parts": i + 1,
                }
            }
            
            print(f"{'='*70}")
            print(f"✅ STREAMING COMPLETO")
            print(f"   Registros: {len(rows)}")
            print(f"   Gráfico: {chart_info is not None}")
            print(f"   Chunks processados: {i+1}")
            print(f"{'='*70}\n")
            
            # YIELD FINAL: Completa processamento
            yield ('complete', (summary, tech_details))
        
        except Exception as e:
            import traceback
            error_msg = f"Erro Conversational Analytics: {str(e)}"
            print(f"\n❌ {error_msg}")
            traceback.print_exc()
            
            yield ('error', (error_msg, {
                "error": True,
                "error_message": error_msg,
                "response_type": "error",
                "conversational_analytics": True,
            }))
    
    def _create_chart_info(self, data: List[Dict]) -> Dict:
        """Cria informações de gráfico a partir dos dados."""
        if not data or len(data) == 0:
            return None
        
        try:
            fig = self._create_chart_figure(data)
            return {
                "has_chart": fig is not None,
                "data": data,
                "type": "bar",
                "fig": fig
            } if fig else None
        except Exception as e:
            print(f"⚠️ Erro criando chart_info: {e}")
            return None
    
    def _create_chart_figure(self, data: List[Dict]) -> Any:
        """Cria gráfico Altair a partir dos dados."""
        try:
            if not data:
                return None
            
            df = pd.DataFrame(data)
            
            # Detecta colunas
            numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
            string_cols = df.select_dtypes(include=['object']).columns.tolist()
            
            if not numeric_cols or not string_cols:
                return None
            
            # Seleciona colunas
            y_col = next(
                (c for c in numeric_cols if any(kw in c.lower() for kw in ['score', 'total', 'count', 'valor'])),
                numeric_cols[0]
            )
            x_col = string_cols[0]
            
            # Cria gráfico
            chart = alt.Chart(df).mark_bar().encode(
                x=alt.X(f"{x_col}:N", title=x_col),
                y=alt.Y(f"{y_col}:Q", title=y_col),
                color=alt.Color(f"{y_col}:Q", scale=alt.Scale(scheme='blues'))
            ).properties(
                width=600,
                height=400,
                title=f"Distribuição de {y_col}"
            )
            
            return chart
        
        except Exception as e:
            print(f"⚠️ Erro ao criar gráfico: {e}")
            return None


def main():
    """Testa o handler com uma pergunta simples."""
    print("\n" + "="*60)
    print("🚀 TESTE CONVERSATIONAL ANALYTICS HANDLER")
    print("="*60)
    
    # Inicializa handler
    handler = ConversationalAnalyticsHandler(
        project_id="superacessovip",
        dataset_id="DW_SuperAcesso"
    )
    
    # Pergunta de teste simples
    pergunta_teste = "Quais os assuntos mais negativos referente a empresa de id 1272 no ano de 2025?"
    
    print(f"\n❓ Pergunta teste: {pergunta_teste}")
    print("\n🔄 Processando...")
    
    # Chama handler
    summary, tech_details = handler.process(pergunta_teste)
    
    # Exibe resultados
    print("\n" + "="*60)
    print("📝 RESPOSTA:")
    print("="*60)
    print(summary)
    
    # Exibe dados técnicos se disponíveis
    if not tech_details.get("error"):
        print("\n" + "="*60)
        print("📊 DADOS TÉCNICOS:")
        print("="*60)
        print(f"Agent ID: {tech_details.get('agent_id')}")
        print(f"Project: {tech_details.get('project')}")
        print(f"Dataset: {tech_details.get('dataset')}")
        print(f"Conversation: {tech_details.get('conversation_id')}")
        print(f"Response Type: {tech_details.get('response_type')}")
        
        if tech_details.get('sql_query'):
            print(f"\n📋 SQL Query:")
            print(tech_details.get('sql_query'))
        
        if tech_details.get('aggrid_data'):
            print(f"\n📊 Registros retornados: {len(tech_details['aggrid_data'])}")
            print("\nPrimeiros registros:")
            for i, row in enumerate(tech_details['aggrid_data'][:3], 1):
                print(f"  {i}. {row}")
        
        if tech_details.get('chart_info') and tech_details['chart_info'].get('has_chart'):
            print("\n📈 Gráfico: Disponível")
    else:
        print(f"\n❌ Erro: {tech_details.get('error_message')}")
    
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    main()


