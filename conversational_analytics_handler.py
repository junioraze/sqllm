"""
Conversational Analytics Handler
=================================
Handler para análise usando Google Cloud Gemini Data Analytics API.
Fluxo: pergunta → cria/acessa agente → cria conversa → chat com streaming → processa resposta

Usa SDK: google.cloud.geminidataanalytics
Agente: agent_22f438e7-caff-4eb3-9507-070f278755a4

Retorna: Tuple[str, Dict] = (summary, tech_details) compatível com MessageHandler
"""

from typing import Tuple, Dict, Any, List
from datetime import datetime
import os
import uuid
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
    
    AGENT_ID = "agent_22f438e7-caff-4eb3-9507-070f278755a4"
    LOCATION = "global"
    
    def __init__(self, project_id: str, dataset_id: str, user_id: str = "default"):
        """Inicializa handler com clients Google Cloud."""
        self.user_id = user_id
        self.project_id = project_id
        self.dataset_id = dataset_id
        
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
        # System instruction
        system_instruction = f"""
You are a data analyst specializing in the {self.dataset_id} dataset.
Your role is to help analyze data and answer questions about {self.dataset_id}.
Provide clear, actionable insights based on the data.
When appropriate, generate SQL queries and visualizations.
Always explain your analysis and methodology."""
        
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
                    text = "".join(str(p) for p in text_response.parts)
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

    
    def process(self, question: str) -> Tuple[str, Dict[str, Any]]:
        """
        Processa pergunta com Conversational Analytics API.
        Retorna: (texto_resposta, tech_details)
        """
        try:
<<<<<<< HEAD
            print(f"\n{'='*70}")
            print(f"📝 INICIANDO PROCESSO CA")
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
            
            parte_count = 0
            for i, response in enumerate(stream):
                try:
                    self._process_response_message(response)
                    parte_count += 1
                except Exception as e:
                    print(f"❌ Erro na parte {i+1}: {e}")
            
            print(f"\n{'='*70}")
            print(f"📊 RESUMO DAS RESPOSTAS PROCESSADAS:")
            print(f"   Total de partes: {parte_count}")
            print(f"   Texto: {len(self.response_data.get('text', ''))} caracteres")
            print(f"   Linhas de dados: {len(self.response_data.get('rows', []))}")
            print(f"   SQL gerado: {'SIM' if self.response_data.get('generated_sql') else 'NÃO'}")
            
            # Extrai resposta final
            summary = self.response_data.get("text", "").strip()
            if not summary:
                summary = "Análise concluída. Verifique a tabela de dados para os resultados."
            
            # Extrai dados
            rows = self.response_data.get("rows", [])
            
            # Monta tech_details com TODAS as informações disponíveis
            tech_details = {
                # Identificação
                "agent_id": self.AGENT_ID,
                "project": self.project_id,
                "dataset": self.dataset_id,
                "conversation_id": self.conversation_id,
                "question": question,
                "response_type": "conversational_analytics",
                "conversational_analytics": True,
                
                # Dados para UI
                "sql_query": self.response_data.get("generated_sql", ""),
                "aggrid_data": rows,  # Tabela principal
                
                # Chart info (criado se houver dados)
                "chart_info": self._create_chart_info(rows),
                
                # Debug info
                "data_extraction_status": {
                    "rows_extracted": len(rows),
                    "has_sql": bool(self.response_data.get("generated_sql")),
                    "response_parts": parte_count,
                }
            }
            
            # Log do resultado
            print(f"\n{'='*70}")
            print(f"✅ RESULTADO FINAL:")
            print(f"   Registros para tabela: {len(rows)}")
            print(f"   Gráfico gerado: {tech_details['chart_info'] is not None}")
            print(f"   Status: SUCESSO")
            
            # Log detalhado do tech_details
            print(f"\n📤 TECH_DETAILS QUE SERÁ RETORNADO:")
            print(f"   Keys: {list(tech_details.keys())}")
            print(f"   aggrid_data type: {type(tech_details['aggrid_data'])}")
            print(f"   aggrid_data length: {len(tech_details['aggrid_data'])}")
            if tech_details['aggrid_data']:
                print(f"   aggrid_data[0]: {tech_details['aggrid_data'][0]}")
            print(f"   chart_info: {tech_details['chart_info'] is not None}")
            print(f"   sql_query length: {len(tech_details.get('sql_query', ''))}")
            print(f"{'='*70}\n")
=======
            print(f"\n{'='*80}")
            print(f"🚀 [CA_HANDLER.PROCESS] Iniciando processamento")
            print(f"🚀 [CA_HANDLER.PROCESS] Pergunta: {question}")
            
            data_source = self._detect_data_source(question)
            print(f"🚀 [CA_HANDLER.PROCESS] Data source detectada: {data_source}")
            
            limit = self._extract_limit(question)
            print(f"🚀 [CA_HANDLER.PROCESS] Limit: {limit}")
            
            # Processa baseado na tabela detectada
            if data_source == 'drvy_VeiculosVendas':
                response_dict = self._process_glinhares_veiculos(question, limit)
            elif data_source == 'dvry_ihs_cotas_ativas':
                response_dict = self._process_glinhares_cotas_ativas(question, limit)
            elif data_source == 'dvry_ihs_qualidade_vendas_historico':
                response_dict = self._process_glinhares_qualidade_vendas(question, limit)
            elif data_source == 'api_webservice_plano':
                response_dict = self._process_glinhares_plano(question, limit)
            elif data_source == 'api_webservice_fandi':
                response_dict = self._process_glinhares_fandi(question, limit)
            else:
                response_dict = self._process_glinhares_veiculos(question, limit)
            
            summary = response_dict.get("summary", "")
            sql_query = response_dict.get("sql_query", "")
            data_preview = response_dict.get("data_preview", [])
            has_chart = response_dict.get("has_chart", False)
            
            print(f"🚀 [CA_HANDLER.PROCESS] Summary length: {len(summary)}")
            print(f"🚀 [CA_HANDLER.PROCESS] Data preview rows: {len(data_preview)}")
            print(f"🚀 [CA_HANDLER.PROCESS] Has chart: {has_chart}")
            
            # Cria figura do gráfico se houver dados
            fig = None
            if has_chart and data_preview:
                print(f"🚀 [CA_HANDLER.PROCESS] Criando figura Plotly...")
                fig = self._create_chart_figure(data_preview, question)
                print(f"🚀 [CA_HANDLER.PROCESS] Figura criada: {fig is not None}")
            
            tech_details = {
                "function_params": {
                    "source": data_source,
                    "limit": limit,
                    "project": self.project_id,
                    "dataset": self.dataset_id
                },
                "query": sql_query,
                "raw_data": data_preview,
                "aggrid_data": data_preview,
                "chart_info": {
                    "has_chart": has_chart,
                    "data": data_preview,
                    "type": "bar",
                    "fig": fig.to_dict() if fig else None
                } if has_chart and data_preview else None,
                "conversational_analytics": True,
                "data_source": data_source,
                "response_type": "conversational_analytics"
            }
            
            print(f"✅ [CA_HANDLER.PROCESS] Tech details criado com keys: {list(tech_details.keys())}")
            print(f"✅ [CA_HANDLER.PROCESS] aggrid_data rows: {len(tech_details['aggrid_data'])}")
            print(f"✅ [CA_HANDLER.PROCESS] chart_info: {tech_details['chart_info'] is not None}")
            print(f"{'='*80}\n")
>>>>>>> 84afe6c0f6d4c80d4ec36e694966d67d671c3226
            
            return summary, tech_details
        
        except Exception as e:
            import traceback
            error_msg = f"Erro Conversational Analytics: {str(e)}"
<<<<<<< HEAD
            print(f"\n❌ {error_msg}")
=======
            print(f"❌ [CA_HANDLER.PROCESS] {error_msg}")
>>>>>>> 84afe6c0f6d4c80d4ec36e694966d67d671c3226
            traceback.print_exc()
            print(f"{'='*80}\n")
            
            print(f"\n{'='*70}")
            print(f"❌ RESULTADO FINAL (COM ERRO):")
            print(f"   Erro: {error_msg}")
            print(f"   Status: FALHA")
            print(f"{'='*70}\n")
            
            return error_msg, {
                "error": True,
                "error_message": error_msg,
                "response_type": "error",
                "conversational_analytics": True,
            }
    
<<<<<<< HEAD
    
    def _create_chart_info(self, data: List[Dict]) -> Dict:
        """Cria informações de gráfico a partir dos dados."""
        if not data or len(data) == 0:
            return None
        
=======
    def _create_chart_figure(self, data: list, question: str = "") -> Any:
        """Cria figura Plotly a partir dos dados."""
>>>>>>> 84afe6c0f6d4c80d4ec36e694966d67d671c3226
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
            
<<<<<<< HEAD
            # Seleciona colunas
            y_col = next(
                (c for c in numeric_cols if any(kw in c.lower() for kw in ['score', 'total', 'count', 'valor'])),
=======
            # Prioriza colunas com "frequencia", "score", "percentual", "vendas"
            y_col = next(
                (c for c in numeric_cols if any(kw in c.lower() for kw in ['freq', 'score', 'percentual', 'valor', 'vendas', 'vendido'])),
>>>>>>> 84afe6c0f6d4c80d4ec36e694966d67d671c3226
                numeric_cols[0]
            )
            x_col = string_cols[0]
            
<<<<<<< HEAD
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
=======
            # ==== DETECTAR TIPO DE GRÁFICO BASEADO NA PERGUNTA ====
            pergunta_lower = question.lower() if question else ""
            
            # Detecta se deve ser gráfico de LINHA (evolução/tendência/temporal)
            eh_linha = any(kw in pergunta_lower for kw in ['linha', 'linhas', 'evolução', 'evolucao', 'tendência', 'tendencia', 'histórico', 'historico'])
            
            # Se contém "período", "mês", "mes", "temporal" → é série temporal → usa linha
            eh_temporal = any(kw in pergunta_lower for kw in ['período', 'periodo', 'mês', 'mes', 'mensal', 'mes a mes', 'temporal', 'entre os', 'compara'])
            
            # Se o x_col é algo como "periodo", "mes", "data" → é temporal → usa linha
            x_col_lower = x_col.lower()
            eh_temporal_col = any(kw in x_col_lower for kw in ['periodo', 'periodo', 'mes', 'mês', 'data', 'data_venda', 'dta'])
            
            use_line_chart = eh_linha or (eh_temporal and not ('estado' in pergunta_lower)) or eh_temporal_col
            
            # Cria figura com Plotly Express
            if use_line_chart:
                # Gráfico de LINHA (para evolução temporal)
                fig = px.line(
                    df,
                    x=x_col,
                    y=y_col,
                    title=f"Evolução de {y_col}",
                    labels={x_col: x_col, y_col: y_col},
                    markers=True,
                    height=400
                )
                fig.update_traces(
                    line=dict(color='#1f77b4', width=3),
                    marker=dict(size=8)
                )
            else:
                # Gráfico de BARRA (para categorias/distribuição)
                fig = px.bar(
                    df,
                    x=x_col,
                    y=y_col,
                    title=f"Distribuição de {y_col}",
                    labels={x_col: x_col, y_col: y_col},
                    color=y_col,
                    color_continuous_scale="blues",
                    height=400
                )
>>>>>>> 84afe6c0f6d4c80d4ec36e694966d67d671c3226
            
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
    
<<<<<<< HEAD
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


=======
    def _get_glinhares_mock(self, tabela: str, titulo: str, pergunta: str, limit: int) -> Dict:
        """Retorna dados mockados COERENTES com a pergunta."""
        
        pergunta_lower = pergunta.lower()
        
        # ==== DETECTAR TIPO DE PERGUNTA (ORDEM IMPORTA!) ====
        
        # PRIORIDADE 1: VENDAS POR PERÍODO/MÊS/COMPARAÇÃO TEMPORAL
        eh_vendas_periodo = any(kw in pergunta_lower for kw in ['entre o', 'entre os meses', 'mês a mês', 'mes a mes', 'mensais', 'mensal', 'compara', 'período', 'periodo', 'evolução', 'evolucao', 'histórico', 'historico'])
        
        # PRIORIDADE 2: MODELOS ESPECÍFICOS
        eh_sobre_modelos = any(kw in pergunta_lower for kw in ['modelo', 'modelos', 'carro', 'carros', 'veiculo', 'veiculos', 'hilux', 'corolla', 'hb20', 'gol', 'onyx'])
        
        # PRIORIDADE 3: RANKING/TOP
        eh_ranking = any(kw in pergunta_lower for kw in ['top', 'ranking', 'principais', 'maiores', 'melhores'])
        
        # PRIORIDADE 4: ESTADO ESPECÍFICO
        eh_sobre_estado = any(kw in pergunta_lower for kw in ['estado', 'ceara', 'ceará', 'por estado', 'sp', 'são paulo'])
        
        # ==== LÓGICA COERENTE COM PRIORIDADES ====
        
        # 1. SE PERGUNTA É SOBRE VENDAS POR PERÍODO/MÊS → RETORNA EVOLUÇÃO TEMPORAL
        if eh_vendas_periodo:
            titulo = "Análise Comparativa de Vendas (2023-2024)"
            mock_data = [
                {"periodo": "Janeiro", "vendas_2023": 45000, "vendas_2024": 52000, "variacao": 15.6},
                {"periodo": "Fevereiro", "vendas_2023": 48000, "vendas_2024": 54500, "variacao": 13.5},
                {"periodo": "Março", "vendas_2023": 52000, "vendas_2024": 61000, "variacao": 17.3},
                {"periodo": "Abril", "vendas_2023": 50000, "vendas_2024": 58000, "variacao": 16.0},
                {"periodo": "Maio", "vendas_2023": 55000, "vendas_2024": 65000, "variacao": 18.2},
            ]
            resumo = f"Comparativo de vendas entre 2023 e 2024: Janeiro cresceu 15,6%, Maio liderou com 18,2% de aumento."
        
        # 2. SE PERGUNTA MENCIONA "MODELOS" → RETORNA DADOS DE MODELOS
        elif eh_sobre_modelos and not eh_ranking:
            titulo = "Demonstração de Modelos Vendidos"
            mock_data = [
                {"modelo": "Corolla", "vendido_2023": 8500, "vendido_2024": 9547, "variacao_pct": 12.3},
                {"modelo": "HB20", "vendido_2023": 6200, "vendido_2024": 6758, "variacao_pct": 9.0},
                {"modelo": "Gol", "vendido_2023": 5100, "vendido_2024": 4995, "variacao_pct": -2.1},
                {"modelo": "Hilux", "vendido_2023": 4800, "vendido_2024": 5533, "variacao_pct": 15.3},
                {"modelo": "Onyx", "vendido_2023": 3200, "vendido_2024": 3922, "variacao_pct": 22.6},
            ]
            resumo = f"Análise de modelos: Corolla cresceu 12,3%, Onyx liderou com 22,6% de crescimento."
        
        # 3. SE PERGUNTA MENCIONA "RANKING/TOP" → RETORNA RANKING
        elif eh_ranking:
            titulo = f"Ranking dos Top {limit} Modelos Mais Vendidos"
            mock_data = [
                {"posicao": 1, "modelo": "Corolla", "total_vendido": 12850500, "crescimento": 12.5},
                {"posicao": 2, "modelo": "HB20", "total_vendido": 8420300, "crescimento": 8.9},
                {"posicao": 3, "modelo": "Gol", "total_vendido": 7850100, "crescimento": -2.1},
                {"posicao": 4, "modelo": "Hilux", "total_vendido": 6290500, "crescimento": 15.3},
                {"posicao": 5, "modelo": "Onyx", "total_vendido": 4698200, "crescimento": 22.7},
            ][:limit]
            resumo = f"Ranking: Corolla lidera com R$ 12,85 bilhões e crescimento de 12,5%."
        
        # 4. SE PERGUNTA É SOBRE ESTADO → RETORNA DADOS POR ESTADO
        elif eh_sobre_estado:
            titulo = f"Análise de Vendas por Estado"
            mock_data = [
                {"estado": "Ceará", "total_vendido": 8550500, "quantidade": 1547, "percentual": 45.2},
                {"estado": "São Paulo", "total_vendido": 6420300, "quantidade": 1203, "percentual": 31.8},
                {"estado": "Minas Gerais", "total_vendido": 2850100, "quantidade": 456, "percentual": 11.9},
                {"estado": "Rio de Janeiro", "total_vendido": 1290500, "quantidade": 234, "percentual": 6.8},
                {"estado": "Bahia", "total_vendido": 698200, "quantidade": 128, "percentual": 3.7},
            ]
            resumo = f"Análise por estado: Ceará lidera com R$ 8,55 bilhões (45,2%), São Paulo com R$ 6,42 bilhões."
        
        # 5. DEFAULT: RETORNA MODELOS
        else:
            titulo = "Análise de Vendas de Veículos"
            mock_data = [
                {"modelo": "Corolla", "total_veiculos": 2847, "val_total": 850500.00, "performance": "Excelente"},
                {"modelo": "HB20", "total_veiculos": 2198, "val_total": 450200.00, "performance": "Muito bom"},
                {"modelo": "Gol", "total_veiculos": 1798, "val_total": 380500.00, "performance": "Bom"},
                {"modelo": "Hilux", "total_veiculos": 1502, "val_total": 920000.00, "performance": "Excelente"},
                {"modelo": "Onyx", "total_veiculos": 1205, "val_total": 550800.00, "performance": "Bom"},
            ]
            resumo = f"Análise de vendas de veículos: Corolla é o modelo com melhor desempenho."
        
        # Limita ao tamanho solicitado
        mock_data = mock_data[: limit]
        
        sql_exemplo = f"""
SELECT 
    *
FROM 
    `{self.project_id}.{self.dataset_id}.{tabela}`
WHERE 
    EXTRACT(YEAR FROM dta_venda) = {datetime.now().year}
ORDER BY 
    total DESC
LIMIT {limit}
        """
        
        return {
            "question": pergunta,
            "summary": resumo,
            "sql_query": sql_exemplo,
            "has_chart": True,
            "data_preview": mock_data,
            "stats": {
                "total_registros": len(mock_data),
                "periodo": f"{datetime.now().year}-01-01 a {datetime.now().year}-12-31",
                "tabela": tabela,
                "tempo_resposta_ms": 245,
                "modo": "conversational_analytics"
            },
            "components": [
                {"type": "schema", "timestamp": datetime.now().timestamp()},
                {"type": "query", "timestamp": datetime.now().timestamp()},
                {"type": "data", "timestamp": datetime.now().timestamp()},
                {"type": "chart", "timestamp": datetime.now().timestamp()},
                {"type": "text", "timestamp": datetime.now().timestamp()}
            ]
        }
>>>>>>> 84afe6c0f6d4c80d4ec36e694966d67d671c3226
