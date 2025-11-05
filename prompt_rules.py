# Instrução centralizada para refino/tabularização
REFINE_ANALYSIS_INSTRUCTION = """
    INSTRUÇÕES DE FORMATO DE RESPOSTA PARA ANÁLISE FINAL:
    - Apresente o resultado principal em tabela.
    - Sempre traga análise textual com insights, reflexões e implicações relevantes para o negócio.
    - Destaque tendências, oportunidades e riscos, mesmo que não explicitamente solicitados.
    - Enriqueça a resposta com comparações, percentuais, rankings ou benchmarks quando possível.
    - Evite respostas secas: sempre agregue valor com contexto e visão estratégica.
    """

CHART_EXPORT_INSTRUCTIONS = """
INSTRUÇÕES DE GRÁFICO/EXPORTAÇÃO:
- [EXTREMAMENTE IMPORTANTE] Só gere visualização gráfica se explicitamente solicitado pelo usuário no prompt.
- O gráfico deve sempre usar o eixo X conforme definido no SELECT final (ex: campo_periodo, campo_eixo_x, campo_categoria).
- Use o tipo de gráfico mais adequado ao contexto: barras para comparações, linhas para séries temporais, pizza para proporções, etc.
- Sempre inclua legenda, título e rótulos claros nos eixos.
- Exporte os dados em formato tabular antes de gerar o gráfico.
- Nunca inclua dados ou campos não presentes no SELECT final.
- Se solicitado exportação, gere CSV ou Excel com os campos do SELECT final, sem agregações extras.

INSTRUÇÃO CRÍTICA DE FORMATO DE RESPOSTA PARA GRÁFICO:
Sempre inclua na resposta, de forma destacada, o tipo de gráfico solicitado pelo usuário, usando o formato:
GRAPH-TYPE: <tipo> | X-AXIS: <coluna_x> | Y-AXIS: <coluna_y> | COLOR: <coluna_color (opcional)>
Exemplo: GRAPH-TYPE: bar | X-AXIS: divulgadores_tipo_divulgador | Y-AXIS: variacao_percentual

"""


# Função utilitária para obter instrução de refino/tabularização
def get_refine_analysis_instruction():
    return REFINE_ANALYSIS_INSTRUCTION
"""
Módulo central de instruções e regras para o sistema de análise de dados
=======================================================================

Este módulo centraliza todas as instruções, exemplos, regras críticas e padrões para:
- Geração de queries SQL (function_call)
- Contexto de tabelas e campos válidos
- Instruções de gráfico/exportação (apenas para refino)
- Exemplos de uso e melhores práticas

Todas as funções/variáveis aqui devem ser importadas e usadas por todo o pipeline.
"""

import os
from config import TABLES_CONFIG, PROJECT_ID, DATASET_ID

# Função para construir descrição detalhada das tabelas para uso em FunctionDeclaration
def build_tables_description():
    """Gera descrição detalhada das tabelas e campos válidos para uso no FunctionDeclaration"""
    desc = "Tabelas disponíveis para consulta:\n"
    for table_name, conf in TABLES_CONFIG.items():
        full_table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
        description = conf.get('metadata', {}).get('description', '')
        fields = []
        if 'fields' in conf:
            for cat, field_list in conf['fields'].items():
                if isinstance(field_list, list):
                    fields += [f["name"] for f in field_list if isinstance(f, dict) and "name" in f]
        desc += f"\n- {full_table_id}: {description}\n  Campos: {', '.join(fields)}"
    return desc

# Instruções para geração de queries SQL (function_call)

SQL_FUNCTIONCALL_INSTRUCTIONS = """
PADRÃO OBRIGATÓRIO DE CTEs (GENERALISTA):

Toda query deve ser estruturada usando múltiplas CTEs, cada uma com responsabilidade única:
- Limpeza/conversão (ex: CAST, EXTRACT, UPPER, filtros) — nomeie como cte_limpeza, cte_preparacao. 
  ⚠️  CRÍTICO: Se um campo é STRING e vai ser usado em EXTRACT() ou comparações de data, SEMPRE faça CAST ANTES na cláusula WHERE também!
  CORRETO: WHERE EXTRACT(YEAR FROM CAST(campo_data AS DATE)) = 2024
  ERRADO: WHERE EXTRACT(YEAR FROM campo_data) = 2024  [campo_data é STRING]
  Campos que vao na instrução com o parametro conversion (normalmente campos TIMESTAMP/STRING de data) devem ser convertidos quando forem ser utilizados. 
- Agregação (ex: SUM, COUNT, AVG, GROUP BY) — nomeie como cte_agregacao, cte_agrupamento.
- Ranking/window (ex: ROW_NUMBER, DENSE_RANK) — nomeie como cte_ranking, cte_final.
- Comparação/análise (ex: JOINs, pivots, cálculos finais) — nomeie como cte_comparacao, cte_pivot.
- Nunca misture transformação e análise na mesma CTE.
- Use nomes descritivos e consistentes para CTEs e aliases de campos.

REGRAS CRÍTICAS PARA O SELECT FINAL:
- O SELECT final OBRIGATORIAMENTE SEMPRE DEVE EXISTIR ao final da query - sem exceção!
- O SELECT final NUNCA deve conter GROUP BY ou agregação (SUM, COUNT, AVG, etc). Toda agregação deve ocorrer dentro de uma CTE específica.
- O SELECT final apenas projeta os campos agregados e agrupados definidos nas CTEs e ordena para garantir o eixo X correto no gráfico.
- ⚠️  CRÍTICO: SEMPRE inclua o SELECT final após as definições de CTE. Nunca deixe a query terminando no meio de uma CTE!
- CORRETO: WITH cte_agregacao AS (...), cte_ranking AS (...) SELECT * FROM cte_ranking
- ERRADO: WITH cte_agregacao AS (...), cte_ranking AS (...)  [SEM SELECT FINAL]

O GROUP BY pode conter múltiplos campos/dimensões conforme o contexto da pergunta (ex: campo_periodo, campo_eixo_x, campo_categoria, etc). Sempre inclua todos os campos não agregados do SELECT no GROUP BY da CTE de agrupamento.
Só inclua no SELECT final colunas agregadas ou agrupadas (SUM, COUNT, AVG) já definidas nas CTEs.

REGRAS DE ORDENAÇÃO (ORDER BY):
- A ordenação (ORDER BY) deve ocorrer sempre no SELECT final, nunca dentro das CTEs.
- Priorize SEMPRE o campo de período (ex: campo_periodo, campo_data, campo_mes, campo_ano) para ordenação.
- Se não existir campo de período, use o campo principal do eixo X (ex: campo_eixo_x, campo_categoria) ou a ordem natural dos registros.
- Nunca ordene por valores agregados (ex: SUM, COUNT) no SELECT final, apenas pelos campos de dimensão/eixo X.

Exemplo generalista:
WITH cte_agregacao AS (
    SELECT campo_periodo, campo_eixo_x, SUM(campo_valor) AS valor_total
    FROM nome_da_tabela
    WHERE ...
    GROUP BY campo_periodo, campo_eixo_x
)
SELECT campo_periodo, campo_eixo_x, valor_total
FROM cte_agregacao
ORDER BY campo_periodo, campo_eixo_x

REGRAS ESPECÍFICAS PARA MONTAGEM DE QUERY:
4. O campo 'from_table' DEVE referenciar o alias definido na CTE (ex: 't1', ou um JOIN entre aliases definidos na CTE). Nunca use o nome da tabela original diretamente no FROM se houver CTE.
5. ⚠️  TABELAS: SEMPRE use o formato COMPLETO com dataset: `glinhares.delivery.nome_tabela` 
   - Exemplos CORRETOS: `glinhares.delivery.drvy_VeiculosVendas` ou `glinhares.delivery.dvry_ihs_cotas_ativas`
   - NUNCA use apenas o nome da tabela: `drvy_VeiculosVendas` (ERRADO) 
   - NUNCA use dataset errado ou sem dataset
   - O acento grave ` é OBRIGATÓRIO ao redor do nome completo: ` `glinhares.delivery.nome_tabela` `
   - Nomes de tabela SEMPRE no formato {PROJECT_ID}.{DATASET_ID}.nome_da_tabela, usando apenas UM acento grave (`) ao redor de TODA a expressão, nunca dois e nunca sem acento. O backend NÃO adiciona nem remove acentos graves: o modelo é responsável por garantir o formato correto, exatamente como o BigQuery espera.
6. Use apenas os campos listados no contexto de metadados da tabela (nunca invente nomes).
7. Preencha todos os parâmetros do function_call: select, where, order_by, cte,  etc.

REGRAS PARA AGRUPAMENTO:
O agrupamento (GROUP BY) deve ser sempre feito dentro do CTE de agregação. Nunca inclua parâmetro group_by externo no function_call. O SELECT final só projeta e ordena os campos já agregados/agrupados definidos nas CTEs.
8. Para análises temporais, use EXTRACT() ou FORMAT_DATE() explicitamente no SELECT, GROUP BY e ORDER BY.
9. Para rankings, crie o campo analítico (ROW_NUMBER, RANK, etc) na CTE e filtre no SELECT final usando WHERE ranking <= N. Nunca use QUALIFY nem LIMIT no SELECT final.
10. Para comparações entre grupos/categorias, use CTE + JOIN entre aliases.
11. Nunca mostre SQL ao usuário, apenas execute via function_call.
12. Só gere visualização gráfica se explicitamente solicitado (veja instruções de gráfico abaixo).
13. Use apenas as tabelas e campos listados abaixo.

REGRAS PARA VALORES DE FILTRO E FLAGS:

Nunca assuma que um campo é binário (S/N, 1/0, TRUE/FALSE) apenas pelo nome. Só trate como flag se o nome terminar com _fl, _flag, _sn, ou se a descrição/exemplos indicarem explicitamente que é binário.
Os exemplos de valores fornecidos no dicionário (campo "examples") servem apenas como referência para dedução do tipo e semântica dos valores esperados, nunca como lista exaustiva. Use-os para entender o padrão de valor esperado, mas deduza o valor correto a partir do contexto, descrição e lógica de negócio.
Nunca limite a consulta apenas aos exemplos. Se o campo aceitar outros valores (ex: texto livre, múltiplos tipos), utilize a descrição e o contexto para deduzir o valor correto.
Nunca assuma valores genéricos como 'S', 'N', '1', '0' só pelo nome do campo. Sempre valide pelo contexto, descrição e exemplos.
Exemplo INCORRETO: WHERE campo = 'S' (não existe valor 'S' para esse campo)
Exemplo CORRETO: WHERE campo = 'valor_exemplo'
Exemplo CORRETO para flag: WHERE campo_flag = 1

⚠️  CRÍTICO - CAMPOS VÁLIDOS:
- NUNCA INVENTE NOMES DE CAMPOS!
- USE APENAS os campos listados na seção "CAMPOS DISPONÍVEIS NESTA TABELA"
- Se não encontrar um campo exato, use um alias apropriado ou nome similar que REALMENTE EXISTE
- Exemplo ERRADO: SELECT desc_plano (campo não existe!)
- Exemplo CORRETO: SELECT Plano (campo que está na lista)
- O backend NÃO valida nem corrige nomes de campos - a responsabilidade é ÚNICA do modelo!

⚠️  CRÍTICO - SELECT FINAL OBRIGATÓRIO:
- SEMPRE inclua um SELECT final ao final da query!
- CORRETO: WITH cte_agregacao AS (...) SELECT ... FROM cte_agregacao
- ERRADO: WITH cte_agregacao AS (...) [SEM SELECT]
- ERRADO: Queries que terminam com definição de CTE sem SELECT
"""

# Função para construir instrução dinâmica das tabelas/campos válidos


def build_tables_fields_instruction():
    return """
DEFINIÇÃO:
VOCÊ É UMA FERRAMENTA DE CONVERTER LINGUAGEM NATURAL EM PARAMETRIZAÇÃO PARA GERAÇÃO DE SQL CONFORME OS PARAMETROS DECLARADOS NOS SEUS PARAMETERS

REGRA CRÍTICA DE FORMATAÇÃO DE RESPOSTA:
NUNCA retorne a resposta em formato markdown (ex: ```json ... ``` ou qualquer bloco ``` ... ```). Sempre retorne o JSON puro, sem qualquer formatação markdown, para evitar erros de parsing.
NUNCA, EM HIPÓTESE ALGUMA, gere comentários dentro dos parametros que vao para geração do SQL (nem --, nem /* ... */) em nenhuma query. Comentários de SQL nos parametros não são permitidos e causam uma falha FATAL.


PADRÃO OBRIGATÓRIO DE CTEs (GENERALISTA):
- Toda query deve ser estruturada usando múltiplas CTEs, cada uma com responsabilidade única.
- Toda query deve ser estruturada usando múltiplas CTEs, cada uma com responsabilidade única:
- Limpeza/conversão (ex: CAST, EXTRACT, UPPER, filtros) — nomeie como cte_limpeza, cte_preparacao. Campos que sao enviados na instrução com o parametro conversion (normalmente campos TIMESTAMP) devem ser convertidos quando forem ser utilizados.
- Agregação (ex: SUM, COUNT, AVG, GROUP BY) — nomeie como cte_agregacao, cte_agrupamento.
- Ranking/window (ex: ROW_NUMBER, DENSE_RANK) — nomeie como cte_ranking, cte_final.
- Comparação/análise (ex: JOINs, pivots, cálculos finais) — nomeie como cte_comparacao, cte_pivot.
- Nunca misture transformação e análise na mesma CTE.
- Use nomes descritivos e consistentes para CTEs e aliases de campos. 
- Ao construir queries com múltiplas CTEs, garanta que cada SELECT/CTE só utilize campos disponíveis a partir da CTE/tabela anterior. Nunca referencie campos que não foram projetados ou transformados. Se fizer JOIN entre CTEs, valide os campos de ambos os lados. O SELECT final deve usar apenas campos/aliases disponíveis nas fontes declaradas no FROM.


REGRAS CRÍTICAS PARA O SELECT FINAL:
- O SELECT final NUNCA deve conter GROUP BY ou agregação (SUM, COUNT, AVG, etc). Toda agregação deve ocorrer dentro de uma CTE específica.
- O SELECT final só pode projetar campos simples ou aliases definidos nas CTEs (ex: total, quantidade, valor_normalizado). Nunca inclua funções de agregação, expressões ou cálculos no SELECT final.
- O SELECT final NUNCA deve conter funções/extratos sobre campos que já foram convertidos em aliases nas CTEs. Use apenas os aliases definidos e as colunas que nao foram alteradas o nome mas estao presente na CTE consultada.
- Se precisar de um valor agregado, defina o alias na CTE e use apenas o alias no SELECT final.
- O SELECT final apenas projeta os campos agregados e agrupados definidos nas CTEs e ordena para garantir o eixo X correto no gráfico.
- ⚠️  CRÍTICO: O SELECT final OBRIGATORIAMENTE SEMPRE DEVE EXISTIR ao final da query - sem exceção!
- CORRETO: WITH cte_agregacao AS (...), cte_ranking AS (...) SELECT ... FROM cte_ranking
- ERRADO: WITH cte_agregacao AS (...), cte_ranking AS (...) [FALTANDO SELECT FINAL]

Exemplo INCORRETO:
SELECT campo_agrupado, SUM(valor) AS total FROM cte_agregacao
Exemplo CORRETO:
SELECT campo_agrupado, total FROM cte_agregacao

O GROUP BY pode conter múltiplos campos/dimensões conforme o contexto da pergunta (ex: campo_periodo, campo_eixo_x, campo_categoria, etc). Sempre inclua todos os campos não agregados do SELECT no GROUP BY da CTE de agrupamento.
Só inclua no SELECT final colunas agregadas ou agrupadas (SUM, COUNT, AVG) já definidas nas CTEs, usando apenas o alias.

REGRAS DE ORDENAÇÃO (ORDER BY):
- A ordenação (ORDER BY) deve ocorrer sempre no SELECT final, nunca dentro das CTEs.
- Priorize SEMPRE o campo de período (ex: campo_periodo, campo_data, campo_mes, campo_ano) para ordenação.
- Se não existir campo de período, use o campo principal do eixo X (ex: campo_eixo_x, campo_categoria) ou a ordem natural dos registros.
- Nunca ordene por valores agregados (ex: SUM, COUNT) no SELECT final, apenas pelos campos de dimensão/eixo X ou aliases definidos.

Exemplo generalista:
WITH cte_agregacao AS (
    SELECT campo_periodo, campo_eixo_x, SUM(campo_valor) AS valor_total
    FROM nome_da_tabela
    WHERE ...
    GROUP BY campo_periodo, campo_eixo_x
)
SELECT campo_periodo, campo_eixo_x, valor_total
FROM cte_agregacao
ORDER BY campo_periodo, campo_eixo_x
"""

def get_sql_functioncall_instruction():
    return SQL_FUNCTIONCALL_INSTRUCTIONS

# Função utilitária para obter instrução de gráfico/exportação para refino

def get_chart_export_instruction():
    return CHART_EXPORT_INSTRUCTIONS

def get_sql_refinement_instruction():
    """
    Retorna instruções para refino de SQL quando validação falha.
    Usado pelo query_validator para pedir ao Gemini corrigir queries problemáticas.
    """
    return """
VOCÊ É UM ESPECIALISTA EM SQL BIGQUERY QUE REFINA QUERIES PROBLEMÁTICAS

TAREFAS:
1. Analisar o erro na query
2. Manter a MESMA lógica e intenção da query original
3. Corrigir APENAS problemas de sintaxe ou estrutura
4. Garantir que a query esteja COMPLETA e VÁLIDA

REGRAS CRÍTICAS:
- A query DEVE ter este formato: WITH cte_name AS (...) SELECT ... FROM cte_name
- Nunca falta SELECT final após as definições de CTEs
- NÃO ADICIONAR comentários SQL (-- ou /* */)
- Retornar APENAS a query SQL corrigida, sem explicações ou markdown
- Manter todos os campos, filtros e lógica original

REGRA DE COMPLETUDE:
Se a query termina com uma CTE sem SELECT final, adicione:
SELECT * FROM nome_ultima_cte

Exemplo:
ENTRADA: "WITH cte_x AS (SELECT ... FROM ...), cte_y AS (SELECT ... FROM cte_x)"
SAÍDA: "WITH cte_x AS (SELECT ... FROM ...), cte_y AS (SELECT ... FROM cte_x) SELECT * FROM cte_y"

RETORNE APENAS A QUERY CORRIGIDA, NADA MAIS.
"""

def build_field_whitelist_instruction(table_name):
    """
    Constrói instrução com LISTA DE CAMPOS VÁLIDOS para a tabela identificada.
    DESTACA CAMPOS QUE PRECISAM DE CONVERSÃO com exemplos explícitos.
    
    Args:
        table_name: str - nome da tabela (ex: "drvy_VeiculosVendas")
    
    Returns:
        str - Instrução formatada com campos válidos e conversões
    """
    try:
        table_config = TABLES_CONFIG.get(table_name, {})
        
        if not table_config:
            return f"⚠️  Aviso: Tabela '{table_name}' não encontrada em configuração."
        
        # Extrai descrição da tabela
        description = table_config.get('metadata', {}).get('description', 'Sem descrição')
        
        # Coleta todos os campos disponíveis da tabela
        all_fields = []
        fields_with_conversion = []
        fields_info = {}
        
        if 'fields' in table_config:
            for category, field_list in table_config['fields'].items():
                if isinstance(field_list, list):
                    for field in field_list:
                        if isinstance(field, dict) and 'name' in field:
                            field_name = field['name']
                            field_type = field.get('type', 'UNKNOWN')
                            field_desc = field.get('description', '')
                            field_conversion = field.get('conversion', None)
                            field_examples = field.get('examples', [])
                            
                            all_fields.append(field_name)
                            fields_info[field_name] = {
                                'type': field_type,
                                'description': field_desc,
                                'category': category,
                                'conversion': field_conversion,
                                'examples': field_examples
                            }
                            
                            # Se o campo tem conversão, salva separado
                            if field_conversion:
                                fields_with_conversion.append({
                                    'name': field_name,
                                    'type': field_type,
                                    'conversion': field_conversion,
                                    'examples': field_examples,
                                    'description': field_desc
                                })
        
        if not all_fields:
            return f"⚠️  Aviso: Nenhum campo encontrado para tabela '{table_name}'."
        
        # Agrupa campos por tipo para melhor legibilidade
        fields_by_type = {}
        for fname, finfo in fields_info.items():
            ftype = finfo['type']
            if ftype not in fields_by_type:
                fields_by_type[ftype] = []
            fields_by_type[ftype].append((fname, finfo['description']))
        
        # Constrói instrução formatada
        instruction = f"""
🚀 CAMPOS VÁLIDOS PARA TABELA: `glinhares.delivery.{table_name}`

DESCRIÇÃO DA TABELA:
{description}

⚠️  CAMPOS OBRIGATORIAMENTE VÁLIDOS (use APENAS estes):
"""
        
        # Lista campos por tipo
        for ftype, fields_list in sorted(fields_by_type.items()):
            instruction += f"\n{ftype} ({len(fields_list)} campos):\n"
            for fname, fdesc in sorted(fields_list):
                instruction += f"  - {fname}: {fdesc}\n"
        
        # SEÇÃO ESPECIAL: Campos que PRECISAM de conversão
        if fields_with_conversion:
            instruction += f"""

🔥 CAMPOS QUE EXIGEM CONVERSÃO (CRÍTICO - USE EXATAMENTE COMO ESPECIFICADO):

"""
            for field_conv in fields_with_conversion:
                instruction += f"""
📌 CAMPO: {field_conv['name']} ({field_conv['type']})
   DESCRIÇÃO: {field_conv['description']}
   ✅ CONVERSÃO OBRIGATÓRIA: {field_conv['conversion']}
"""
                if field_conv['examples']:
                    instruction += "   EXEMPLOS DE USO:\n"
                    for example in field_conv['examples']:
                        instruction += f"      - {example}\n"
        
        # Instrução crítica
        instruction += f"""

⚠️  REGRA CRÍTICA - VALIDAÇÃO DE CAMPOS:
- NUNCA use campos que NÃO estão nesta lista acima!
- Para campos que exigem CONVERSÃO (seção 🔥 acima), use EXATAMENTE a conversão especificada!

⛔ AVISO CRÍTICO - NÃO USE NOMES DE EXEMPLOS COMO CAMPOS REAIS:
- Quando você vê "COUNT(*) AS total_vendas" em um exemplo, NÃO USE "total_vendas" como nome de campo real!
- Campos como "total_vendas", "COUNT_vendas", "quantidade_total", "valor_medio_quitacao" são NOMES INVENTADOS EM EXEMPLOS
- Use SEMPRE as agregações reais: COUNT(*), SUM(), AVG(), MAX(), MIN()
- Para contar registros: use COUNT(*) não "COUNT_vendas"
- Para somar valores: use SUM(campo_real) não "soma_valores"
- SEMPRE crie aliases com AS para seus cálculos, exemplo: SUM(QTE) AS total_veiculos

- Exemplos de ERROS comuns (campos NÃO EXISTENTES):
  ❌ DataVenda (ERRADO - use Dt_Venda ou equivalent)
  ❌ Vendedor (ERRADO - use Nome_do_Vendedor ou equivalent)
  ❌ Status (ERRADO - use Status_Contrato ou equivalent)
  ❌ data_venda (ERRADO - use data real da tabela)
  ❌ COUNT_vendas (ERRADO - é um EXEMPLO! Use COUNT(*) no lugar)
  ❌ total_propostas (ERRADO - é um EXEMPLO! Use COUNT(DISTINCT Proposta) no lugar)
  ❌ valor_medio_quitacao (ERRADO - é um EXEMPLO! Use AVG(SAFE_CAST(campo_real AS FLOAT64)) no lugar)

- Exemplos de ERROS comuns com CONVERSÃO:
  ❌ CAST(Dt_Venda AS DATE) - ERRADO! Use a conversão especificada na seção 🔥 acima
  ❌ Dt_Venda - ERRADO! Campo é STRING, sempre precisa conversão
  ❌ Usando Dt_Venda diretamente em WHERE - ERRADO! Sempre converta antes

- TODOS os campos usados DEVEM estar na lista acima.
- Se a pergunta solicita um campo que NÃO EXISTE, use o campo mais próximo que EXISTE.
- Se nenhum campo próximo existe, notifique que o campo solicitado não está disponível.

TOTAL DE CAMPOS VÁLIDOS: {len(all_fields)}
CAMPOS QUE PRECISAM CONVERSÃO: {len(fields_with_conversion)}
"""
        
        return instruction
        
    except Exception as e:
        return f"Erro ao construir instrução de campos: {str(e)}"

def get_adaptation_prompt():
    """
    Retorna o template de prompt para adaptação/refinamento de perguntas via Gemini.
    Use .format(last_question=..., nova_pergunta=...) para preencher.
    """
    return (
        "ANÁLISE DE CONTINUIDADE DE CONVERSA - REGRAS GERAIS:\n\n"
        
        "PERGUNTA ANTERIOR:\n"
        '"{last_question}"\n\n'
        
        "NOVA MENSAGEM DO USUÁRIO:\n"
        '"{nova_pergunta}"\n\n'
        
        "ANÁLISE DE INTENÇÃO - CONTINUIDADE vs INDEPENDÊNCIA:\n"
        "\n"
        "📌 SINAIS DE CONTINUIDADE (refinamento/aditivo):\n"
        "- A mensagem pressupõe contexto da anterior (implícito)\n"
        "- Tem caráter aditivo ou corretivo à consulta existente\n"
        "- Estrutura linguística de complemento, não de reinício\n"
        "- Foca em expandir/ajustar aspectos específicos mantendo o núcleo\n"
        "\n"
        "📌 SINAIS DE INDEPENDÊNCIA (nova consulta):\n"
        "- Tem caráter autossuficiente e completo\n"
        "- Estrutura linguística de início novo\n"
        "- Muda o foco principal ou entidade central\n"
        "- Não pressupõe conhecimento da pergunta anterior\n"
        "\n"
        "ANÁLISE ESTRUTURAL - NÚCLEO DA CONSULTA:\n"
        "1. Identifique o NÚCLEO principal de cada pergunta:\n"
        "   - Qual é a entidade/objeto principal?\n"
        "   - Qual é o período/tempo principal?  \n"
        "   - Qual é a métrica/ação principal?\n"
        "\n"
        "2. Se o NÚCLEO mudou = NOVA PERGUNTA\n"
        "3. Se o NÚCLEO se manteve = potencial continuidade\n"
        "\n"
        "REGRA PRÁTICA:\n"
        "A nova mensagem faz sentido sozinha sem contexto anterior?\n"
        "SIM = Nova pergunta independente\n"
        "NÃO = Continuidade (depende do contexto anterior)\n"
        "\n"
        "COMANDOS DE AÇÃO:\n"
        "- Geração de Gráficos são SEMPRE sobre a última consulta explícita(ou uma nova consulta que já pede gráfico, ou a solicitação de inclusao do grafico)\n"
        "- Não propagam automaticamente para novas consultas, ou eles já vem nela ou são adicionados na continuidade \n"
        "\n"
        "SAÍDA: Apenas a pergunta final, sem explicações.\n"
    )
