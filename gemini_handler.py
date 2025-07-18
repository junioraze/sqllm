import google.generativeai as genai
from google.generativeai.types import Tool, FunctionDeclaration
from config import MODEL_NAME, SYSTEM_INSTRUCTION, TABLES_CONFIG, PROJECT_ID, DATASET_ID
import re
import json
import pandas as pd
import plotly.express as px
from utils import create_styled_download_button, generate_excel_bytes, generate_csv_bytes
from datetime import datetime

def initialize_model():
    """
    Inicializa o modelo Gemini com instruções dinâmicas baseadas nas tabelas configuradas
    """
    
    # Constrói a descrição dinamicamente baseada nas tabelas disponíveis com full_table_id
    tables_description = "Consulta dados no BigQuery. Tabelas disponíveis:\n"
    full_table_mapping = {}
    
    for table_name, config in TABLES_CONFIG.items():
        full_table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
        full_table_mapping[full_table_id] = table_name
        tables_description += f"- {full_table_id}: {config['description']}\n"
    
    tables_description += (
        "\nREGRAS ABSOLUTAS:\n"
        "1. 🚨 QUALIFY - REGRAS CRÍTICAS:\n"
        "   - Para TOP N GERAL (ex: 'top 20 modelos'): NUNCA use PARTITION BY, use apenas ORDER BY\n"
        "   - Para TOP N POR GRUPO (ex: 'top 3 modelos por estado'): use PARTITION BY com o campo do grupo\n"
        "   - PARTITION BY só funciona com campos que estão no GROUP BY\n"
        "   - NUNCA use PARTITION BY com campos que já estão filtrados no WHERE\n"
        "2. NUNCA use LIMIT para consultas agrupadas - sempre use QUALIFY\n"
        "3. Para múltiplas dimensões inclua TODOS os campos do PARTITION BY no SELECT\n"
        "4. Campos no GROUP BY DEVEM estar no SELECT\n"
        "5. SEMPRE use a tabela correta baseada na pergunta do usuário\n"
        "6. 🔴 GRÁFICOS TEMPORAIS - REGRA CRÍTICA:\n"
        "   Para análises temporais (vendas por mês/ano, evolução temporal), SEMPRE crie uma coluna de data contínua:\n"
        "   - NUNCA use EXTRACT(MONTH FROM data) - quebra continuidade temporal\n"
        "   - USE: CONCAT(EXTRACT(YEAR FROM data), '-', LPAD(EXTRACT(MONTH FROM data), 2, '0')) AS periodo_mes\n"
        "   - OU: FORMAT_DATE('%Y-%m', data) AS periodo_mes\n"
        "   - OU: FORMAT_DATE('%Y-%m-%d', data) AS periodo_dia (para dados diários)\n"
        "   - OU: EXTRACT(YEAR FROM data) AS ano (apenas para dados anuais)\n"
        "   Isso garante visualização correta em gráficos de linha temporal!\n\n"
        "Exemplo CORRETO para top 20 modelos (SEM PARTITION BY):\n"
        "{\n"
        f'  "full_table_id": "{PROJECT_ID}.{DATASET_ID}.drvy_VeiculosVendas",\n'
        '  "select": ["modelo", "SUM(QTE) AS total_vendas"],\n'
        '  "where": "EXTRACT(YEAR FROM dta_venda) = 2024",\n'
        '  "group_by": ["modelo"],\n'
        '  "order_by": ["total_vendas DESC"],\n'
        '  "qualify": "ROW_NUMBER() OVER (ORDER BY total_vendas DESC) <= 20"\n'
        "}\n\n"
        "Exemplo CORRETO para top 3 modelos por estado (COM PARTITION BY):\n"
        "{\n"
        f'  "full_table_id": "{PROJECT_ID}.{DATASET_ID}.drvy_VeiculosVendas",\n'
        '  "select": ["modelo", "uf", "SUM(QTE) AS total"],\n'
        '  "where": "EXTRACT(YEAR FROM dta_venda) = 2024",\n'
        '  "group_by": ["modelo", "uf"],\n'
        '  "order_by": ["uf", "total DESC"],\n'
        '  "qualify": "ROW_NUMBER() OVER (PARTITION BY uf ORDER BY total DESC) <= 3"\n'
        "}\n\n"
        "Exemplo CORRETO para vendas mensais (gráfico temporal):\n"
        "{\n"
        f'  "full_table_id": "{PROJECT_ID}.{DATASET_ID}.drvy_VeiculosVendas",\n'
        '  "select": ["FORMAT_DATE(\'%Y-%m\', dta_venda) AS periodo_mes", "SUM(QTE) AS total_vendas"],\n'
        '  "where": "EXTRACT(YEAR FROM dta_venda) = 2024",\n'
        '  "group_by": ["FORMAT_DATE(\'%Y-%m\', dta_venda)"],\n'
        '  "order_by": ["periodo_mes"]\n'
        "}"
    )
    
    query_func = FunctionDeclaration(
        name="query_business_data",
        description=tables_description,
        parameters={
            "type": "object",
            "properties": {
                "full_table_id": {
                    "type": "string",
                    "description": f"ID completo da tabela no BigQuery (PROJECT.DATASET.TABLE). Opções: {', '.join(full_table_mapping.keys())}",
                    "enum": list(full_table_mapping.keys())
                },
                "select": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Campos para SELECT (DEVE incluir todos do PARTITION BY)",
                },
                "where": {
                    "type": "string",
                    "description": "Condições WHERE (SQL puro)",
                },
                "group_by": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Campos para GROUP BY (DEVEM estar no SELECT)",
                },
                "order_by": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Campos para ORDER BY",
                },
                "qualify": {
                    "type": "string",
                    "description": "Para TOP N: ROW_NUMBER() OVER (ORDER BY...) <= N (SEM partition) OU ROW_NUMBER() OVER (PARTITION BY campo_grupo ORDER BY...) <= N (COM partition apenas para grupos diferentes)",
                },
                "limit": {
                    "type": "integer",
                    "description": "USO PROIBIDO para consultas agrupadas - apenas para consultas simples",
                },
            },
            "required": ["full_table_id", "select"],
        },
    )

    business_tool = Tool(function_declarations=[query_func])

    generation_config = {
        "temperature": 0.5,
        "max_output_tokens": 2000,
    }

    return genai.GenerativeModel(
        MODEL_NAME,
        tools=[business_tool],
        system_instruction=SYSTEM_INSTRUCTION,
        generation_config=generation_config,
    )


def generate_chart(data, chart_type, x_axis, y_axis, color=None):
    """Gera gráfico com tratamento para múltiplas dimensões"""
    if not data or not x_axis or not y_axis:
        return None

    try:
        df = pd.DataFrame.from_records(data)

        # Verificação de colunas com tratamento para múltiplas dimensões
        required_columns = {x_axis, y_axis}
        if color:  # Terceira dimensão
            required_columns.add(color)
            if color not in df.columns:
                color = None  # Degrada para 2D

        # Conversão segura de tipos para eixos
        df[y_axis] = pd.to_numeric(df[y_axis], errors="coerce")

        # Paleta de cores para múltiplas categorias
        palette = px.colors.qualitative.Plotly

        if chart_type == "bar":
            fig = px.bar(
                df,
                x=x_axis,
                y=y_axis,
                color=color,
                barmode="group",  # Essencial para múltiplas dimensões
                color_discrete_sequence=palette,
            )
        elif chart_type == "line":
            fig = px.line(
                df,
                x=x_axis,
                y=y_axis,
                color=color,
                markers=True,
                color_discrete_sequence=palette,
            )
        else:
            return None

        fig.update_layout(hovermode="x unified", plot_bgcolor="rgba(0,0,0,0)")
        return fig

    except Exception as e:
        print(f"Erro ao gerar gráfico (multi-dimensão): {str(e)}")
        return None


def refine_with_gemini(
    prompt: str, data: list, function_params: dict = None, query: str = None
):
    """
    Envia os dados para o Gemini fazer o refinamento e retorna a resposta e detalhes técnicos.
    """
    if function_params is not None:
        if hasattr(function_params, "_values"):
            function_params = {k: v for k, v in function_params.items()}
        elif not isinstance(function_params, dict):
            function_params = dict(function_params)

    instruction = f"""
    Você é um analista de dados especializado. Sua tarefa é:
    1. Analisar os dados fornecidos (em JSON abaixo) + a pergunta do usuário e gerar uma resposta completa e contextualizada.
    2. Responder à pergunta do usuário de forma completa.
    3. Formatar a resposta com:
       - Introdução contextual
       - Principais insights
       - Dados em formato tabular (quando aplicável)
       - Só gere gráficos se e somente se for solicitado a gerar (usando formato GRAPH-TYPE)
       - Só gere arquivos excel/xlsx ou csv se o usuário solicitar explicitamente (usando palavras como exportar, baixar, excel, planilha, csv).
       - Atenção à formatação para evitar erros de markdown.

    🔴 IMPORTANTE: Os dados fornecidos foram FILTRADOS e PROCESSADOS pelo BigQuery conforme a consulta SQL executada.
    Se a consulta SQL contém filtros (WHERE), os dados JÁ ESTÃO filtrados por esses critérios.
    
    CONSULTA SQL EXECUTADA: {query if query else "Consulta não disponível"}
    FILTROS APLICADOS: {function_params.get('where', 'Nenhum filtro') if function_params else 'Não disponível'}

    Os dados fornecidos são FINAIS e COMPLETOS para a pergunta feita. NÃO diga que faltam informações 
    se a consulta SQL já aplicou os filtros necessários.

    PERGUNTA DO USUÁRIO: "{prompt}"

    DADOS PARA ANÁLISE:
    {json.dumps(data, indent=2, default=str)}

    FORMATO ESPERADO DA RESPOSTA:
    [Contexto e introdução]

    [Análise dos principais resultados]

    [Tabela ou resumo dos dados quando relevante]

    [Sugestão de gráfico se aplicável, no formato:]
    GRAPH-TYPE: [tipo] | X-AXIS: [coluna] | Y-AXIS: [coluna] | COLOR: [coluna]
    - O tipo pode ser "bar" ou "line", nunca gere "pie". 
    - COLOR é opcional e deve ser usado para representar a terceira dimensão.
    - As colunas devem existir nos dados fornecidos.

    [Exportação de dados se solicitado, no formato:]
    EXPORT-INFO: FORMATO: [excel/csv] 
    - Aqui você só precisa fornecer essa linha de EXPORT-INFO, não fornecer nenhuma informação a mais sobre o arquivo.
    
    ATENÇÃO: 
    Só gere visualização gráfica se o usuário solicitar explicitamente um gráfico, visualização, plot, curva, barra, linha ou termos semelhantes.
   - Nunca gere gráfico por padrão, nem sugira gráfico se não for solicitado.
        Exemplo: 
        Usuário: "Quais as vendas das lojas de limoeiro em janeiro/2025?"
        Resposta: [NÃO incluir gráfico]
        Usuário: "Me mostre um gráfico das vendas das lojas de limoeiro em janeiro/2025"
        Resposta: [Incluir gráfico conforme instrução]
        
    Se o usuário solicitar exportação, gere links para download dos dados em Excel e CSV. 
    - Nunca gere se não houver dados ou se não for explicitamente solicitado.
    """

    model = genai.GenerativeModel(MODEL_NAME)
    response = model.generate_content(instruction)
    response_text = response.text
    chart_info = None

    # Extrai instrução de gráfico, se houver
    if "GRAPH-TYPE:" in response_text:
        try:
            graph_part = response_text.split("GRAPH-TYPE:")[1].strip()
            graph_type = graph_part.split("|")[0].strip()
            x_axis = graph_part.split("X-AXIS:")[1].split("|")[0].strip()
            y_axis = graph_part.split("Y-AXIS:")[1].split("|")[0].strip()
            color = None
            if "COLOR:" in graph_part:
                color = graph_part.split("COLOR:")[1].strip()

            fig = generate_chart(data, graph_type, x_axis, y_axis, color)
            #print("DEBUG generate_chart:", fig)
            if fig:
                chart_info = {
                    "type": graph_type,
                    "x": x_axis,
                    "y": y_axis,
                    "color": color,
                    "fig": fig,
                }

            else:
                print(
                    "DEBUG gráfico não gerado. Dados:",
                    data,
                    "Tipo:",
                    graph_type,
                    "X:",
                    x_axis,
                    "Y:",
                    y_axis,
                    "Color:",
                    color,
                )
                response_text = response_text.split("GRAPH-TYPE:")[0].strip()
        except Exception as e:
            print(f"Erro ao processar instrução de gráfico: {e}")

    # Verificar se o usuário solicitou exportação
    export_requested = any(keyword in prompt.lower() for keyword in 
                          ['exportar', 'excel', 'planilha', 'csv', 'baixar']) or "EXPORT:" in response_text
    
    # Gerar links de exportação se solicitado
    export_links = []
    export_info = {}
    
    if export_requested:
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

    tech_details = {
        "function_params": function_params,
        "query": query,
        "raw_data": data,
        "chart_info": {
            "type": chart_info["type"],
            "x": chart_info["x"],
            "y": chart_info["y"],
            "color": chart_info["color"],
            # "fig" removido para evitar erro de serialização no cache
        } if chart_info else None,
        "export_links": export_links,
        "export_info": export_info,
    }
    
    # Adicionar figura de volta ao chart_info para retorno (uso imediato)
    if chart_info:
        tech_details["chart_info"]["fig"] = chart_info["fig"]
    
    #response_text = re.sub(r"GRAPH-TYPE:.*", "", response_text).strip()
    return response_text, tech_details


def should_reuse_data(model, current_prompt: str, user_history: list = None) -> dict:
    """
    Pergunta ao Gemini se deve reutilizar os dados das últimas consultas
    considerando o histórico do usuário
    Retorna um dict com 'should_reuse': bool e 'reason': str
    """
    if not user_history:
        return {"should_reuse": False, "reason": "Nenhum histórico disponível"}
    
    # Constrói contexto do histórico recente
    history_items = []
    for interaction in user_history:
        data_summary = f" ({interaction.get('raw_data_count', 0)} registros)" if interaction.get('raw_data_count', 0) > 0 else ""
        interaction_id = interaction.get('id', 'N/A')
        history_items.append(f"- ID: {interaction_id} | {interaction.get('user_prompt', 'N/A')}{data_summary}")
    
    if not history_items:
        return {"should_reuse": False, "reason": "Histórico vazio"}
        
    history_context = f"\nHISTÓRICO RECENTE (com IDs para referência):\n" + "\n".join(history_items) + "\n"
    
    context_prompt = f"""
🚨 VALIDADOR INTELIGENTE DE REUTILIZAÇÃO DE DADOS 🚨

MISSÃO: Analisar o histórico e determinar se alguma consulta anterior pode responder à nova pergunta.

NOVA PERGUNTA: "{current_prompt}"

{history_context}

🧠 ANÁLISE INTELIGENTE - Examine o histórico e responda:

1. **COMPATIBILIDADE**: A nova pergunta é sobre o MESMO ASSUNTO da consulta anterior?
   - Ex: Nova pergunta sobre "tempo médio" vs histórico sobre "montante de compras" → INCOMPATÍVEL → NOVA CONSULTA

2. **QUANTIDADE**: Se a nova pergunta solicita mais registros do que qualquer consulta anterior retornou, é NOVA CONSULTA.
   - Ex: Histórico mostra "5 registros" mas nova pergunta pede "20 modelos" → NOVA CONSULTA
   - Ex: Histórico mostra "100 registros" mas nova pergunta pede "10 primeiros" → PODE REUTILIZAR

3. **ESCOPO**: Se a nova pergunta muda filtros, período, ou critérios, é NOVA CONSULTA.
   - Ex: Histórico de "todos estados" mas nova pergunta pede "só SP" → NOVA CONSULTA
   - Ex: Histórico de "2023" mas nova pergunta pede "2024" → NOVA CONSULTA

4. **TIPO DE ANÁLISE**: Se a nova pergunta pede cálculos/análises diferentes dos já feitos, é NOVA CONSULTA.
   - Ex: Histórico tem lista simples mas nova pergunta pede "total por categoria" → NOVA CONSULTA
   - Ex: Histórico tem valores mas nova pergunta pede "tempo médio" → NOVA CONSULTA

5. **VISUALIZAÇÃO/EXPORT**: Se a nova pergunta só quer apresentar os mesmos dados de forma diferente, PODE REUTILIZAR.
   - Ex: "fazer gráfico", "exportar excel", "mostrar tabela" dos mesmos dados → REUTILIZAR

🎯 DECISÃO:
- Se a nova pergunta é sobre ASSUNTO DIFERENTE ou pede ANÁLISE DIFERENTE → NOVA CONSULTA
- Encontrou consulta anterior que responde à nova pergunta com dados suficientes? → REUTILIZAR (informe o ID)
- Nova pergunta precisa de dados diferentes/mais dados? → NOVA CONSULTA

Responda APENAS:
{{"should_reuse": false, "reason": "nova pergunta sobre assunto/análise diferente"}}
OU
{{"should_reuse": true, "reason": "consulta anterior contém dados suficientes", "interaction_id": "ID_da_consulta"}}
"""

    try:
        # Usa um modelo simples só para avaliação, sem tools
        evaluation_model = genai.GenerativeModel(
            MODEL_NAME,
            generation_config={"temperature": 0.3, "max_output_tokens": 150}
        )
        
        response = evaluation_model.generate_content(context_prompt)
        response_text = response.text.strip()
        
        # Tenta extrair JSON da resposta
        if "{" in response_text and "}" in response_text:
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            json_str = response_text[json_start:json_end]
            result = json.loads(json_str)
            return result
        else:
            return {"should_reuse": False, "reason": "Resposta inválida do modelo"}
            
    except Exception as e:
        print(f"Erro na avaliação de reutilização: {str(e)}")
        # Em caso de erro, não reutiliza por segurança
        return {"should_reuse": False, "reason": f"Erro na avaliação: {str(e)}"}
