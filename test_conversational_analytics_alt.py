"""
Fluxo alternativo da Conversational Analytics API.
Em vez de streaming (resposta contínua), este implementa:
- Processamento batch: coleta TODA resposta antes de processar
- Agregação customizada: formata dados em estrutura unificada
- Retry com fallback: tenta stateful, cai para stateless se falhar
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import json
from datetime import datetime


class ResponseType(Enum):
    """Tipos de componentes na resposta."""
    SCHEMA = "schema"
    QUERY = "query"
    DATA = "data"
    CHART = "chart"
    TEXT = "text"
    ERROR = "error"


@dataclass
class ResponseComponent:
    """Componente individual da resposta."""
    type: ResponseType
    content: Any
    timestamp: float


@dataclass
class AggregatedResponse:
    """Resposta agregada em formato unificado."""
    question: str
    components: List[ResponseComponent]
    summary: str
    has_chart: bool
    sql_query: Optional[str] = None
    data_preview: Optional[List[Dict]] = None
    
    def to_dict(self) -> Dict:
        return {
            "question": self.question,
            "summary": self.summary,
            "sql_query": self.sql_query,
            "has_chart": self.has_chart,
            "data_preview": self.data_preview,
            "components": [
                {
                    "type": c.type.value,
                    "timestamp": c.timestamp
                } for c in self.components
            ]
        }


class BatchResponseProcessor:
    """Processa resposta batch em vez de streaming."""
    
    def __init__(self):
        self.components: List[ResponseComponent] = []
        self.start_time = datetime.now().timestamp()
    
    def collect_response(self, stream):
        """
        Coleta TODA resposta do stream antes de processar.
        Em vez de processar incrementalmente, acumula tudo.
        """
        for response in stream:
            if hasattr(response, 'schema'):
                self.components.append(ResponseComponent(
                    type=ResponseType.SCHEMA,
                    content=str(response.schema),
                    timestamp=datetime.now().timestamp()
                ))
            
            if hasattr(response, 'generated_sql'):
                self.components.append(ResponseComponent(
                    type=ResponseType.QUERY,
                    content=response.generated_sql,
                    timestamp=datetime.now().timestamp()
                ))
            
            if hasattr(response, 'result') and response.result:
                self.components.append(ResponseComponent(
                    type=ResponseType.DATA,
                    content=self._convert_result(response.result),
                    timestamp=datetime.now().timestamp()
                ))
            
            if hasattr(response, 'chart_vega_json'):
                self.components.append(ResponseComponent(
                    type=ResponseType.CHART,
                    content=response.chart_vega_json,
                    timestamp=datetime.now().timestamp()
                ))
            
            if hasattr(response, 'text_response'):
                self.components.append(ResponseComponent(
                    type=ResponseType.TEXT,
                    content=response.text_response,
                    timestamp=datetime.now().timestamp()
                ))
        
        return self.components
    
    def aggregate(self, question: str) -> AggregatedResponse:
        """Agrega componentes em resposta unificada."""
        sql_query = next(
            (c.content for c in self.components if c.type == ResponseType.QUERY),
            None
        )
        text_summary = next(
            (c.content for c in self.components if c.type == ResponseType.TEXT),
            "Processamento concluído."
        )
        data = next(
            (c.content for c in self.components if c.type == ResponseType.DATA),
            None
        )
        has_chart = any(c.type == ResponseType.CHART for c in self.components)
        
        return AggregatedResponse(
            question=question,
            components=self.components,
            summary=text_summary,
            has_chart=has_chart,
            sql_query=sql_query,
            data_preview=data[:5] if data else None  # Primeiras 5 linhas
        )
    
    @staticmethod
    def _convert_result(result) -> List[Dict]:
        """Converte resultado em lista de dicts."""
        try:
            # Se for DataFrame do pandas
            return result.to_dict('records')
        except:
            # Se for lista
            if isinstance(result, list):
                return result
            # Fallback
            return [{"raw": str(result)}]


class StatelessFallbackHandler:
    """Fallback para modo stateless se stateful falhar."""
    
    def __init__(self, billing_project: str, location: str, data_agent_id: str):
        self.billing_project = billing_project
        self.location = location
        self.data_agent_id = data_agent_id
        self.message_history = []
    
    def send_stateless_request(self, question: str, conversation_context: Optional[str] = None):
        """
        Envia request stateless (sem conversa persistente).
        Gerencia contexto localmente no objeto.
        """
        # Simular armazenamento local de história
        self.message_history.append({
            "role": "user",
            "content": question,
            "timestamp": datetime.now().isoformat()
        })
        
        # Em uso real, seria:
        # request = geminidataanalytics.ChatRequest(
        #     parent=f"projects/{self.billing_project}/locations/{self.location}",
        #     messages=[...user_messages...],
        #     # SEM conversation_reference
        # )
        
        return {
            "type": "stateless",
            "question": question,
            "history_length": len(self.message_history),
            "message_ids": [f"msg_{i}" for i in range(len(self.message_history))]
        }
    
    def add_assistant_response(self, response: str):
        """Adiciona resposta ao histórico local."""
        self.message_history.append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now().isoformat()
        })


class ConversationalAnalyticsAltFlow:
    """Fluxo alternativo completo com retry e fallback."""
    
    def __init__(self, billing_project: str, location: str, data_agent_id: str):
        self.billing_project = billing_project
        self.location = location
        self.data_agent_id = data_agent_id
        self.stateless_handler = StatelessFallbackHandler(
            billing_project, location, data_agent_id
        )
    
    def execute_with_fallback(self, question: str, conversation_id: Optional[str] = None) -> AggregatedResponse:
        """
        Tenta stateful, cai para stateless.
        Retorna resposta agregada em ambos os casos.
        """
        try:
            # Tenta abordagem stateful batch
            return self._execute_stateful_batch(question, conversation_id)
        except Exception as e:
            print(f"[FALLBACK] Stateful falhou: {e}")
            # Cai para stateless
            return self._execute_stateless(question)
    
    def _execute_stateful_batch(self, question: str, conversation_id: str) -> AggregatedResponse:
        """
        Executa em modo stateful mas coleta TODA resposta antes de processar.
        
        Em uso real:
        - Cria conversation (se não existir)
        - Manda ChatRequest
        - Coleta stream inteiro com BatchResponseProcessor
        - Agrega resultado
        """
        processor = BatchResponseProcessor()
        
        # Simulação: em produção seria:
        # stream = data_chat_client.chat(request=chat_request)
        # processor.collect_response(stream)
        
        # Para demo, simular resposta
        sim_components = [
            ResponseComponent(
                type=ResponseType.SCHEMA,
                content="Tables: google_trends.top_terms, google_trends.top_rising_terms",
                timestamp=datetime.now().timestamp()
            ),
            ResponseComponent(
                type=ResponseType.QUERY,
                content="SELECT term, score FROM `bigquery-public-data.google_trends.top_terms` WHERE dma_name='New York NY' LIMIT 20",
                timestamp=datetime.now().timestamp()
            ),
            ResponseComponent(
                type=ResponseType.DATA,
                content=[{"term": f"search_term_{i}", "score": 100-i*5} for i in range(5)],
                timestamp=datetime.now().timestamp()
            ),
            ResponseComponent(
                type=ResponseType.CHART,
                content={"$schema": "https://vega.github.io/schema/vega-lite/v5.json", "mark": "bar"},
                timestamp=datetime.now().timestamp()
            ),
            ResponseComponent(
                type=ResponseType.TEXT,
                content="Os 20 termos mais populares em NYC na última semana mostram tendência crescente em tech.",
                timestamp=datetime.now().timestamp()
            ),
        ]
        processor.components = sim_components
        
        return processor.aggregate(question)
    
    def _execute_stateless(self, question: str) -> AggregatedResponse:
        """
        Executa em modo stateless com gerenciamento local de contexto.
        """
        # Simula request stateless
        result = self.stateless_handler.send_stateless_request(question)
        
        # Simula resposta e agrega
        response = AggregatedResponse(
            question=question,
            components=[
                ResponseComponent(
                    type=ResponseType.QUERY,
                    content="SELECT * FROM google_trends.top_terms",
                    timestamp=datetime.now().timestamp()
                )
            ],
            summary="Resposta em modo stateless. Contexto mantido localmente.",
            has_chart=False,
            sql_query="SELECT * FROM google_trends.top_terms"
        )
        
        self.stateless_handler.add_assistant_response(response.summary)
        return response


# ============ TESTE ============

def main():
    """Demo do fluxo alternativo."""
    
    print("=" * 70)
    print("TESTE FLUXO ALTERNATIVO - Conversational Analytics API")
    print("=" * 70)
    print()
    
    # Inicializa fluxo alternativo
    flow = ConversationalAnalyticsAltFlow(
        billing_project="seu-projeto",
        location="global",
        data_agent_id="demo_agent"
    )
    
    # Teste 1: Consulta simples
    print("[TESTE 1] Consulta estatual em modo batch")
    print("-" * 70)
    response1 = flow.execute_with_fallback(
        question="Quais são os 20 termos mais populares em NYC?",
        conversation_id="test_conv_1"
    )
    print(f"Q: {response1.question}")
    print(f"Componentes coletados: {len(response1.components)}")
    print(f"SQL: {response1.sql_query}")
    print(f"Tem chart: {response1.has_chart}")
    print(f"Resposta: {response1.summary}")
    print(f"Preview dos dados:\n  {response1.data_preview}")
    print()
    
    # Teste 2: Simula failure e fallback
    print("[TESTE 2] Fallback para modo stateless")
    print("-" * 70)
    response2 = flow.execute_with_fallback(
        question="Qual foi o crescimento semana anterior?"
    )
    print(f"Q: {response2.question}")
    print(f"SQL: {response2.sql_query}")
    print(f"Resposta: {response2.summary}")
    print()
    
    # Teste 3: Exportar como JSON
    print("[TESTE 3] Export estruturado JSON")
    print("-" * 70)
    json_output = json.dumps(response1.to_dict(), indent=2, default=str)
    print(json_output[:500] + "..." if len(json_output) > 500 else json_output)
    print()
    
    print("=" * 70)
    print("FIM DO TESTE")
    print("=" * 70)


if __name__ == "__main__":
    main()
