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
                "cte": {
                    "type": "string",
                    "description": (
                        "Bloco WITH contendo todas as CTEs necessárias para a consulta. "
                        "Sempre preencha este campo, mesmo para queries simples. "
                        "Exemplo: WITH t1 AS (SELECT ... FROM ... WHERE ...), t2 AS (...). "
                        "Nunca inclua o SELECT final aqui. "
                        "Jamais gere comentários SQL (nem --, nem /* ... */) em nenhuma parte da query."
                        "CTE's que tem dependencia de outras CTE's NUNCA devem consultar diretamente o BQ, elas devem ter no from a referencia a CTE da qual dependem."
                    )
                },
                "from_table": {
                    "type": "string",
                    "description": (
                        "Alias ou JOIN entre aliases definidos nas CTEs para o SELECT final. "
                        "Exemplo: 't1' ou 't1 JOIN t2 ON ...'. "
                        "Nunca use o nome da tabela original diretamente no FROM se houver CTE."
                    )
                },
                "select": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Lista de campos para o SELECT final. "
                        "Inclua aliases definidos nas CTEs e/ou campos simples disponíveis no resultado das colunas presentes nas tabelas do parametro from_table. "
                        "Nunca use expressões originais diretamente, apenas aliases ou campos simples que realmente existem no resultado das tabelas do parametro from_table."
                    )
                },
                "order_by": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Lista de campos para ORDER BY no SELECT final. "
                        "Use apenas aliases ou campos simples que existem no resultado das colunas presentes nas tabelas do parametro from_table. "
                        "Nunca use expressões, apenas nomes de colunas/aliases que estão disponíveis nas tabelas do parametro from_table."
                    )
                },
                "where": {
                    "type": "string",
                    "description": (
                        "Condições para o WHERE do SELECT final. "
                        "Filtre usando apenas aliases ou campos simples que existem no resultado das colunas presentes nas tabelas do parametro from_table. "
                        "Para rankings, filtre pelo campo analítico criado na CTE (ex: ranking <= N)."
                    )
                }
            },
            "required": ["select", "cte", "from_table", "order_by"]
        }
    )

    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        generation_config={
            "temperature": 0.1,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 16000,
        },
        system_instruction=base_instruction,
        tools=[query_func]
    )

    return model

def refine_with_gemini_rag(model, user_question: str, user_id: str = "default"):
    # O print de debug só pode ser chamado após a atribuição de rag_context
    """
    Processa pergunta usando sistema RAG otimizado + orientações SQL
    """

    start_time = time.time()
    # Inicia sessão de métricas
    session_id = ai_metrics.start_session(user_id)
    try:
        # Obtém contexto otimizado do RAG de negócios usando v3 (melhor)
        try:
            from business_metadata_rag_v3 import BusinessMetadataRAGv3
            rag_v3 = BusinessMetadataRAGv3()
            best_table = rag_v3.get_best_table(user_question, debug=False)
            top_tables = rag_v3.get_top_3_tables(user_question, debug=False)
            
            if best_table:
                rag_context = f"📊 Tabela identificada: {best_table}\nTabelas alternativas: {', '.join(top_tables)}\n\nUtilize a tabela identificada para construir a consulta SQL."
                
                # 🔥 NOVO: Injeta LISTA DE CAMPOS VÁLIDOS para a tabela identificada
                from prompt_rules import build_field_whitelist_instruction
                field_instruction = build_field_whitelist_instruction(best_table)
                rag_context += "\n\n" + field_instruction
            else:
                # Fallback para v2
                rag_context = get_optimized_business_context(user_question)
        except Exception as e:
            print(f"[RAG v3] Erro, usando fallback v2: {e}")
            rag_context = get_optimized_business_context(user_question)
        
        # Garante que o contexto seja sempre string (nunca dict)
        if isinstance(rag_context, dict):
            import json
            rag_context = json.dumps(rag_context, ensure_ascii=False, indent=2)
        elif isinstance(rag_context, list):
            import json
            rag_context = '\n'.join([json.dumps(item, ensure_ascii=False, indent=2) if isinstance(item, dict) else str(item) for item in rag_context])

        # Obtém orientações SQL específicas
        from sql_pattern_rag import get_sql_guidance_for_query
        sql_guidance = get_sql_guidance_for_query(user_question)

        # Detecta se a pergunta envolve datas/períodos
        date_keywords = ['mes', 'mês', 'ano', 'ano', 'data', 'data', 'período', 'periodo', 'trimestre', 'semana', 'dia', 'mensal', 'anual', 'diário', 'diario', 'por mês', 'por mes']
        has_date_aggregation = any(keyword in user_question.lower() for keyword in date_keywords)
        
        # Cria instrução de formatação de datas se necessário
        date_guidance = ""
        if has_date_aggregation:
            date_guidance = """

INSTRUÇÕES CRÍTICAS PARA FORMATAÇÃO DE DATAS:
⚠️  SEMPRE filtrar NULL antes de formatar:
  1. Na CTE de limpeza, converta: CAST(SAFE.PARSE_TIMESTAMP('%Y-%m-%d %H:%M:%S', Data_da_Venda) AS DATE) AS data_venda
  2. Adicione: WHERE data_venda IS NOT NULL
  3. Só depois formate com FORMAT_DATE() ou EXTRACT()
  
EXEMPLOS CORRETOS:
✅ WITH cte_limpeza AS (
     SELECT CAST(SAFE.PARSE_TIMESTAMP('%Y-%m-%d %H:%M:%S', Data_da_Venda) AS DATE) AS data_venda
     FROM tabela
     WHERE Data_da_Venda IS NOT NULL
   ),
   cte_agregacao AS (
     SELECT FORMAT_DATE('%Y-%m', data_venda) AS mes_ano, COUNT(*) AS total
     FROM cte_limpeza
     GROUP BY mes_ano
   )
   SELECT mes_ano, total FROM cte_agregacao ORDER BY mes_ano

❌ ERRADO - gera linha com 'None':
   SELECT FORMAT_DATE('%Y-%m', Data_da_Venda) AS mes_ano
   FROM tabela
   GROUP BY mes_ano  -- Agrupa NULLs também! Não converte timestamp string primeiro!

CONVERSÃO CORRETA DO DATA_DA_VENDA (STRING '2025-09-02 00:00:00'):
- Sempre usar: CAST(SAFE.PARSE_TIMESTAMP('%Y-%m-%d %H:%M:%S', Data_da_Venda) AS DATE)
- Depois: FORMAT_DATE('%Y-%m', [resultado acima]) para mês-ano
- Depois: EXTRACT(YEAR FROM [resultado acima]) para apenas ano
- Depois: EXTRACT(MONTH FROM [resultado acima]) para apenas mês
"""

        # Detecta se é pergunta sobre comparações (múltiplos períodos/categorias)
        comparison_keywords = ['comparacao', 'comparação', 'vs', 'versus', 'diferenca', 'diferença', 'evolucao', 'evolução', 'por ano', 'por mes', 'por mês', 'por periodo', 'por período']
        has_comparison = any(keyword in user_question.lower() for keyword in comparison_keywords)
        
        comparison_guidance = ""
        if has_comparison:
            comparison_guidance = """

⚠️  FORMATO DE RESULTADO PARA COMPARAÇÕES (MUITO IMPORTANTE):
Se o resultado precisa comparar múltiplos períodos/categorias:
- NÃO use PIVOT (colunas como 'ano_2024', 'ano_2025')
- USE formato "LONG" com colunas: [coluna_agrupamento] | [categoria/período] | [valor]

EXEMPLO ERRADO (PIVOT):
  mes | ano_2024 | ano_2025
  1   | 3092     | 3827
  2   | 3357     | 3585

EXEMPLO CORRETO (LONG/MELTED):
  mes | ano | quantidade
  1   | 2024 | 3092
  1   | 2025 | 3827
  2   | 2024 | 3357
  2   | 2025 | 3585

O formato LONG permite:
✅ Colorir linhas/barras por categoria/período
✅ Comparação lado-a-lado no gráfico
✅ Legendas automáticas
❌ PIVOT não funciona bem com gráficos de comparação
"""

        # Cria prompt otimizado com ambos os contextos
        # 🔥 CRITICAL: Coloca REGRAS CRÍTICAS PRIMEIRO, antes da pergunta!
        optimized_prompt = f"""
⛔⛔⛔ REGRAS CRÍTICAS OBRIGATÓRIAS (LEIA PRIMEIRO ANTES DE TUDO) ⛔⛔⛔

Se a pergunta envolve FILTROS específicos de negócio (tipo de produto, tipo de contrato, etc):
- SEMPRE aplique os filtros conforme as REGRAS CRÍTICAS na seção CONTEXTO DE NEGÓCIO
- Exemplo: "Para filtro por tipo de veículo use Negocio_CC: '2R' para motos, '4R' para carros"
- Se pergunta pede "carros" → DEVE gerar: WHERE Negocio_CC = '4R'
- Se pergunta pede "motos" → DEVE gerar: WHERE Negocio_CC = '2R'
- NUNCA retorne dados sem aplicar esses filtros - é erro crítico!

================================================================================

PERGUNTA DO USUÁRIO:
{user_question}

CONTEXTO DE NEGÓCIO (baseado na pergunta):
{rag_context}

ORIENTAÇÕES SQL/BIGQUERY (baseado no tipo de análise):
{sql_guidance}{date_guidance}{comparison_guidance}

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
        # DEBUG: Sempre printa o prompt final enviado ao Gemini
        print("\n[DEBUG][GEMINI_PROMPT] Prompt final enviado ao Gemini:\n" + optimized_prompt)
        print("[DEBUG][RAG_CONTEXT] Contexto RAG injetado:\n" + str(rag_context))
        print("[DEBUG][SQL_GUIDANCE] Orientações SQL injetadas:\n" + str(sql_guidance))

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

def refine_sql_with_error(model, user_question: str, error_message: str, previous_sql: str, table_name: str, best_table_score: float = None) -> tuple:
    """
    Refina SQL quando há erro na execução, mesmo após RAG ter acertado a tabela.
    
    Args:
        model: Modelo Gemini inicializado
        user_question: Pergunta original do usuário
        error_message: Mensagem de erro do BigQuery
        previous_sql: SQL que falhou
        table_name: Tabela identificada pelo RAG (acertada)
        best_table_score: Score do RAG para a tabela (para diagnosticar)
    
    Returns:
        tuple: (response_dict, tech_details)
    """
    print(f"\n🔁 [REFINAMENTO] RAG acertou tabela '{table_name}' mas SQL falhou")
    print(f"❌ Erro: {error_message}")
    print(f"🔄 Tentando refinar SQL com Gemini...")
    
    try:
        from prompt_rules import build_field_whitelist_instruction
        field_instruction = build_field_whitelist_instruction(table_name)
        
        # Injeta instruções de refinamento
        refine_prompt = f"""
REFINAMENTO DE QUERY SQL COM ERRO

PERGUNTA ORIGINAL:
{user_question}

TABELA IDENTIFICADA (CORRETA):
{table_name}

SQL QUE FALHOU:
{previous_sql}

ERRO BIGQUERY:
{error_message}

INSTRUÇÕES DE REFINAMENTO:
1. A tabela foi CORRETAMENTE identificada como '{table_name}'
2. O erro SQL sugere que a estrutura da query está incorreta
3. Revise especialmente:
   - Sintaxe de PIVOT (se usado)
   - Alias de colunas em PIVOT
   - Sintaxe de função window
   - Tipos de conversão de data
4. Gere uma SQL ALTERNATIVA que evite o erro

{field_instruction}

GERE UMA NOVA PROPOSTA DE SQL/CTE CORRIGIDA:
"""
        
        # Chama Gemini para refinamento
        response = model.generate_content(refine_prompt)
        
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and candidate.content:
                if hasattr(candidate.content, 'parts') and candidate.content.parts:
                    part = candidate.content.parts[0]
                    if hasattr(part, 'text') and part.text:
                        response_text = part.text.strip()
                        
                        # Tenta extrair JSON se o modelo retornar function_call
                        try:
                            import json
                            cleaned = response_text.strip()
                            if cleaned.startswith('```json'):
                                cleaned = cleaned[len('```json'):].strip()
                            if cleaned.startswith('```'):
                                cleaned = cleaned[len('```'):].strip()
                            if cleaned.endswith('```'):
                                cleaned = cleaned[:-3].strip()
                            
                            parsed = json.loads(cleaned)
                            if isinstance(parsed, dict):
                                print(f"✅ Gemini retornou JSON refinado")
                                tech_details = {
                                    "refine_from_error": True,
                                    "original_error": error_message,
                                    "failed_sql": previous_sql,
                                    "table_name": table_name,
                                    "rag_table_score": best_table_score
                                }
                                return parsed, tech_details
                        except:
                            pass
                        
                        print(f"✅ Gemini retornou resposta de refinamento (texto)")
                        tech_details = {
                            "refine_from_error": True,
                            "original_error": error_message,
                            "failed_sql": previous_sql,
                            "table_name": table_name,
                            "rag_table_score": best_table_score
                        }
                        return {"refinement_suggestion": response_text}, tech_details
        
        print(f"⚠️  Gemini não retornou resposta válida para refinamento")
        return None, None
        
    except Exception as e:
        print(f"❌ Erro ao refinar SQL: {e}")
        return None, None

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
    df_full = None
    if data and isinstance(data, list) and len(data) > 0:
        df_full = pd.DataFrame(data)
        float_cols = df_full.select_dtypes(include=['float', 'float64', 'float32']).columns
        if len(float_cols) > 0:
            df_full[float_cols] = df_full[float_cols].round(2)
        # Para o modelo Gemini, envia só as primeiras 15 linhas + mini relatório se houver mais de 15
        if len(df_full) > 15:
            df_prompt = df_full.head(15)
            mini_report = df_full.describe(include='all').to_dict()
            data_for_prompt = df_prompt.to_dict(orient='records')
            mini_report_text = f"\nMINI RELATÓRIO DOS DADOS COMPLETOS:\n{json.dumps(mini_report, indent=2, default=str)}"
        else:
            data_for_prompt = df_full.to_dict(orient='records')
            mini_report_text = ""
        # O DataFrame completo (df_full) será usado para gráficos e downloads
    else:
        data_for_prompt = data
        mini_report_text = ""

    # Lista de colunas disponíveis para orientar o modelo
    columns_list = list(df_full.columns) if df_full is not None else (list(data[0].keys()) if data and isinstance(data, list) and isinstance(data[0], dict) else [])

    instruction = f"""
    Você é um ANALISTA SÊNIOR especializado em transformar dados em insights estratégicos.

    MISSÃO: Analisar ESPECÍFICAMENTE os dados fornecidos e responder DIRETAMENTE à pergunta do usuário.

    CONTEXTO COMPLETO:
    - PERGUNTA DO USUÁRIO: "{prompt}"
    - CONSULTA SQL EXECUTADA: {query if query else "Consulta direta"}
    - FILTROS APLICADOS: {function_params.get('where', 'Nenhum') if function_params else 'Nenhum'}

    DADOS ESPECÍFICOS PARA ANÁLISE (máx. 15 linhas):
    {json.dumps(data_for_prompt, indent=2, default=str)}
    {mini_report_text}

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
                
                # Validação do tipo de gráfico
                valid_types = ['bar', 'barra', 'line', 'linha', 'scatter', 'dispersao']
                if graph_type not in valid_types:
                    print(f"⚠️  Tipo de gráfico inválido: '{graph_type}'. Usando 'bar' como padrão.")
                    graph_type = 'bar'
                
                # Extração segura do X-AXIS
                if "X-AXIS:" in graph_part:
                    x_axis = graph_part.split("X-AXIS:")[1].split("|")[0].strip()
                    # Remove escapes indevidos (ex: mod\_ds -> mod_ds)
                    x_axis = x_axis.replace('\\_', '_').strip()
                else:
                    print("⚠️  X-AXIS não encontrado. Usando primeira coluna como X.")
                    x_axis = list(df_full.columns)[0] if len(df_full.columns) > 0 else None
                    if not x_axis:
                        return response_text, None
                    
                # Extração segura do Y-AXIS  
                if "Y-AXIS:" in graph_part:
                    y_axis = graph_part.split("Y-AXIS:")[1].split("|")[0].strip()
                    # Remove escapes indevidos (ex: total\_vendas -> total_vendas)
                    y_axis = y_axis.replace('\\_', '_').strip()
                else:
                    print("⚠️  Y-AXIS não encontrado. Usando segunda coluna como Y.")
                    y_axis = list(df_full.columns)[1] if len(df_full.columns) > 1 else None
                    if not y_axis:
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

                print(f"📊 Parâmetros do gráfico - Tipo: {graph_type}, X: {x_axis}, Y: {y_axis}, Color: {color}")
                
                # Converte dados para DataFrame
                df_data = df_full
                print(f"[DEBUG] Colunas disponíveis: {list(df_data.columns)}")
                
                # 🔥 NOVO: Auto-detecta e converte PIVOT → MELTED ANTES de extrair parâmetros
                import re
                value_cols = [col for col in df_data.columns if col != x_axis and re.match(r'.*_\d{4}', col)]
                if len(value_cols) > 1:
                    print(f"🔄 [MELT] Detectado formato PIVOT com colunas: {value_cols}")
                    print(f"   Convertendo de PIVOT para MELTED...")
                    
                    # Faz MELT
                    df_melted = df_data.melt(
                        id_vars=[x_axis],
                        value_vars=value_cols,
                        var_name='categoria',
                        value_name='valor'
                    )
                    
                    # Extrai o valor numérico da categoria (ex: "ano_2024" → "2024")
                    df_melted['categoria'] = df_melted['categoria'].str.replace(r'^.*_', '', regex=True)
                    
                    print(f"✅ [MELT] Conversão bem-sucedida!")
                    print(f"   Forma original: {df_data.shape} → Forma melted: {df_melted.shape}")
                    print(f"   Novas colunas: {list(df_melted.columns)}")
                    
                    # Usa dados MELTED
                    df_data = df_melted
                    # Atualiza Y para 'valor' (coluna do MELT)
                    y_axis = 'valor'
                    # Se não tinha color, usa 'categoria' automaticamente
                    if not color:
                        color = 'categoria'
                        print(f"✅ Auto-detectado 'categoria' como COLOR para dados MELTED")
                
                # Garante que os nomes das colunas não tenham espaços/quebras de linha
                x_axis_clean = x_axis.strip() if isinstance(x_axis, str) else x_axis
                y_axis_clean = y_axis.strip() if isinstance(y_axis, str) else y_axis
                color_axis_clean = color.strip() if isinstance(color, str) and color else None

                # Aplica fuzzy matching para encontrar colunas reais
                try:
                    x_axis_real = fuzzy_column(x_axis_clean, list(df_data.columns))
                    y_axis_real = fuzzy_column(y_axis_clean, list(df_data.columns))
                    color_real = fuzzy_column(color_axis_clean, list(df_data.columns)) if color_axis_clean else None
                except ValueError as ve:
                    print(f"❌ Erro ao mapear colunas: {ve}")
                    print(f"   X procurado: '{x_axis_clean}' → Não encontrado")
                    print(f"   Y procurado: '{y_axis_clean}' → Não encontrado")
                    return response_text, None
                
                print(f"✅ Colunas mapeadas - X: {x_axis_real}, Y: {y_axis_real}, Color: {color_real}")
                
                # Valida tipos de dados antes de gerar gráfico
                try:
                    # Verifica se as colunas existem e têm tipos válidos
                    if x_axis_real not in df_data.columns or y_axis_real not in df_data.columns:
                        print(f"❌ Colunas não encontradas no DataFrame")
                        return response_text, None
                    
                    # Verifica se Y é numérico (para gráficos)
                    if not pd.api.types.is_numeric_dtype(df_data[y_axis_real]):
                        print(f"⚠️  Coluna Y '{y_axis_real}' não é numérica. Convertendo para número.")
                        try:
                            df_data[y_axis_real] = pd.to_numeric(df_data[y_axis_real], errors='coerce')
                        except:
                            print(f"❌ Não foi possível converter coluna Y para numérico")
                            return response_text, None
                    
                    # Gera gráfico
                    fig = generate_chart(df_data, graph_type, x_axis_real, y_axis_real, color_real)
                    
                    if fig:
                        chart_info = {
                            "type": graph_type,
                            "x": x_axis,
                            "y": y_axis,
                            "color": color,
                            "fig": fig,
                        }
                        print("✅ Gráfico gerado com sucesso")
                    else:
                        print(f"❌ Falha ao gerar gráfico. Tipo: {graph_type}, X: {x_axis_real}, Y: {y_axis_real}, Color: {color_real}")
                        
                except Exception as e:
                    print(f"❌ Erro ao validar/gerar gráfico: {e}")
                    import traceback
                    traceback.print_exc()
                    chart_info = None
                    
            except Exception as e:
                print(f"❌ Erro ao processar instrução GRAPH-TYPE: {e}")
                import traceback
                traceback.print_exc()
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
                excel_bytes = generate_excel_bytes(df_full.to_dict(orient='records'))
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
    """
    Gera gráfico do TIPO EXATO que o usuário solicitou.
    ⚠️  NÃO faz fallback - se o tipo for inválido, retorna None.
    ⚠️  SEMPRE prioriza o tipo solicitado.
    """
    import re
    
    def clean_alias(alias):
        """Remove caracteres especiais para matching de colunas"""
        return re.sub(r'[^a-zA-Z0-9_]', '', alias.strip().lower().replace(' ', '_'))

    def get_real_column(alias, columns):
        """Encontra coluna real no DataFrame por alias fuzzy"""
        alias_norm = clean_alias(alias)
        for col in columns:
            col_norm = clean_alias(col)
            if col_norm == alias_norm:
                return col
        raise ValueError(f"Coluna '{alias}' não encontrada em: {list(columns)}")

    # Normaliza tipo de gráfico solicitado
    chart_type_norm = chart_type.lower().strip()
    print(f"📊 [GRAFICO] Tipo solicitado: '{chart_type}' → Normalizado: '{chart_type_norm}'")
    
    # Valida tipo - se for inválido, retorna None (NÃO faz fallback!)
    valid_types = {
        'bar': ['bar', 'barra', 'barras', 'coluna', 'colunas'],
        'line': ['line', 'linha', 'linhas', 'curva', 'tendencia'],
        'scatter': ['scatter', 'dispersao', 'dispersão', 'pontos', 'ponto']
    }
    
    chart_type_final = None
    for key, aliases in valid_types.items():
        if chart_type_norm in aliases:
            chart_type_final = key
            break
    
    if not chart_type_final:
        # Tipo inválido - NÃO faz fallback, retorna erro
        print(f"❌ [GRAFICO] Tipo '{chart_type}' NÃO SUPORTADO")
        print(f"   Tipos válidos: {list(valid_types.keys())}")
        return None
    
    print(f"✅ [GRAFICO] Tipo validado como: '{chart_type_final}'")

    # Valida e obtém colunas reais
    try:
        x_axis_real = get_real_column(x_axis, data.columns)
        y_axis_real = get_real_column(y_axis, data.columns)
        print(f"✅ [GRAFICO] Colunas validadas - X: {x_axis_real}, Y: {y_axis_real}")
    except ValueError as e:
        print(f"❌ [GRAFICO] Erro de coluna: {e}")
        return None

    # Valida coluna de cor (opcional)
    color_real = None
    if color:
        try:
            color_real = get_real_column(color, data.columns)
            print(f"✅ [GRAFICO] Coluna de cor validada: {color_real}")
        except ValueError as e:
            print(f"⚠️  [GRAFICO] Coluna de cor '{color}' não encontrada - gerando sem cor")
            color_real = None

    if data.empty:
        print(f"❌ [GRAFICO] DataFrame vazio")
        return None

    import streamlit as st

    # Detecta tema
    theme_mode = st.session_state.get('theme_mode', 'escuro')
    is_dark_theme = theme_mode == 'escuro'

    # Cores adaptativas
    if is_dark_theme:
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
        color_palette = [
            '#2563eb', '#059669', '#d97706', '#dc2626', '#7c3aed',
            '#0891b2', '#065f46', '#ea580c', '#be185d', '#4338ca'
        ]
        bg_color = 'rgba(255,255,255,0)'
        text_color = '#374151'
        grid_color = 'rgba(0,0,0,0.1)'
        legend_bg = 'rgba(255, 255, 255, 0.95)'
        legend_border = 'rgba(0,0,0,0.1)'

    layout_config = {
        'plot_bgcolor': bg_color,
        'paper_bgcolor': bg_color,
        'font': {'color': text_color, 'size': 14, 'family': 'Arial, sans-serif'},
        'margin': {'l': 20, 'r': 20, 't': 40, 'b': 80},
        'showlegend': True,
        'autosize': True,
        'height': 480,
        'legend': {
            'orientation': 'h',
            'yanchor': 'bottom',
            'y': -1.2,
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
        print(f"🔨 [GRAFICO] Gerando gráfico do tipo: {chart_type_final}")
        
        # Gera gráfico do TIPO EXATO solicitado
        if chart_type_final == 'line':
            fig = px.line(
                data, x=x_axis_real, y=y_axis_real, color=color_real,
                color_discrete_sequence=color_palette,
                line_shape='spline',
                title=f"Gráfico de Linha: {y_axis_real} por {x_axis_real}"
            )
            fig.update_traces(line=dict(width=3))
            print(f"✅ [GRAFICO] Linha gerada com sucesso")

        elif chart_type_final == 'bar':
            fig = px.bar(
                data, x=x_axis_real, y=y_axis_real, color=color_real,
                color_discrete_sequence=color_palette,
                title=f"Gráfico de Barras: {y_axis_real} por {x_axis_real}"
            )
            print(f"✅ [GRAFICO] Barras geradas com sucesso")

        elif chart_type_final == 'scatter':
            fig = px.scatter(
                data, x=x_axis_real, y=y_axis_real, color=color_real,
                color_discrete_sequence=color_palette,
                size_max=15,
                title=f"Gráfico de Dispersão: {y_axis_real} vs {x_axis_real}"
            )
            print(f"✅ [GRAFICO] Dispersão gerada com sucesso")

        # Aplica layout
        fig.update_layout(layout_config)
        fig.update_xaxes(
            showgrid=True, gridwidth=1, gridcolor=grid_color,
            showline=True, linewidth=1, linecolor=grid_color
        )
        fig.update_yaxes(
            showgrid=True, gridwidth=1, gridcolor=grid_color,
            showline=True, linewidth=1, linecolor=grid_color
        )

        print(f"✅ [GRAFICO] Gráfico '{chart_type_final}' finalizado com sucesso")
        return fig
        
    except Exception as e:
        print(f"❌ [GRAFICO] Erro ao gerar gráfico do tipo '{chart_type_final}': {e}")
        import traceback
        traceback.print_exc()
        return None