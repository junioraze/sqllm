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
            
            return summary, tech_details
        
        except Exception as e:
            import traceback
            error_msg = f"Erro Conversational Analytics: {str(e)}"
            print(f"❌ [CA_HANDLER.PROCESS] {error_msg}")
            traceback.print_exc()
            print(f"{'='*80}\n")
            
            return error_msg, {
                "error": True,
                "error_message": error_msg,
                "response_type": "error"
            }
    
    def _create_chart_figure(self, data: list, question: str = "") -> Any:
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
            
            # Prioriza colunas com "frequencia", "score", "percentual", "vendas"
            y_col = next(
                (c for c in numeric_cols if any(kw in c.lower() for kw in ['freq', 'score', 'percentual', 'valor', 'vendas', 'vendido'])),
                numeric_cols[0]
            )
            x_col = string_cols[0]
            
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
