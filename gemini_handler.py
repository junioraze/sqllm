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
from utils import create_styled_download_button, generate_excel_bytes, generate_csv_bytes, dict_to_markdown_table, show_aggrid_table
from datetime import datetime
import time
import os
import streamlit as st
# Sistema RAG obrigatório
from business_metadata_rag import get_business_rag_instance, get_optimized_business_context
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
                            model_name=MODEL_NAME,
                            prompt_type="rag_optimized",
                            optimization_applied=True
                        )
                        ai_metrics.record_token_usage(session_id, user_id, token_usage)
                        # Adiciona tokens ao tech_details
                        tech_details["prompt_tokens"] = prompt_tokens
                        tech_details["completion_tokens"] = completion_tokens
                        tech_details["total_tokens"] = total_tokens
                        return response_text, tech_details
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
                            model_name=MODEL_NAME,
                            prompt_type="rag_optimized",
                            optimization_applied=True
                        )
                        ai_metrics.record_token_usage(session_id, user_id, token_usage)
                        # Adiciona tokens ao tech_details
                        tech_details["prompt_tokens"] = prompt_tokens
                        tech_details["completion_tokens"] = completion_tokens
                        tech_details["total_tokens"] = total_tokens
                        tech_details["function_call_name"] = function_call.name if hasattr(function_call, 'name') else None
                        tech_details["model_used"] = MODEL_NAME
                        tech_details["prompt_type"] = "rag_optimized_with_sql"
                        tech_details["optimization_applied"] = True
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
                    model_name=MODEL_NAME,
                    prompt_type="rag_optimized",
                    optimization_applied=True
                )
                ai_metrics.record_token_usage(session_id, user_id, token_usage)
                # Adiciona tokens ao tech_details
                tech_details["prompt_tokens"] = prompt_tokens
                tech_details["completion_tokens"] = completion_tokens
                tech_details["total_tokens"] = total_tokens
                tech_details["model_used"] = MODEL_NAME
                tech_details["prompt_type"] = "rag_optimized_with_sql"
                tech_details["optimization_applied"] = True
                tech_details["response_type"] = "text"
                return response_text, tech_details

        # Se chegou aqui, algo deu errado
        return "Desculpe, não consegui processar sua solicitação. Tente reformular a pergunta.", None

    except Exception as e:
        # Para erros, apenas registra de forma simples
        print(f"Erro interno: {e}")
        return f"Erro interno: {str(e)}", None

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
    print("[DEBUG] Entrou em analyze_data_with_gemini")
    """
    Analisa dados finais e gera resposta completa com gráficos se solicitado
    """

    # Fuzzy matching para nomes de colunas
    def fuzzy_column(col, columns):
        if col in columns:
            return col
        # Busca por coluna que contenha o termo (case-insensitive)
        matches = [c for c in columns if col.lower() in c.lower()]
        if len(matches) == 1:
            print(f"[FuzzyMatch] '{col}' não encontrado, usando '{matches[0]}'")
            return matches[0]
        elif len(matches) > 1:
            print(f"[FuzzyMatch] '{col}' não encontrado, múltiplas opções: {matches}. Usando original.")
            return col
        else:
            print(f"[FuzzyMatch] '{col}' não encontrado, sem opções semelhantes. Usando original.")
            return col

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

    # Lista de colunas disponíveis para orientar o modelo
    columns_list = list(df.columns) if 'df' in locals() else (list(data[0].keys()) if data and isinstance(data, list) and isinstance(data[0], dict) else [])

    instruction = f"""
    Você é um ANALISTA SÊNIOR especializado em transformar dados em insights estratégicos.

    MISSÃO: Analisar ESPECÍFICAMENTE os dados fornecidos e responder DIRETAMENTE à pergunta do usuário.

    CONTEXTO COMPLETO:
    - PERGUNTA DO USUÁRIO: "{prompt}"
    - CONSULTA SQL EXECUTADA: {query if query else "Consulta direta"}
    - FILTROS APLICADOS: {function_params.get('where', 'Nenhum') if function_params else 'Nenhum'}

    DADOS ESPECÍFICOS PARA ANÁLISE:
    {json.dumps(data, indent=2, default=str)}

    COLUNAS DISPONÍVEIS NO DATAFRAME PARA GRÁFICO:
    {columns_list}

    {chart_export_instruction}

    ORIENTAÇÃO CRÍTICA PARA GRÁFICO:
    - Sempre gere os parâmetros do gráfico (X, Y, COLOR) usando EXATAMENTE os nomes das colunas listadas acima, sem traduzir, abreviar ou modificar.
    - Se não houver coluna adequada para COLOR, deixe COLOR vazio ou None.
    - Se não houver coluna numérica para Y, explique e não gere gráfico.
    - Se não houver coluna categórica para X, explique e não gere gráfico.

    IMPORTANTE:
    - Trabalhe APENAS com os dados fornecidos
    - Seja ESPECÍFICO aos números reais
    - Calcule variações REAIS entre os valores
    - Não seja genérico - seja preciso aos dados
    - Responda EXATAMENTE o que foi perguntado
    - Nunca utilize notação científica para apresentar valores numéricos, sempre use formato decimal com até 2 casas decimais.
    """


    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
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
        analysis_prompt = instruction  # prompt COMPLETO enviado ao modelo
        analysis_prompt_tokens = len(analysis_prompt.split())
        for attempt in range(max_retries):
            try:
                response = model.generate_content(analysis_prompt)
                # Verifica se a resposta foi bloqueada
                if response.candidates and len(response.candidates) > 0:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'finish_reason') and candidate.finish_reason == 2:
                        print(f"Tentativa {attempt + 1}: Resposta bloqueada por segurança")
                        if attempt < max_retries - 1:
                            # Reformula para contexto empresarial
                            business_prompt = f"""
                            print(f"[DEBUG] Prompt recebido: {prompt}")
                            print(f"[DEBUG] Dados retornados para gráfico: {data}")
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
                    
                print(f"[DEBUG] Tentando gerar gráfico com colunas: {list(df.columns)}")
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
                print(f"[DEBUG] Tentando gerar gráfico com colunas: {list(df_data.columns)}")
                # Aplica fuzzy matching para garantir que os nomes de colunas existem no DataFrame
                # Garante que os nomes das colunas não tenham espaços/quebras de linha
                x_axis_clean = x_axis.strip() if isinstance(x_axis, str) else x_axis
                y_axis_clean = y_axis.strip() if isinstance(y_axis, str) else y_axis
                color_clean = color.strip() if isinstance(color, str) else color

                x_axis_real = fuzzy_column(x_axis_clean, list(df_data.columns))
                y_axis_real = fuzzy_column(y_axis_clean, list(df_data.columns))
                color_real = fuzzy_column(color_clean, list(df_data.columns)) if color_clean else None
                fig = generate_chart(df_data, graph_type, x_axis_real, y_axis_real, color_real)
                
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
        completion_tokens = len(response_text.split()) if response_text else 0
        total_tokens = analysis_prompt_tokens + completion_tokens
        tech_details = {
            "function_params": function_params,
            "query": query,
            "raw_data": data,
            "chart_info": chart_info,
            "export_links": export_links,
            "export_info": export_info,
            "analyze_prompt": analysis_prompt,  # prompt COMPLETO
            "analyze_prompt_tokens": analysis_prompt_tokens,
            "analyze_completion_tokens": completion_tokens,
            "analyze_total_tokens": total_tokens,
        }
        
        # Remove instruções de gráfico e export da resposta final
        response_text = response_text.split("GRAPH-TYPE:")[0].strip()
        response_text = response_text.split("EXPORT-INFO:")[0].strip()
        
        # Se a resposta for uma lista de dicts (tabela), retorna para exibição no handler
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            tech_details["aggrid_data"] = data
        return response_text, tech_details
        
    except Exception as e:
        print(f"Erro na analise com Gemini: {e}")
        return f"Erro ao analisar dados: {str(e)}", None

def initialize_rag_system():
    """
    Inicializa sistema RAG
    """
    print("🔄 Inicializando sistema RAG...")
    from business_metadata_rag import get_business_rag_instance
    get_business_rag_instance()
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

def generate_chart(data, chart_type, x_axis, y_axis, color=None):
    # Limite de caracteres para itens da legenda/categorias
    LEGEND_LABEL_MAXLEN = 22

    # Trunca os labels da coluna de cor se necessário
    if color and color in data.columns:
        data[color] = data[color].astype(str).apply(lambda x: x[:LEGEND_LABEL_MAXLEN] + '…' if len(x) > LEGEND_LABEL_MAXLEN else x)

    # Trunca os labels da coluna de categorias (x_axis) se for string/categórica
    if x_axis and x_axis in data.columns:
        if data[x_axis].dtype == object or str(data[x_axis].dtype).startswith('str'):
            data[x_axis] = data[x_axis].astype(str).apply(lambda x: x[:LEGEND_LABEL_MAXLEN] + '…' if len(x) > LEGEND_LABEL_MAXLEN else x)
    """
    Cria gráficos com tema adaptativo (dark/light) e layout responsivo
    """
    import streamlit as st
    
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
        
    # CONFIGURAÇÃO RESPONSIVA ATUALIZADA - EXTENSÃO HORIZONTAL
    layout_config = {
        'plot_bgcolor': bg_color,
        'paper_bgcolor': bg_color,
        'font': {'color': text_color, 'size': 14, 'family': 'Arial, sans-serif'},
        'margin': {'l': 20, 'r': 20, 't': 40, 'b': 80},  # Margens pequenas para ocupar mais espaço
        'showlegend': True,
        'autosize': True,
        'height': 480,
        'legend': {
            'orientation': 'h',
            'yanchor': 'bottom',
            'y': -1.2,  # Mais próximo do gráfico
            'xanchor': 'center',
            'x': 0.5,
            'bgcolor': legend_bg,
            'bordercolor': legend_border,
            'borderwidth': 0,
            'font': {'size': 11, 'color': text_color},
            'itemwidth': 140,
            'indentation': 20,
            'tracegroupgap': 20,
        },
        'xaxis': {
            'title': {'font': {'size': 16, 'color': text_color}},
            'tickfont': {'size': 13, 'color': text_color},
            'automargin': True
        },
        'yaxis': {
            'title': {'font': {'size': 16, 'color': text_color}},
            'tickfont': {'size': 13, 'color': text_color},
            'automargin': True
        }
    }
    
    try:
        if chart_type in ['line', 'linha']:
            fig = px.line(
                data, x=x_axis, y=y_axis, color=color,
                color_discrete_sequence=color_palette,
                line_shape='spline'
            )
            fig.update_traces(line=dict(width=3))
            
        elif chart_type in ['bar', 'barra']:
            fig = px.bar(
                data, x=x_axis, y=y_axis, color=color,
                color_discrete_sequence=color_palette
            )
            
        elif chart_type in ['scatter', 'dispersao']:
            fig = px.scatter(
                data, x=x_axis, y=y_axis, color=color,
                color_discrete_sequence=color_palette,
                size_max=15
            )
            
        else:
            fig = px.bar(data, x=x_axis, y=y_axis, color=color,
                        color_discrete_sequence=color_palette)
        
        # Aplica layout responsivo
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