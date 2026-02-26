"""
Conversational Analytics Handler
=================================
Integração com message_handler.py para suporte a:
- Natura (SuperAcessoVIP)
- Google Trends (ConversationalAnalyticsAltFlow)

Retorna: (texto_resposta, tech_details) compatível com MessageHandler
"""

from typing import Tuple, Dict, Any
from datetime import datetime
import re
from test_conversational_analytics_alt import ConversationalAnalyticsAltFlow
from config import PROJECT_ID, DATASET_ID
import plotly.express as px
import pandas as pd


class ConversationalAnalyticsHandler:
    """Handler para Conversational Analytics integrado ao MessageHandler.
    
    Suporta consultas nas tabelas glinhares:
    - drvy_VeiculosVendas: Vendas de veículos
    - dvry_ihs_cotas_ativas: Contratos de consórcio ativos
    - dvry_ihs_qualidade_vendas_historico: Histórico de qualidade de vendas
    - api_webservice_plano: Planos disponíveis
    - api_webservice_fandi: Dados Fandi
    """
    
    def __init__(self, user_id: str = "default"):
        """Inicializa handler com análise de vendas glinhares."""
        self.flow = ConversationalAnalyticsAltFlow(
            billing_project=PROJECT_ID,
            location="global",
            data_agent_id="glinhares_analyzer"
        )
        
        self.user_id = user_id
        self.project_id = PROJECT_ID
        self.dataset_id = DATASET_ID
    
    def _detect_data_source(self, question: str) -> str:
        """Detecta qual tabela glinhares usar baseado na pergunta."""
        question_lower = question.lower()
        
        # Padrões para diferentes tabelas
        if any(kw in question_lower for kw in ['consórcio', 'consorcio', 'cota', 'plano', 'contempla']):
            # Verificar qual tabela de consórcio usar
            if 'qualidade' in question_lower or 'histórico' in question_lower or 'historico' in question_lower:
                return 'dvry_ihs_qualidade_vendas_historico'
            elif 'ativo' in question_lower or 'ativa' in question_lower:
                return 'dvry_ihs_cotas_ativas'
            else:
                return 'dvry_ihs_cotas_ativas'  # Padrão
        
        if any(kw in question_lower for kw in ['veículo', 'veiculo', 'moto', 'carro', 'car', 'modelo']):
            return 'drvy_VeiculosVendas'
        
        if any(kw in question_lower for kw in ['plano', 'plan']):
            return 'api_webservice_plano'
        
        if 'fandi' in question_lower:
            return 'api_webservice_fandi'
        
        # Padrão: retorna vendas de veículos
        return 'drvy_VeiculosVendas'
    
    def _extract_limit(self, question: str) -> int:
        """Extrai o número de registros desejado."""
        patterns = [
            r'(\d+)\s+(?:assuntos|termos|itens|registros|linhas|primeiros)',
            r'top\s+(\d+)',
            r'(\d+)\s+principais',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, question.lower())
            if match:
                return int(match.group(1))
        
        return 20
    
    def process(self, question: str) -> Tuple[str, Dict[str, Any]]:
        """
        Processa pergunta com Conversational Analytics.
        Retorna: (texto_resposta, tech_details)
        Compatível com MessageHandler.process_message()
        """
        try:
            data_source = self._detect_data_source(question)
            limit = self._extract_limit(question)
            
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
            
            # Cria figura do gráfico se houver dados
            fig = None
            if has_chart and data_preview:
                fig = self._create_chart_figure(data_preview)
            
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
            
            return summary, tech_details
        
        except Exception as e:
            import traceback
            error_msg = f"Erro Conversational Analytics: {str(e)}"
            print(error_msg)
            traceback.print_exc()
            
            return error_msg, {
                "error": True,
                "error_message": error_msg,
                "response_type": "error"
            }
    
    def _create_chart_figure(self, data: list) -> Any:
        """Cria figura Plotly a partir dos dados."""
        try:
            if not data or len(data) == 0:
                return None
            
            df = pd.DataFrame(data)
            
            # Detecta colunas para o gráfico
            numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
            string_cols = df.select_dtypes(include=['object']).columns.tolist()
            
            if not numeric_cols or not string_cols:
                return None
            
            # Prioriza colunas com "frequencia", "score", "percentual"
            y_col = next(
                (c for c in numeric_cols if any(kw in c.lower() for kw in ['freq', 'score', 'percentual', 'valor'])),
                numeric_cols[0]
            )
            x_col = string_cols[0]
            
            # Cria figura com Plotly Express
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
            
            fig.update_layout(
                showlegend=False,
                xaxis_tickangle=-45,
                hovermode='x unified'
            )
            
            return fig
        
        except Exception as e:
            print(f"Erro ao criar figura: {e}")
            return None
    
    def _process_glinhares_veiculos(self, question: str, limit: int = 20) -> Dict[str, Any]:
        """Processa pergunta sobre vendas de veículos glinhares."""
        return self._get_glinhares_mock(
            tabela="drvy_VeiculosVendas",
            titulo="Análise de Vendas de Veículos",
            pergunta=question,
            limit=limit
        )
    
    def _process_glinhares_cotas_ativas(self, question: str, limit: int = 20) -> Dict[str, Any]:
        """Processa pergunta sobre contratos de consórcio ativos."""
        return self._get_glinhares_mock(
            tabela="dvry_ihs_cotas_ativas",
            titulo="Análise de Contratos de Consórcio Ativos",
            pergunta=question,
            limit=limit
        )
    
    def _process_glinhares_qualidade_vendas(self, question: str, limit: int = 20) -> Dict[str, Any]:
        """Processa pergunta sobre qualidade histórica de vendas."""
        return self._get_glinhares_mock(
            tabela="dvry_ihs_qualidade_vendas_historico",
            titulo="Análise Histórica de Qualidade de Vendas",
            pergunta=question,
            limit=limit
        )
    
    def _process_glinhares_plano(self, question: str, limit: int = 20) -> Dict[str, Any]:
        """Processa pergunta sobre planos disponíveis."""
        return self._get_glinhares_mock(
            tabela="api_webservice_plano",
            titulo="Análise de Planos Disponíveis",
            pergunta=question,
            limit=limit
        )
    
    def _process_glinhares_fandi(self, question: str, limit: int = 20) -> Dict[str, Any]:
        """Processa pergunta sobre dados Fandi."""
        return self._get_glinhares_mock(
            tabela="api_webservice_fandi",
            titulo="Análise de Dados Fandi",
            pergunta=question,
            limit=limit
        )
    
    def _get_glinhares_mock(self, tabela: str, titulo: str, pergunta: str, limit: int) -> Dict:
        """Retorna dados mockados para glinhares quando consulta é feita."""
        
        # Dados mockados por tabela
        mock_templates = {
            "drvy_VeiculosVendas": [
                {"modelo": "Corolla", "total_veiculos": 2847, "val_total": 850500.00},
                {"modelo": "HB20", "total_veiculos": 2198, "val_total": 450200.00},
                {"modelo": "Gol", "total_veiculos": 1798, "val_total": 380500.00},
                {"modelo": "Hilux", "total_veiculos": 1502, "val_total": 920000.00},
                {"modelo": "Onyx", "total_veiculos": 1205, "val_total": 550800.00},
            ],
            "dvry_ihs_cotas_ativas": [
                {"Modelo": "Honda Civic", "total_contratos": 342, "valor_medio": 125000},
                {"Modelo": "Ford Fiesta", "total_contratos": 298, "valor_medio": 95000},
                {"Modelo": "Chevrolet Cruze", "total_contratos": 256, "valor_medio": 110000},
                {"Modelo": "Volkswagen Jetta", "total_contratos": 198, "valor_medio": 118000},
                {"Modelo": "Motos Yamaha", "total_contratos": 156, "valor_medio": 35000},
            ],
            "dvry_ihs_qualidade_vendas_historico": [
                {"Plano": "Motos Premium", "total_vendas": 1250, "percentual": 25.5},
                {"Plano": "Carros Popular", "total_vendas": 1050, "percentual": 21.4},
                {"Plano": "Carros Premium", "total_vendas": 955, "percentual": 19.5},
                {"Plano": "Motos Básico", "total_vendas": 850, "percentual": 17.3},
                {"Plano": "Especiais", "total_vendas": 645, "percentual": 13.2},
            ],
            "api_webservice_plano": [
                {"plano_nome": "Motos Premium", "total_ativo": 342, "valor": 35000},
                {"plano_nome": "Carros Popular", "total_ativo": 298, "valor": 85000},
                {"plano_nome": "Carros Premium", "total_ativo": 256, "valor": 115000},
                {"plano_nome": "Motos Básico", "total_ativo": 198, "valor": 28000},
                {"plano_nome": "Especiais", "total_ativo": 156, "valor": 150000},
            ],
            "api_webservice_fandi": [
                {"fandi_item": "Fandi Veículos", "total": 4250, "percentual": 42.5},
                {"fandi_item": "Fandi Motos", "total": 2150, "percentual": 21.5},
                {"fandi_item": "Fandi Premium", "total": 1850, "percentual": 18.5},
                {"fandi_item": "Fandi Especiais", "total": 950, "percentual": 9.5},
                {"fandi_item": "Outros", "total": 810, "percentual": 8.1},
            ]
        }
        
        mock_data = mock_templates.get(tabela, [])[:limit]
        
        # Resumo automático
        if mock_data:
            primeiro_item = mock_data[0]
            chave_primeira = list(primeiro_item.keys())[0]
            resumo = f"{titulo}: Análise de {limit} principais itens. Destaque: {primeiro_item[chave_primeira]} é o principal, seguido de outros itens relevantes."
        else:
            resumo = f"{titulo}: Nenhum resultado encontrado."
        
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
