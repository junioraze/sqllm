# gemini_handler.py
import google.generativeai as genai
from google.generativeai.types import Tool, FunctionDeclaration
from config import MODEL_NAME, SYSTEM_INSTRUCTION
import json
import add_instructions

def initialize_model():
    """Inicializa o modelo Gemini com configurações mais flexíveis."""
    veiculos_vendas_func = FunctionDeclaration(
        name="query_vehicle_sales",
        description="""Consulta vendas de veículos. 
    DETALHES TECNICOS:
    - As consultas são realizadas no banco BigQuery da Google Cloud
    - Todas as sintaxes de funções devem levar em condsideração as regras do BigQuery (STANRDARD SQL)
    - Exemplo de consulta válida:
    - EXEMPLO INVALIDO:
                    SELECT STRFTIME("%Y-%m", dta_venda) AS mes, AVG(QTE) AS media_vendas_dia
                    FROM `glinhares.delivery.drvy_VeiculosVendas`
                    WHERE dta_venda BETWEEN "2025-01-01" AND "2025-12-31"
                    GROUP BY mes
                    ORDER BY mes
    - EXEMPLO VALIDO:
                    SELECT EXTRACT(MONTH FROM dta_venda) AS mes, AVG(QTE) AS media_vendas_dia
                    FROM `glinhares.delivery.drvy_VeiculosVendas`   
                    WHERE dta_venda BETWEEN "2025-01-01" AND "2025-12-31"
                    GROUP BY mes
                    ORDER BY mes
                
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
    INSTRUÇÕES:
    1. Analise os dados fornecidos e responda à pergunta do usuário
    2. Os dados já estão filtrados conforme a consulta SQL
    3. Se necessário, calcule métricas adicionais com base nos dados brutos
    4. Formate a resposta de forma clara e analítica
    
    DADOS DISPONÍVEIS:
    {json.dumps(data, indent=2, default=str)}
    
    PERGUNTA DO USUÁRIO:
    "{prompt}"
    """
    
    model = genai.GenerativeModel(MODEL_NAME)
    response = model.generate_content(instruction)
    
    tech_details = {
        "function_params": function_params,
        "query": query,
        "raw_data": data
    }
    
    return response.text, tech_details