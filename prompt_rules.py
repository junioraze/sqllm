# Instrução centralizada para refino/tabularização
REFINE_ANALYSIS_INSTRUCTION = """
INSTRUÇÕES DE FORMATO DE RESPOSTA PARA ANÁLISE FINAL:
- Sempre apresente o resultado principal em formato de tabela (markdown ou similar), mesmo que seja uma única linha.
- Sempre que possível, derive e apresente variações, percentuais, totais, médias, rankings ou comparações relevantes, mesmo que não explicitamente solicitados, para enriquecer a análise.
- Após a tabela, forneça uma análise textual clara, destacando os principais pontos, tendências e possíveis interpretações.
- Nunca responda apenas com texto seco; sempre inclua a tabela e análises derivadas.
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
EXEMPLO CRÍTICO (CTE correta, só placeholders):
WITH cte_agrupada AS (
    SELECT campo_temporal, campo_categoria, SUM(campo_valor) AS valor_total
    FROM tabela
    GROUP BY campo_temporal, campo_categoria
)
SELECT campo_temporal, campo_categoria, valor_total
FROM cte_agrupada
ORDER BY campo_temporal, campo_categoria

// ERRADO: nunca faça GROUP BY campo_temporal, campo_categoria, valor_total

REGRAS ESSENCIAIS:
- No SELECT final, NUNCA coloque colunas agregadas (ex: valor_total) no GROUP BY. Só campos não agregados vão no GROUP BY.
- No SELECT final, só inclua no SELECT colunas do GROUP BY ou agregadas (ex: SUM, COUNT, AVG). Nunca coloque coluna não agregada fora do GROUP BY.
- SEMPRE use CTE (WITH) para toda query, mesmo simples.
- O campo 'cte' deve conter apenas a(s) definição(ões) de CTE, nunca o SELECT final.
- O campo 'from_table' deve ser o alias definido na CTE.
- O campo 'select' é uma lista de strings, cada item uma coluna/expressão, nunca uma string única com vírgulas.
- Sempre preencha todos os parâmetros do function_call.
- Use apenas tabelas/campos listados no contexto.

ATENÇÃO: Nunca envie parâmetros de consulta como texto puro, JSON, string, markdown ou qualquer formato diferente de function_call. Sempre envie o objeto/dict puro para o function_call, exatamente como o backend espera. O campo "full_table_id" é OBRIGATÓRIO em TODOS os casos.

Nunca gere dois SELECTs seguidos na query final. O SELECT principal deve ser sempre separado das definições de CTE.


ATENÇÃO: NUNCA envie parâmetros de consulta como texto puro, JSON isolado, string, markdown (```json ... ```), ou qualquer formato diferente de function_call. Sempre envie o objeto/dict puro (ou tuple com dict) para o function_call, exatamente como o backend espera. NÃO ESQUEÇA: O campo "full_table_id" é OBRIGATÓRIO em TODOS os casos, mesmo quando a consulta usa CTE. Sempre inclua "full_table_id" nos parâmetros, indicando a tabela base do BigQuery utilizada. Não envie explicações, JSON, markdown, texto solto ou qualquer outro formato para parâmetros de consulta. O backend só aceita function_call.

REGRAS ABSOLUTAS PARA GERAÇÃO DE QUERIES SQL:

1. SEMPRE use CTE (WITH) para TODA query, mesmo as mais simples. Toda consulta DEVE ser estruturada usando CTE, mesmo que haja apenas uma tabela ou um único passo. Exemplo: WITH t1 AS (SELECT ... FROM ... WHERE ...) SELECT ... FROM t1 ...
2. O campo 'cte' DEVE ser preenchido SEMPRE, contendo APENAS a(s) definição(ões) de CTE (WITH ... AS (...)), NUNCA o SELECT final. O SELECT principal deve ser montado separadamente, fora do campo 'cte', usando os aliases definidos nas CTEs.
     - Exemplo CORRETO de 'cte':
         WITH t1 AS (SELECT ... FROM ... WHERE ...)
     - Exemplo INCORRETO de 'cte':
         WITH t1 AS (SELECT ... FROM ...) SELECT ... FROM t1 ...
     - O SELECT final NUNCA deve estar dentro do campo 'cte'.
3. O campo 'select' deve ser uma lista de strings, cada item representando uma coluna ou expressão, SEM aspas internas e SEM concatenar tudo em uma única string.
     - Exemplo CORRETO de 'select':
         ["coluna1", "coluna2", "SUM(valor) AS total"]
     - Exemplo INCORRETO de 'select':
         ["'coluna1', 'coluna2', 'SUM(valor) AS total'"]
         ou
         ["coluna1, coluna2, SUM(valor) AS total"]
     - Cada item da lista deve ser uma expressão SQL válida, sem aspas simples ou duplas internas, e nunca uma string única com várias colunas separadas por vírgula.
     - O pipeline irá montar o SELECT usando cada item da lista como uma coluna.

4. O campo 'from_table' DEVE referenciar o alias definido na CTE (ex: 't1', ou um JOIN entre aliases definidos na CTE). Nunca use o nome da tabela original diretamente no FROM se houver CTE.
5. Nomes de tabela SEMPRE no formato {PROJECT_ID}.{DATASET_ID}.nome_da_tabela, usando apenas UM acento grave (`) ao redor do nome da tabela, nunca dois e nunca sem acento. O backend NÃO adiciona nem remove acentos graves: o modelo é responsável por garantir o formato correto, exatamente como o BigQuery espera.
6. Use apenas os campos listados no contexto de metadados da tabela (nunca invente nomes).
7. Preencha todos os parâmetros do function_call: full_table_id, select, where, group_by, order_by, cte, qualify, limit, etc.
8. Para análises temporais, use EXTRACT() ou FORMAT_DATE() explicitamente no SELECT, GROUP BY e ORDER BY.
9. Para rankings, use QUALIFY ROW_NUMBER() OVER (...), nunca LIMIT.
10. Para comparações entre grupos/categorias, use CTE + JOIN entre aliases.
11. Nunca mostre SQL ao usuário, apenas execute via function_call.
12. Só gere visualização gráfica se explicitamente solicitado (veja instruções de gráfico abaixo).
13. Use apenas as tabelas e campos listados abaixo.



REGRAS PARA VALORES DE FILTRO E FLAGS:
- Nunca assuma que um campo é binário (S/N, 1/0, TRUE/FALSE) apenas pelo nome. Só trate como flag se o nome terminar com _fl, _flag, _sn, ou se a descrição/exemplos indicarem explicitamente que é binário.
- Os exemplos de valores fornecidos no dicionário (campo "examples") servem apenas como referência para dedução do tipo e semântica dos valores esperados, nunca como lista exaustiva. Use-os para entender o padrão de valor esperado, mas deduza o valor correto a partir do contexto, descrição e lógica de negócio.
- Nunca limite a consulta apenas aos exemplos. Se o campo aceitar outros valores (ex: texto livre, múltiplos tipos), utilize a descrição e o contexto para deduzir o valor correto.
- Nunca assuma valores genéricos como 'S', 'N', '1', '0' só pelo nome do campo. Sempre valide pelo contexto, descrição e exemplos.
- Exemplo INCORRETO: WHERE campo = 'S'  (não existe valor 'S' para esse campo)
- Exemplo CORRETO: WHERE campo = 'valor_exemplo'
- Exemplo CORRETO para flag: WHERE campo_flag = 1 

ATENÇÃO: Nunca gere dois SELECTs seguidos na query final. O SELECT principal deve ser sempre separado das definições de CTE.
"""

# Função para construir instrução dinâmica das tabelas/campos válidos

def build_tables_fields_instruction():
    if not TABLES_CONFIG:
        return "Nenhuma tabela configurada."
    instr = "\n=== TABELAS E CAMPOS DISPONÍVEIS ===\n"
    for table, conf in TABLES_CONFIG.items():
        instr += f"\nTabela: `{PROJECT_ID}.{DATASET_ID}.{table}`\n"
        if 'metadata' in conf:
            instr += f"Descrição: {conf['metadata'].get('description','')}\n"
        else:
            instr += f"Descrição: {conf.get('description','')}\n"
        # Campos detalhados
        if 'fields' in conf:
            for cat, fields in conf['fields'].items():
                if isinstance(fields, list) and fields:
                    instr += f"{cat}:\n"
                    for field in fields:
                        if not isinstance(field, dict) or 'name' not in field:
                            continue
                        instr += f"  - {field['name']} ({field.get('type','')})"
                        if field.get('description'):
                            instr += f" | {field['description']}"
                        # Exemplos
                        if field.get('examples') and isinstance(field['examples'], list) and field['examples']:
                            exemplos = ', '.join(str(e) for e in field['examples'][:5])
                            instr += f" | exemplos: {exemplos}"
                        # Padrão de busca
                        if field.get('search_pattern'):
                            instr += f" | busca: {field['search_pattern']}"
                        # Conversão/uso
                        if field.get('conversion'):
                            instr += f" | conversão: {field['conversion']}"
                        if field.get('usage'):
                            instr += f" | uso: {field['usage']}"
                        instr += "\n"
    return instr

# Instruções para gráfico/exportação (apenas para refino, nunca na function_call)
CHART_EXPORT_INSTRUCTIONS = """
INSTRUÇÕES PARA GRÁFICO/EXPORTAÇÃO (APENAS SE O USUÁRIO SOLICITAR):
- Só gere gráfico se o usuário pedir explicitamente (gráfico, visualização, plot, curva, barra, linha, etc).
- Nunca gere gráfico por padrão.
- Se solicitado, inclua no final da resposta:
    GRAPH-TYPE: [tipo] | X-AXIS: [coluna] | Y-AXIS: [coluna] | COLOR: [coluna]
    Tipos suportados: bar, line
- Só use como COLOR colunas que estejam presentes no resultado da consulta. Se não houver coluna adequada para COLOR, omita o parâmetro COLOR.
- Nunca assuma que existe uma coluna chamada "ano", "categoria" ou similar: sempre verifique as colunas reais do resultado antes de definir COLOR.
- Para exportação, só gere links ou instruções se o usuário pedir (exportar, excel, csv, baixar, download).
"""

# Exemplos de uso e melhores práticas (pode ser expandido)
EXAMPLES_AND_BEST_PRACTICES = """
EXEMPLOS DE USO E MELHORES PRÁTICAS:
- Para perguntas como "top 5 produtos e evolução mensal": use CTE para identificar o top N e depois filtrar a evolução.
- Para comparações entre anos: use CTEs separadas para cada ano e UNION ALL.
- Para rankings: QUALIFY ROW_NUMBER() OVER (...)
- Para análises temporais: FORMAT_DATE('%Y-%m', campo_data) AS periodo_mes
- Sempre trate divisões por zero com CASE WHEN ...
"""

# Função utilitária para obter instrução completa para function_call

def get_sql_functioncall_instruction():
    return SQL_FUNCTIONCALL_INSTRUCTIONS + build_tables_fields_instruction() + "\n" + EXAMPLES_AND_BEST_PRACTICES

# Função utilitária para obter instrução de gráfico/exportação para refino

def get_chart_export_instruction():
    return CHART_EXPORT_INSTRUCTIONS
