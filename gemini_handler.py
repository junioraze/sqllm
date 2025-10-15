"""
Gemini Handler Limpo com Sistema RAG Puro
========================================
"""

import google.generativeai as genai
from google.generativeai.types import Tool, FunctionDeclaration
from config import MODEL_NAME, TABLES_CONFIG, PROJECT_ID, DATASET_ID
from ai_metrics import TokenUsageMetric
import re
import json
import pandas as pd
import plotly.express as px
import streamlit as st
from utils import create_styled_download_button, generate_excel_bytes, generate_csv_bytes
from datetime import datetime
import time
import os
import streamlit as st
# Sistema RAG obrigatório
from business_metadata_rag import business_rag, get_optimized_business_context
from ai_metrics import ai_metrics
from prompt_rules import get_sql_functioncall_instruction, build_tables_fields_instruction, get_refine_analysis_instruction

def initialize_model():
    """
    Inicializa o modelo Gemini com sistema RAG otimizado.
    """


    # Usa instrução centralizada
    base_instruction = get_sql_functioncall_instruction()

    # Descrição detalhada das tabelas e campos válidos (coerente com o RAG)
    fields_description = build_tables_fields_instruction()

    query_func = FunctionDeclaration(
        name="query_business_data",
        description=f"Campos e tabelas disponíveis para consulta:\n{fields_description}",
        parameters={
            "type": "object",
            "properties": {
                "full_table_id": {
                    "type": "string",
                    "description": "ID completo da tabela no BigQuery (PROJECT.DATASET.TABLE). Deve ser um dos listados acima. Sempre sem crase."
                },
                "cte": {
                    "type": "string",
                    "description": "CTE (Common Table Expression). O campo 'cte' DEVE ser SEMPRE preenchido, mesmo para queries simples. Estruture toda consulta usando CTE, por exemplo: WITH t1 AS (SELECT ... FROM ... WHERE ...). Nunca deixe vazio."
                },
                "from_table": {
                    "type": "string",
                    "description": "FROM ou JOIN a ser usado na query final. O campo 'from_table' DEVE ser o alias definido na CTE (ex: 't1', ou um JOIN entre aliases definidos na CTE). Nunca use o nome da tabela original diretamente no FROM se houver CTE."
                },
                "select": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Campos para SELECT com ALIASES obrigatórios para gráficos. Use AS mes, AS valor_total, AS quantidade. Exemplo: ['EXTRACT(MONTH FROM <<coluna_periodo>>) AS mes', 'SUM(<<coluna_de_valor>>) AS valor_total']"
                },
                "where": {
                    "type": "string",
                    "description": "Condições WHERE (SQL puro)"
                },
                "group_by": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Campos para GROUP BY (DEVEM estar no SELECT)"
                },
                "order_by": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Campos para ORDER BY"
                },
                "qualify": {
                    "type": "string",
                    "description": "QUALIFY (para windows functions - ROW_NUMBER, RANK, etc.)"
                },
                "limit": {
                    "type": "integer",
                    "description": "LIMIT (número máximo de registros). NUNCA use junto com QUALIFY"
                }
            },
            "required": ["full_table_id", "select"]
        }
    )

    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        generation_config={
            "temperature": 0.2,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
        },
        system_instruction=base_instruction,
        tools=[query_func]
    )

    return model

def refine_with_gemini_rag(model, user_question: str, user_id: str = "default"):
    """
    Processa pergunta usando sistema RAG otimizado + orientações SQL
    """

    start_time = time.time()
    # Inicia sessão de métricas
    session_id = ai_metrics.start_session(user_id)
    try:
        # Obtém contexto otimizado do RAG de negócios
        rag_context = get_optimized_business_context(user_question)

        # Obtém orientações SQL específicas
        from sql_pattern_rag import get_sql_guidance_for_query
        sql_guidance = get_sql_guidance_for_query(user_question)

        # Cria prompt otimizado com ambos os contextos
        optimized_prompt = f"""
{user_question}

CONTEXTO DE NEGÓCIO (baseado na pergunta):
{rag_context}

ORIENTAÇÕES SQL/BIGQUERY (baseado no tipo de análise):
{sql_guidance}

INSTRUÇÕES CRÍTICAS:

ALIASES OBRIGATÓRIOS:

REGRAS PARA COMPARAÇÕES TEMPORAIS:
"""

        # Adiciona detalhes técnicos do prompt otimizado, contexto RAG e seu tamanho
        tech_details = {
            "optimized_prompt": optimized_prompt,
            "optimized_prompt_length": len(optimized_prompt),
            "rag_context_sent": rag_context,
            "rag_context_length": len(rag_context) if rag_context else 0,
            "sql_guidance_sent": sql_guidance,
            "sql_guidance_length": len(sql_guidance) if sql_guidance else 0,
        }

        # Processa com Gemini
        try:
            response = model.generate_content(optimized_prompt)
        except Exception as e:
            print(f"ERRO GEMINI: {e}")
            return f"Erro ao processar consulta: {str(e)}", None

        # Extrai resposta - verificação simples
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            # Verifica se tem texto direto
            if hasattr(candidate, 'content') and candidate.content:
                if hasattr(candidate.content, 'parts') and candidate.content.parts:
                    part = candidate.content.parts[0]
                    
                    # Prioriza texto direto se disponível
                    if hasattr(part, 'text') and part.text and part.text.strip():
                        response_text = part.text.strip()
                        
                        # Registra uso básico de tokens para texto
                        prompt_tokens = len(optimized_prompt.split())
                        completion_tokens = len(response_text.split())
                        total_tokens = prompt_tokens + completion_tokens
                        token_usage = TokenUsageMetric(
                            prompt_tokens=prompt_tokens,
                            completion_tokens=completion_tokens,
                            total_tokens=total_tokens,
                            estimated_cost_usd=0.001,
                            model_name="gemini-2.0-flash-exp",
                            prompt_type="rag_optimized",
                            optimization_applied=True
                        )
                        ai_metrics.record_token_usage(session_id, user_id, token_usage)
                        
                        return response_text, None
                    
                    # Se não tem texto, verifica function call
                    elif hasattr(part, 'function_call') and part.function_call:
                        function_call = part.function_call
                        
                        # Registra uso básico de tokens para function call
                        prompt_tokens = len(optimized_prompt.split())
                        completion_tokens = 50
                        total_tokens = prompt_tokens + completion_tokens
                        token_usage = TokenUsageMetric(
                            prompt_tokens=prompt_tokens,
                            completion_tokens=completion_tokens,
                            total_tokens=total_tokens,
                            estimated_cost_usd=0.001,
                            model_name="gemini-2.0-flash-exp",
                            prompt_type="rag_optimized",
                            optimization_applied=True
                        )
                        ai_metrics.record_token_usage(session_id, user_id, token_usage)
                        
                        # Cria detalhes técnicos incluindo contexto RAG e orientações SQL
                        tech_details = {
                            "rag_context": rag_context,
                            "sql_guidance": sql_guidance,
                            "model_used": "gemini-2.0-flash-exp",
                            "prompt_type": "rag_optimized_with_sql",
                            "optimization_applied": True,
                                    "function_call_name": function_call.name if hasattr(function_call, 'name') else None,
                                    "optimized_prompt": optimized_prompt,
                                    "prompt_tokens": prompt_tokens,
                                    "completion_tokens": completion_tokens,
                                    "total_tokens": total_tokens
                        }
                        
                        return function_call, tech_details
            
            # Fallback: tenta usar response.text diretamente
            if hasattr(response, 'text') and response.text:
                response_text = response.text.strip()
                
                # Registra uso básico de tokens
                prompt_tokens = len(optimized_prompt.split())
                completion_tokens = len(response_text.split())
                total_tokens = prompt_tokens + completion_tokens
                token_usage = TokenUsageMetric(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    estimated_cost_usd=0.001,
                    model_name="gemini-2.0-flash-exp",
                    prompt_type="rag_optimized",
                    optimization_applied=True
                )
                ai_metrics.record_token_usage(session_id, user_id, token_usage)
                
                # Cria detalhes técnicos incluindo contexto RAG e orientações SQL
                tech_details = {
                    "rag_context": rag_context,
                    "sql_guidance": sql_guidance,
                    "model_used": "gemini-2.0-flash-exp",
                    "prompt_type": "rag_optimized_with_sql",
                    "optimization_applied": True,
                    "response_type": "text",
                    "optimized_prompt": optimized_prompt,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens
                }
                
                return response_text, tech_details
        
        # Se chegou aqui, algo deu errado
        return "Desculpe, não consegui processar sua solicitação. Tente reformular a pergunta.", None
            
    except Exception as e:
        # Para erros, apenas registra de forma simples
        print(f"Erro interno: {e}")
        return f"Erro interno: {str(e)}", None
    finally:
        ai_metrics.end_session(session_id)

def refine_with_gemini(model, user_question: str, user_id: str = "default"):
    """
    Função principal - usa sistema RAG otimizado
    """
    return refine_with_gemini_rag(model, user_question)


from prompt_rules import get_chart_export_instruction
import json
import google.generativeai as genai
import os

def analyze_data_with_gemini(prompt: str, data: list, function_params: dict = None, query: str = None):
    """
    Analisa dados finais e gera resposta completa com gráficos se solicitado
    """
    if function_params is not None:
        if hasattr(function_params, "_values"):
            function_params = {k: v for k, v in function_params.items()}
        elif not isinstance(function_params, dict):
            function_params = dict(function_params)

    # Usa instrução centralizada para gráfico/exportação e refino/tabularização
    chart_export_instruction = get_chart_export_instruction()
    refine_instruction = get_refine_analysis_instruction()

    # Formatação automática dos dados numéricos do DataFrame (2 casas decimais, inplace, sem onerar processamento)
    if data and isinstance(data, list) and len(data) > 0:
        df = pd.DataFrame(data)
        float_cols = df.select_dtypes(include=['float', 'float64', 'float32']).columns
        if len(float_cols) > 0:
            df[float_cols] = df[float_cols].round(2)
        # Atualiza a lista de dicts formatada
        data = df.to_dict(orient='records')

    instruction = f"""
    Você é um ANALISTA SÊNIOR especializado em transformar dados em insights estratégicos.

    MISSÃO: Analisar ESPECÍFICAMENTE os dados fornecidos e responder DIRETAMENTE à pergunta do usuário.

    CONTEXTO COMPLETO:
    - PERGUNTA DO USUÁRIO: "{prompt}"
    - CONSULTA SQL EXECUTADA: {query if query else "Consulta direta"}
    - FILTROS APLICADOS: {function_params.get('where', 'Nenhum') if function_params else 'Nenhum'}

    DADOS ESPECÍFICOS PARA ANÁLISE:
    {json.dumps(data, indent=2, default=str)}

    {chart_export_instruction}

    {refine_instruction}

    IMPORTANTE:
    - Trabalhe APENAS com os dados fornecidos
    - Seja ESPECÍFICO aos números reais
    - Calcule variações REAIS entre os valores
    - Não seja genérico - seja preciso aos dados
    - Responda EXATAMENTE o que foi perguntado
    - Nunca utilize notação científica para apresentar valores numéricos, sempre use formato decimal com até 2 casas decimais.
    """

    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash-exp",
        generation_config={
            "temperature": 0,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
        },
        system_instruction=instruction
    )
    
    try:
        # Usa sistema de retry para contornar bloqueios
        response = None
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                # Prompt direto e focado
                analysis_prompt = f"Analise os dados fornecidos e responda especificamente: {prompt}"
                response = model.generate_content(analysis_prompt)
                
                # Verifica se a resposta foi bloqueada
                if response.candidates and len(response.candidates) > 0:
                    candidate = response.candidates[0]
                    
                    if hasattr(candidate, 'finish_reason') and candidate.finish_reason == 2:
                        print(f"Tentativa {attempt + 1}: Resposta bloqueada por segurança")
                        
                        if attempt < max_retries - 1:
                            # Reformula para contexto empresarial
                            business_prompt = f"""
                            Contexto: Análise de dados empresariais para tomada de decisão.
                            Objetivo: {prompt}
                            Dados: {json.dumps(data[:3], default=str)}... (amostra)
                            Tarefa: Gere análise empresarial dos dados fornecidos.
                            """
                            response = model.generate_content(business_prompt)
                            if response and response.text:
                                break
                            continue
                        else:
                            print("Máximo de tentativas - resposta bloqueada")
                            return "Análise temporariamente indisponível. Tente reformular a pergunta.", None
                    
                    # Resposta válida
                    break
                else:
                    print(f"Tentativa {attempt + 1}: Sem resposta")
                    if attempt == max_retries - 1:
                        return "Não foi possível gerar análise. Tente novamente.", None
                        
            except Exception as e:
                print(f"Tentativa {attempt + 1}: Erro - {str(e)}")
                if attempt == max_retries - 1:
                    return f"Erro na análise: {str(e)}", None
        
        if not response or not response.text:
            return "Não foi possível gerar análise dos dados. Tente novamente.", None
        else:
            response_text = response.text
        
        # Se solicitado gráfico, adiciona instrução
        if any(word in prompt.lower() for word in ['gráfico', 'grafico', 'chart', 'visualização']):
            # Detecta coluna Y automaticamente dos dados
            if data and len(data) > 0:
                columns = list(data[0].keys())
                # X-AXIS: prioriza 'mes', 'semana', 'data', senão primeira coluna string
                x_axis = next((c for c in columns if c.lower() in ['mes', 'semana', 'data', 'periodo', 'month', 'week', 'date', 'period']), None)
                if not x_axis:
                    x_axis = next((c for c in columns if isinstance(data[0].get(c), str)), columns[0])
                # Y-AXIS: primeira coluna numérica diferente do X
                y_col = next((c for c in columns if c != x_axis and isinstance(data[0].get(c), (int, float))), None)
                if not y_col:
                    y_col = columns[0] if columns[0] != x_axis else (columns[1] if len(columns) > 1 else columns[0])
                # COLOR: só se houver terceira coluna categórica diferente de X e Y
                color_col = next((c for c in columns if c not in [x_axis, y_col] and isinstance(data[0].get(c), str)), None)
                if color_col:
                    response_text += f"\nGRAPH-TYPE: line | X-AXIS: {x_axis} | Y-AXIS: {y_col} | COLOR: {color_col}"
                else:
                    response_text += f"\nGRAPH-TYPE: line | X-AXIS: {x_axis} | Y-AXIS: {y_col}"
            else:
                response_text += "\nGRAPH-TYPE: line | X-AXIS: x | Y-AXIS: y"
        
        # Se solicitado exportação, adiciona instrução
        if any(word in prompt.lower() for word in ['exportar', 'excel', 'planilha', 'csv', 'baixar']):
            response_text += "\nEXPORT-INFO: FORMATO: excel"
        
        # TESTE REAL COM GEMINI (comentado por agora)
        # response = model.generate_content(f"Analise os dados fornecidos e responda à pergunta: {prompt}")
        # if not response or not response.text:
        #     return "Não foi possível gerar análise dos dados.", None
        # response_text = response.text
        
        chart_info = None

        # Extrai instrução de gráfico, se houver
        if "GRAPH-TYPE:" in response_text:
            try:
                graph_part = response_text.split("GRAPH-TYPE:")[1].strip()
                
                # Parse mais robusto dos parâmetros
                graph_type = graph_part.split("|")[0].strip().lower()
                
                # Extração segura do X-AXIS
                if "X-AXIS:" in graph_part:
                    x_axis = graph_part.split("X-AXIS:")[1].split("|")[0].strip()
                    # Remove escapes indevidos (ex: mod\_ds -> mod_ds)
                    x_axis = x_axis.replace('\\_', '_')
                else:
                    print("X-AXIS nao encontrado na instrucao do grafico")
                    return response_text, None
                    
                # Extração segura do Y-AXIS  
                if "Y-AXIS:" in graph_part:
                    y_axis = graph_part.split("Y-AXIS:")[1].split("|")[0].strip()
                    # Remove escapes indevidos (ex: total\_vendas -> total_vendas)
                    y_axis = y_axis.replace('\\_', '_')
                else:
                    print("Y-AXIS nao encontrado na instrucao do grafico")
                    return response_text, None
                    
                # Extração segura do COLOR (opcional)
                color = None
                if "COLOR:" in graph_part:
                    color_raw = graph_part.split("COLOR:")[1].strip()
                    # Remove quebras de linha e espaços extras
                    color = color_raw.split('\n')[0].split('\r')[0].strip()
                    
                    # Se color está vazio ou é "None", remove
                    if not color or color.lower() == "none" or color == "":
                        color = None
                    else:
                        print(f"COLOR detectado: '{color}'")

                print(f"Parametros do grafico - Tipo: {graph_type}, X: {x_axis}, Y: {y_axis}, Color: {color}")
                
                # Converte dados para DataFrame
                df_data = pd.DataFrame(data)
                
                fig = generate_chart(df_data, graph_type, x_axis, y_axis, color)
                
                if fig:
                    chart_info = {
                        "type": graph_type,
                        "x": x_axis,
                        "y": y_axis,
                        "color": color,
                        "fig": fig,
                    }
                    print("Grafico gerado com sucesso")
                else:
                    print(f"Falha ao gerar grafico. Tipo: {graph_type}, X: {x_axis}, Y: {y_axis}, Color: {color}")
                    
            except Exception as e:
                print(f"Erro ao processar grafico: {e}")
                chart_info = None

        # Verificar se o usuário solicitou exportação
        export_requested = any(keyword in prompt.lower() for keyword in 
                              ['exportar', 'excel', 'planilha', 'csv', 'baixar']) or "EXPORT-INFO:" in response_text
        
        # Gerar links de exportação se solicitado
        export_links = []
        export_info = {}
        
        if export_requested:
            try:
                # Gerar Excel
                excel_bytes = generate_excel_bytes(data)
                if excel_bytes:
                    excel_filename = f"dados_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
                    excel_link = create_styled_download_button(excel_bytes, excel_filename, "Excel")
                    export_links.append(excel_link)
                    export_info['excel'] = excel_filename
                
                # Gerar CSV
                csv_bytes = generate_csv_bytes(data)
                if csv_bytes:
                    csv_filename = f"dados_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
                    csv_link = create_styled_download_button(csv_bytes, csv_filename, "CSV")
                    export_links.append(csv_link)
                    export_info['csv'] = csv_filename
                    
            except Exception as e:
                print(f"Erro ao gerar exportações: {e}")
                export_links = []
                export_info = {'error': str(e)}

        # Prepara tech_details
        tech_details = {
            "function_params": function_params,
            "query": query,
            "raw_data": data,
            "chart_info": chart_info,
            "export_links": export_links,
            "export_info": export_info,
        }
        
        # Remove instruções de gráfico e export da resposta final
        response_text = response_text.split("GRAPH-TYPE:")[0].strip()
        response_text = response_text.split("EXPORT-INFO:")[0].strip()
        
        return response_text, tech_details
        
    except Exception as e:
        print(f"Erro na analise com Gemini: {e}")
        return f"Erro ao analisar dados: {str(e)}", None

def initialize_rag_system():
    """
    Inicializa sistema RAG
    """
    print("🔄 Inicializando sistema RAG...")
    from business_metadata_rag import setup_business_rag
    setup_business_rag()
    print("✅ Sistema RAG inicializado com sucesso!")

def should_reuse_data(current_prompt, user_history):
    """
    Função simples que sempre retorna False para forçar nova consulta
    (compatibilidade durante limpeza do sistema)
    """
    return {"should_reuse": False, "reason": "Nova consulta necessária"}

def should_reuse_data(model, current_prompt: str, user_history: list = None) -> dict:
    """
    VERSÃO OTIMIZADA: Prioriza dados mais recentes para casos como 'agora gere um gráfico desse dado'
    """
    if not user_history:
        return {"should_reuse": False, "reason": "Nenhum histórico disponível"}
    
    prompt_lower = current_prompt.lower()
    
    # DETECÇÃO AUTOMÁTICA DE CONTINUIDADE (casos como "agora gere um gráfico desse dado")
    continuity_indicators = [
        "agora", "desse", "destes", "dessa", "dessas", "do resultado", "dos dados",
        "da consulta", "da tabela", "deste", "desta"
    ]
    
    visualization_requests = [
        "gráfico", "grafico", "chart", "visualização", "visualizacao", 
        "plotar", "plot", "curva", "linha", "barra"
    ]
    
    export_requests = [
        "exportar", "excel", "planilha", "csv", "baixar", "download"
    ]
    
    # CASO 1: CONTINUIDADE CLARA - usa dados mais recentes automaticamente
    has_continuity = any(ind in prompt_lower for ind in continuity_indicators)
    has_visualization = any(vis in prompt_lower for vis in visualization_requests)
    has_export = any(exp in prompt_lower for exp in export_requests)
    
    if has_continuity or (has_visualization and not any(word in prompt_lower for word in ["vendas", "produtos", "clientes", "top", "2024", "2025"])):
        # Usa dados mais recentes
        most_recent = next((item for item in user_history if item.get('raw_data_count', 0) > 0), None)
        if most_recent:
            return {
                "should_reuse": True,
                "reason": "Continuidade detectada - usando dados mais recentes",
                "interaction_id": most_recent.get('id'),
                "auto_selected": True
            }
    
    return {"should_reuse": False, "reason": "Nova consulta necessária"}

# Função para gerar gráficos (mantida como estava)
def generate_chart(data, chart_type, x_axis, y_axis, color=None):
    """
    Cria gráficos com tema adaptativo (dark/light)
    """
    
    
    # Detecta tema atual do Streamlit
    theme_mode = st.session_state.get('theme_mode', 'escuro')
    is_dark_theme = theme_mode == 'escuro'
    
    # Cores adaptativas baseadas no tema
    if is_dark_theme:
        # Tema escuro
        color_palette = [
            '#00d4ff', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6',
            '#06b6d4', '#10b981', '#f97316', '#ec4899', '#6366f1'
        ]
        bg_color = 'rgba(0,0,0,0)'
        text_color = '#e5e7eb'
        grid_color = 'rgba(255,255,255,0.1)'
        legend_bg = 'rgba(20, 20, 20, 0.9)'
        legend_border = 'rgba(255,255,255,0.2)'
    else:
        # Tema claro
        color_palette = [
            '#2563eb', '#059669', '#d97706', '#dc2626', '#7c3aed',
            '#0891b2', '#065f46', '#ea580c', '#be185d', '#4338ca'
        ]
        bg_color = 'rgba(255,255,255,0)'
        text_color = '#374151'
        grid_color = 'rgba(0,0,0,0.1)'
        legend_bg = 'rgba(255, 255, 255, 0.95)'
        legend_border = 'rgba(0,0,0,0.1)'
    
    if data.empty:
        return None
        
    # Configuração adaptativa para todos os gráficos
    layout_config = {
        'plot_bgcolor': bg_color,
        'paper_bgcolor': bg_color,
        'font': {'color': text_color, 'size': 12, 'family': 'Arial, sans-serif'},
        'margin': {'l': 80, 'r': 80, 't': 80, 'b': 80},
        'showlegend': True,
        'legend': {
            'orientation': 'h',
            'yanchor': 'bottom',
            'y': -1.2,
            'xanchor': 'center',
            'x': 0.5,
            'bgcolor': legend_bg,
            'bordercolor': legend_border,
            'borderwidth': 1,
            'indentation': 20,
            'font': {'size': 11, 'color': text_color}
        },
        'xaxis': {
            'title': {'font': {'size': 14, 'color': text_color}},
            'tickfont': {'size': 11, 'color': text_color}
        },
        'yaxis': {
            'title': {'font': {'size': 14, 'color': text_color}},
            'tickfont': {'size': 11, 'color': text_color}
        }
    }
    
    try:
        # Normaliza nomes de colunas (remove espaços)
        data.columns = [str(col).strip() for col in data.columns]
        x_axis = str(x_axis).strip()
        y_axis = str(y_axis).strip()

        # --- Tratamento generalista para gráficos temporais ---
        # Detecta se x_axis é temporal (semana, mes, dia, data, ano)
        temporal_patterns = ['semana', 'mes', 'dia', 'data', 'ano', 'week', 'month', 'date', 'year']
        is_temporal = any(p in x_axis.lower() for p in temporal_patterns)
        # Detecta coluna de categoria (color) se existir
        category_col = color if color and color in data.columns else None
        if not category_col:
            # Busca coluna categórica diferente de x_axis e y_axis
            for col in data.columns:
                if col not in [x_axis, y_axis] and not pd.api.types.is_numeric_dtype(data[col]):
                    category_col = col
                    break

        if is_temporal and category_col:
            # Completa matriz de períodos x categorias
            all_temporals = sorted(data[x_axis].unique())
            all_categories = sorted(data[category_col].unique())
            import pandas as pd
            idx = pd.MultiIndex.from_product([all_temporals, all_categories], names=[x_axis, category_col])
            data = data.set_index([x_axis, category_col]).reindex(idx, fill_value=0).reset_index()
            # Ordena eixo temporal
            data[x_axis] = pd.Categorical(data[x_axis], ordered=True, categories=all_temporals)
            data = data.sort_values(x_axis)

        # 1. Se color não existe no DataFrame, ou é igual a x_axis ou y_axis, ignora (None)
        color_final = color.strip() if isinstance(color, str) else color
        if (
            color_final is None or
            color_final not in data.columns or
            color_final == x_axis or
            color_final == y_axis
        ):
            color_final = None

        # 2. Se color_final ainda é None, só usa cor se houver uma terceira coluna categórica diferente de x_axis e y_axis
        if color_final is None:
            for col in data.columns:
                if col not in [x_axis, y_axis] and not pd.api.types.is_numeric_dtype(data[col]):
                    color_final = col
                    break
            # Se não encontrou, mantém color_final=None

        # 3. Se só existem x_axis e y_axis, nunca usa cor
        if len(data.columns) <= 2:
            color_final = None

        # Trata eixo X como categoria se for string
        if pd.api.types.is_object_dtype(data[x_axis]):
            data[x_axis] = data[x_axis].astype(str)

        # Geração do gráfico
        if chart_type in ['line', 'linha']:
            fig = px.line(
                data, x=x_axis, y=y_axis, color=color_final,
                color_discrete_sequence=color_palette,
                line_shape='spline'
            )
            fig.update_traces(line=dict(width=3))
        elif chart_type in ['bar', 'barra']:
            fig = px.bar(
                data, x=x_axis, y=y_axis, color=color_final,
                color_discrete_sequence=color_palette
            )
        elif chart_type in ['scatter', 'dispersao']:
            fig = px.scatter(
                data, x=x_axis, y=y_axis, color=color_final,
                color_discrete_sequence=color_palette,
                size_max=15
            )
        else:
            fig = px.bar(data, x=x_axis, y=y_axis, color=color_final,
                        color_discrete_sequence=color_palette)
        # --- Ajuste ainda mais agressivo do eixo Y para ignorar outliers e deixar o gráfico legível ---
        if fig is not None and y_axis in data.columns:
            y_vals = data[y_axis].dropna()
            if len(y_vals) > 0:
                y_min = y_vals.min()
                y_max_real = y_vals.max()
                y_pctl = y_vals.quantile(0.90)
                # Detecta outlier: se o valor máximo for mais que 2x o percentil 90, considera outlier
                is_outlier = y_max_real > y_pctl * 1.7
                if is_outlier and y_max_real > 0:
                    # Aplica escala logarítmica
                    fig.update_yaxes(type="log")
                    annotation_color = text_color
                    fig.add_annotation(
                        text="Escala logarítmica aplicada devido a outlier",
                        xref="paper", yref="paper",
                        x=0.99, y=0.98, showarrow=False,
                        font=dict(size=11, color=annotation_color),
                        bgcolor=bg_color,
                        bordercolor=annotation_color,
                        borderwidth=0,
                        opacity=0.7,
                        xanchor="right", yanchor="top"
                    )
                else:
                    # Ajuste proporcional padrão
                    y_top = max(y_max_real, min(y_pctl * 1.10, y_max_real * 2))
                    fig.update_yaxes(range=[y_min, y_top])
                    if y_top < y_max_real:
                        annotation_color = text_color
                        fig.add_annotation(
                            text=f"Valores acima de {y_top:,.0f} não exibidos",
                            xref="paper", yref="paper",
                            x=0.99, y=0.98, showarrow=False,
                            font=dict(size=11, color=annotation_color),
                            bgcolor=bg_color,
                            bordercolor=annotation_color,
                            borderwidth=0,
                            opacity=0.7,
                            xanchor="right", yanchor="top"
                        )

        # Aplica layout adaptativo
        fig.update_layout(layout_config)
        # Grid adaptativo ao tema
        fig.update_xaxes(
            showgrid=True, gridwidth=1, gridcolor=grid_color,
            showline=True, linewidth=1, linecolor=grid_color
        )
        fig.update_yaxes(
            showgrid=True, gridwidth=1, gridcolor=grid_color,
            showline=True, linewidth=1, linecolor=grid_color
        )
        return fig
    except Exception as e:
        print(f"Erro ao criar gráfico: {e}")
        return None