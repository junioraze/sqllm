# gemini_handler.py
import google.generativeai as genai
from google.generativeai.types import Tool, FunctionDeclaration
from config import MODEL_NAME, SYSTEM_INSTRUCTION
import json, io, base64
import add_instructions
import pandas as pd
import matplotlib.pyplot as plt

def generate_chart(data: list, chart_type: str, x_axis: str, y_axis: str) -> str:
    """Gera um gráfico baseado nos dados e retorna como base64."""
    try:
        df = pd.DataFrame(data)
        
        plt.figure(figsize=(10, 6))
        
        if chart_type == "bar":
            df.plot.bar(x=x_axis, y=y_axis, legend=False)
        elif chart_type == "line":
            df.plot.line(x=x_axis, y=y_axis, marker='o', legend=False)
        elif chart_type == "pie":
            df.plot.pie(y=y_axis, labels=df[x_axis], autopct='%1.1f%%', legend=False)
        else:
            return None
            
        plt.tight_layout()
        
        # Converte para base64
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        plt.close()
        
        return f"data:image/png;base64,{img_str}"
    except Exception as e:
        print(f"Erro ao gerar gráfico: {e}")
        return None


def initialize_model():
    """Inicializa o modelo Gemini com configurações mais flexíveis."""
    veiculos_vendas_func = FunctionDeclaration(
        name="query_vehicle_sales",
        description="""Consulta vendas de veículos. 
    DETALHES TECNICOS:
    - As consultas são realizadas no banco BigQuery da Google Cloud
    - Todas as sintaxes de funções devem levar em condsideração as regras do BigQuery (STANRDARD SQL)

                
    REGRAS ESTRITAS:
    1. GROUP BY: 
       - Deve conter APENAS nomes de colunas SEM funções de agregação
       - Exemplo válido: ["uf", "modelo"]
       - Exemplo inválido: ["SUM(val_total)"]
    2. ORDER BY: 
        - Deve conter APENAS nomes de colunas SEM funções de agregação
       - Exemplo válido: ["uf asc", "modelo desc"]
       - Exemplo inválido: ["SUM(val_total) desc", "COUNT(modelo) asc"]
    3. LIMIT: 
       - Sempre um número inteiro (ex: 10)
       - Exemplo válido: ["10"]
       - Exemplo inválido: ["10.0"]
    4. WHERE: 
       - Condições em SQL puro (ex: "dta_venda BETWEEN '2025-01-01' AND '2025-12-31'")""",
        parameters={
            "type": "object",
            "properties": {
                "query_type": {
                    "type": "string",
                    "description": "Tipo de consulta (aggregation, comparison, raw_data)",
                    "enum": ["aggregation", "comparison", "raw_data"]
                },
                "select": {
                    "type": "array",
                    "description": "Campos a selecionar ou funções de agregação",
                    "items": {
                        "type": "string"
                    }
                },
                "where": {
                    "type": "string",
                    "description": "Condições WHERE em SQL puro"
                },
                "group_by": {
                    "type": "array",
                    "description": "Campos para agrupamento",
                    "items": {
                        "type": "string"
                    }
                },
                "order_by": {
                    "type": "array",
                    "description": "Campos para ordenação",
                    "items": {
                        "type": "string"
                    }
                },
                "limit": {
                    "type": "integer",
                    "description": "Limite de registros"
                }
            },
            "required": ["select"]
        },
    )
    
    veiculos_tool = Tool(function_declarations=[veiculos_vendas_func])
    
    return genai.GenerativeModel(
        MODEL_NAME,
        tools=[veiculos_tool],
        system_instruction=SYSTEM_INSTRUCTION
    )

def refine_with_gemini(prompt: str, data: list, function_params: dict = None, query: str = None):
    """Envia os dados para o Gemini fazer o refinamento."""
    if function_params is not None:
        if hasattr(function_params, '_values'):
            function_params = {k: v for k, v in function_params.items()}
        elif not isinstance(function_params, dict):
            function_params = dict(function_params)
    
    instruction = f"""
    Você é um analista de dados especializado. Sua tarefa é:
    1. Analisar os dados fornecidos (em JSON abaixo) + a pergunta do usuário
       e gerar uma resposta completa e contextualizada.
    2. Responder à pergunta do usuário de forma completa
    3. Formatar a resposta com:
       - Introdução contextual
       - Principais insights
       - Dados em formato tabular (quando aplicável)
       - Gráfico se solicitado (usando formato GRAPH-TYPE)
       - se atentar as formatações para evitar erros de markdown. 
    
    PERGUNTA DO USUÁRIO: "{prompt}"
    
    DADOS PARA ANÁLISE:
    {json.dumps(data, indent=2, default=str)}
    
    FORMATO ESPERADO DA RESPOSTA:
    [Contexto e introdução]
    
    [Análise dos principais resultados]
    
    [Tabela ou resumo dos dados quando relevante]
    
    [Sugestão de gráfico se aplicável, no formato:]
    GRAPH-TYPE: [tipo] | X-AXIS: [coluna] | Y-AXIS: [coluna]
    """
    
    model = genai.GenerativeModel(MODEL_NAME)
    response = model.generate_content(instruction)
    
    # Processar a resposta para extrair informações do gráfico
    response_text = response.text
    chart_info = None
    
    # Verificar se há instruções de gráfico na resposta
    if "GRAPH-TYPE:" in response_text:
        try:
            graph_part = response_text.split("GRAPH-TYPE:")[1].strip()
            graph_type = graph_part.split("|")[0].strip()
            x_axis = graph_part.split("X-AXIS:")[1].split("|")[0].strip()
            y_axis = graph_part.split("Y-AXIS:")[1].strip()
            
            # Gerar o gráfico
            img_base64 = generate_chart(data, graph_type, x_axis, y_axis)
            
            if img_base64:
                chart_info = {
                    "type": graph_type,
                    "x": x_axis,
                    "y": y_axis,
                    "img": img_base64
                }
                
                # Remover a linha de instrução do gráfico da resposta
                response_text = response_text.split("GRAPH-TYPE:")[0].strip()
        except Exception as e:
            print(f"Erro ao processar instrução de gráfico: {e}")
    
    tech_details = {
        "function_params": function_params,
        "query": query,
        "raw_data": data,
        "chart_info": chart_info
    }
    
    return response_text, tech_details