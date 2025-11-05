import os
import json
from dotenv import load_dotenv

load_dotenv(".env")

# Variáveis globais carregadas do .env
PROJECT_ID = os.getenv("PROJECT_ID", "")
DATASET_ID = os.getenv("DATASET_ID", "")
MODEL_NAME = os.getenv("MODEL_NAME", "")
MAX_RATE_LIMIT = os.getenv("MAX_REQUEST_DAY", "")
DATASET_LOG_ID = os.getenv("DATASET_LOG_ID", "")
CLIENTE_NAME = os.getenv("CLIENTE_NAME", "")

def is_empresarial_mode():
    """Verifica se está no modo empresarial"""
    return os.getenv("EMPRESARIAL", "False").lower() == "true"

def load_tables_config():
    """Carrega a configuração das tabelas do arquivo JSON"""
    # Procurar em várias localizações possíveis
    possible_paths = [
        os.path.join(os.path.dirname(__file__), "tables_config.json"),  # config/tables_config.json
        os.path.join(os.path.dirname(__file__), "..", "tables_config.json"),  # raiz/tables_config.json (compatibilidade)
        "tables_config.json",  # raiz (compatibilidade)
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                print(f"Erro ao decodificar {path}: {e}")
                continue
    
    print("Arquivo tables_config.json não encontrado em nenhuma localização")
    return {}

def load_client_config():
    """Carrega a configuração específica do cliente do arquivo JSON"""
    # Procurar em várias localizações possíveis
    possible_paths = [
        os.path.join(os.path.dirname(__file__), "client_config.json"),  # config/client_config.json
        os.path.join(os.path.dirname(__file__), "..", "client_config.json"),  # raiz/client_config.json (compatibilidade)
        "client_config.json",  # raiz (compatibilidade)
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                print(f"Erro ao decodificar {path}: {e}")
                continue
    
    print("Arquivo client_config.json não encontrado, usando configuração padrão")
    return {
        "app_title": "Sistema de Análise de Dados",
        "app_subtitle": "Assistente de IA para análise de dados",
        "business_domain": "dados",
        "data_source": "tabelas configuradas",
        "rate_limit_description": "requisições",
        "examples": ["- Exemplo de pergunta"],
        "limitations": {
            "data_access": "Este assistente só pode consultar as tabelas configuradas no sistema.",
            "cross_reference": "Não é possível acessar ou cruzar dados de outras tabelas ou fontes externas.",
            "single_query": "Apenas uma consulta por vez é permitida.",
            "temporal_comparisons": "Para comparações temporais, utilize perguntas claras.",
            "model_understanding": "O modelo pode não compreender perguntas muito vagas.",
            "data_freshness": "Resultados são baseados nos dados mais recentes disponíveis."
        },
        "error_message": "Não foi possível processar sua solicitação no momento. Nossa equipe técnica foi notificada e está analisando a situação. Tente reformular sua pergunta ou entre em contato conosco."
    }

TABLES_CONFIG = load_tables_config()
CLIENT_CONFIG = load_client_config()

# Mensagem padrão para erros (nunca mostrar detalhes técnicos ao usuário)
STANDARD_ERROR_MESSAGE = CLIENT_CONFIG.get("error_message", "Não foi possível processar sua solicitação no momento. Nossa equipe técnica foi notificada e está analisando a situação. Tente reformular sua pergunta ou entre em contato conosco.")

