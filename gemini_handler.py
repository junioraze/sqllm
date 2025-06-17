import google.generativeai as genai
from google.generativeai.types import Tool, FunctionDeclaration
from config import MODEL_NAME, SYSTEM_INSTRUCTION
import json
import add_instructions

def initialize_model():
    """Inicializa o modelo Gemini com as configurações necessárias."""
    veiculos_vendas_func = FunctionDeclaration(
        name="consultar_vendas_veiculos",
        description=f"Consulta a tabela {add_instructions.CAMPOS_DESCRICAO} para obter dados brutos.",
        parameters={
            "type": "object",
            "properties": {
                "tipo_insight": {"type": "string", "enum": ["total", "por modelo", "por UF", "por revenda", "por período", "quantidade", "multidimensional", "comparacao"]},
                "periodo": {"type": "string"},
                "periodo_comparacao": {"type": "string"},
                "modelo": {"type": "string"},
                "uf": {"type": "string"},
                "revenda": {"type": "string"},
                "agrupar_por": {"type": "array", "items": {"type": "string"}},
                "nivel_agregacao_temporal": {"type": "string", "enum": ["ano", "mes"]}
            },
            "required": ["tipo_insight"],
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
    # Converte os dados para string para evitar problemas de serialização
    data_str = json.dumps(data, indent=2, default=str)
    params_str = json.dumps(function_params, indent=2, default=str) if function_params else "Nenhum"
    
    instruction = f"""
    INSTRUÇÕES ESTRITAS:
    1. Trabalhe APENAS com os dados fornecidos
    2. Não solicite novas consultas
    3. Se os dados não forem suficientes, explique isso claramente
    4. Faça todos os cálculos necessários seguindo estas regras:
    {add_instructions.COMPARACAO_INSTRUCOES}
    
    Dados disponíveis:
    {data_str}
    
    Parâmetros usados na consulta: 
    {params_str}
    
    Responda à seguinte pergunta:
    "{prompt}"
    
    Inclua análises e cálculos conforme necessário, seguindo as instruções de comparação fornecidas.
    """
    
    model = genai.GenerativeModel(
        MODEL_NAME,
        system_instruction="Você é um analista de dados especializado em processar e interpretar resultados de consultas."
    )
    
    response = model.generate_content(instruction)
    
    # Prepara os detalhes técnicos para o spoiler
    tech_details = {
        "function_params": function_params,
        "query": query,
        "raw_data": data
    }
    
    return response.text, tech_details