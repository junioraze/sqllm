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
            
            return summary, tech_details
        
        except Exception as e:
            import traceback
            error_msg = f"Erro Conversational Analytics: {str(e)}"
            print(f"\n❌ {error_msg}")
            traceback.print_exc()
            
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


