import os
import json
from dotenv import load_dotenv

load_dotenv(".env")

def load_tables_config():
    """Carrega a configuração das tabelas do arquivo JSON"""
    try:
        with open("tables_config.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("Arquivo tables_config.json não encontrado")
        return {}
    except json.JSONDecodeError as e:
        print(f"Erro ao decodificar tables_config.json: {e}")
        return {}

def load_client_config():
    """Carrega a configuração específica do cliente do arquivo JSON"""
    try:
        with open("client_config.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
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
            }
        }
    except json.JSONDecodeError as e:
        print(f"Erro ao decodificar client_config.json: {e}")
        return {}

TABLES_CONFIG = load_tables_config()
CLIENT_CONFIG = load_client_config()

# Projeto e dataset
PROJECT_ID = os.getenv("PROJECT_ID")
DATASET_ID = os.getenv("DATASET_ID")
DATASET_LOG_ID = os.getenv("DATASET_LOG_ID")
MODEL_NAME = os.getenv("MODEL_NAME")
CLIENTE_NAME = os.getenv("CLIENTE_NAME")
MAX_RATE_LIMIT = int(os.getenv("MAX_REQUEST_DAY"))

# Autenticação
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv(
    "GOOGLE_APPLICATION_CREDENTIALS"
)

# Instruções gerais para o modelo Gemini
INSTRUCOES_GERAIS = """\n
INSTRUÇÕES PARA ANÁLISE DE DADOS:
1. Você tem liberdade para criar consultas SQL completas
2. Pode usar qualquer campo da tabela
3. Pode criar funções de agregação personalizadas
4. Certifique-se de incluir filtros temporais quando relevante
5. Para análises com múltiplas dimensões (ex: top N por grupo), use QUALIFY ROW_NUMBER() OVER (PARTITION BY ...)
6. Só gere visualização gráfica se o usuário solicitar explicitamente um gráfico, visualização, plot, curva, barra, linha ou termos semelhantes.
   - Nunca gere gráfico por padrão, nem sugira gráfico se não for solicitado.
   - Se solicitado, inclua no final da resposta:
     GRAPH-TYPE: [tipo] | X-AXIS: [coluna] | Y-AXIS: [coluna] | COLOR: [coluna]
     Tipos suportados: bar, line
     Exemplo: 
      Usuário: "Quais as vendas das lojas de limoeiro em janeiro/2025?"
      Resposta: [NÃO incluir gráfico]
      Usuário: "Me mostre um gráfico das vendas das lojas de limoeiro em janeiro/2025"
      Resposta: [Incluir gráfico conforme instrução]
7. Para consultas com múltiplas dimensões (3+), sempre use PARTITION BY no QUALIFY
8. PARA CÁLCULOS PERCENTUAIS:
- SEMPRE verifique se o denominador é diferente de zero antes de dividir
- Para produtos sem vendas no período anterior (denominador zero):
  - Ou retorne NULL e filtre depois
- Use CASE WHEN para tratamento seguro:
  CASE WHEN vendas_anterior > 0 THEN (vendas_atual - vendas_anterior)/vendas_anterior ELSE NULL END
- Para rankings de crescimento, sempre inclua HAVING crescimento IS NOT NULL
9. TABELAS DISPONÍVEIS - USE APENAS ESTAS TABELAS:
"""

def build_tables_instruction():
    """Constrói a instrução das tabelas dinamicamente do JSON"""
    if not TABLES_CONFIG:
        return "Nenhuma tabela configurada."
    
    tables_instruction = ""
    for table_name, table_config in TABLES_CONFIG.items():
        tables_instruction += f"\n### Tabela: {table_name}\n"
        tables_instruction += f"Descrição: {table_config['description']}\n"
        
        # Lidar com fields_description como array ou string
        fields_desc = table_config['fields_description']
        if isinstance(fields_desc, list):
            tables_instruction += "\n".join(fields_desc) + "\n"
        else:
            tables_instruction += f"{fields_desc}\n"
    
    return tables_instruction

# Construir a parte das tabelas para a instrução do sistema
TABLES_INSTRUCTION = build_tables_instruction()

# Instruções adicionais
ADDITIONAL_INSTRUCTIONS = """
INSTRUÇÕES ADICIONAIS PARA QUALIFY E AGRUPAMENTO:

1. PARA DATAS:
- Para agrupar por mês: inclua "EXTRACT(MONTH FROM dta_venda) AS mes" no SELECT
- Para agrupar por ano: inclua "EXTRACT(YEAR FROM dta_venda) AS ano" no SELECT
- Referencie esses campos no GROUP BY como "mes" ou "ano"

2. PARA TOP N POR GRUPO:
- Use "qualify" com: "ROW_NUMBER() OVER (PARTITION BY [grupo] ORDER BY [métrica] DESC) <= N"
- Para múltiplas dimensões: PARTITION BY deve incluir todas as dimensões de agrupamento
- Exemplo válido para 3 dimensões: "ROW_NUMBER() OVER (PARTITION BY mes, uf ORDER BY total_vendas DESC) <= 3"
- INCLUA SEMPRE todos os campos do PARTITION BY no SELECT

3. REGRAS DE CONSISTÊNCIA:
- Campos no QUALIFY devem estar no SELECT
- Campos no GROUP BY devem estar no SELECT
- Para gráficos com 3+ dimensões: use COLOR para a terceira dimensão
- NUNCA agrupe por dta_venda quando quiser análise mensal/anual
- NUNCA use LIMIT com QUALIFY

4. PARA CAMPOS DE TEXTO COM GRANDE VARIAÇÃO DE VALORES:
- Use LIKE para buscas em campos como "cidade", "modelo", "loja"
- Entenda que normalmente o usuário quer buscar por 
  um padrão específico e ele usa "em" ou "de" ou "no" ou qualquer outra preposição semelhante para locais como cidade e loja.

5. VALIDAÇÃO DE TABELAS:
- SEMPRE use apenas as tabelas listadas acima
- Verifique se a tabela solicitada existe na lista
- Para vendas de veículos: use drvy_VeiculosVendas
- Para consórcio ativo: use dvry_ihs_cotas_ativas
- Para histórico de consórcio: use dvry_ihs_qualidade_vendas_historico
- Para dados financeiros: use api_webservice_plano
"""

# Instrução completa do sistema
# Instrução completa do sistema
SYSTEM_INSTRUCTION = f"""
Você é um assistente de dados especializado em análise de negócios. Regras ABSOLUTAS:

1. SEMPRE use a função query_business_data para consultar dados
2. NUNCA mostre a consulta SQL diretamente ao usuário
3. Para análises temporais: use EXTRACT() explicitamente no SELECT
4. APENAS USE AS TABELAS CONFIGURADAS NO SISTEMA

{INSTRUCOES_GERAIS}

{TABLES_INSTRUCTION}

{ADDITIONAL_INSTRUCTIONS}
"""