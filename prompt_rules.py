# Instrução centralizada para refino/tabularização
REFINE_ANALYSIS_INSTRUCTION = """
    INSTRUÇÕES DE FORMATO DE RESPOSTA PARA ANÁLISE FINAL:
    - Apresente o resultado principal em tabela.
    - Sempre traga análise textual com insights, reflexões e implicações relevantes para o negócio.
    - Destaque tendências, oportunidades e riscos, mesmo que não explicitamente solicitados.
    - Enriqueça a resposta com comparações, percentuais, rankings ou benchmarks quando possível.
    - Evite respostas secas: sempre agregue valor com contexto e visão estratégica.
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
- Agregação (ex: SUM, COUNT, AVG, GROUP BY) — nomeie como cte_agregacao, cte_agrupamento.
- Ranking/window (ex: ROW_NUMBER, QUALIFY, DENSE_RANK) — nomeie como cte_ranking, cte_final.
- Comparação/análise (ex: JOINs, pivots, cálculos finais) — nomeie como cte_comparacao, cte_pivot.
- Nunca misture transformação e análise na mesma CTE.
- Use nomes descritivos e consistentes para CTEs e aliases de campos.

REGRAS CRÍTICAS PARA O SELECT FINAL:
- O SELECT final NUNCA deve conter GROUP BY ou agregação (SUM, COUNT, AVG, etc). Toda agregação deve ocorrer dentro de uma CTE específica.
- O SELECT final apenas projeta os campos agregados e agrupados definidos nas CTEs e ordena para garantir o eixo X correto no gráfico.
- Nunca gere dois SELECTs seguidos na query final; o SELECT principal deve ser separado das definições de CTE.

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

Nunca assuma que um campo é binário (S/N, 1/0, TRUE/FALSE) apenas pelo nome. Só trate como flag se o nome terminar com _fl, _flag, _sn, ou se a descrição/exemplos indicarem explicitamente que é binário.
Os exemplos de valores fornecidos no dicionário (campo "examples") servem apenas como referência para dedução do tipo e semântica dos valores esperados, nunca como lista exaustiva. Use-os para entender o padrão de valor esperado, mas deduza o valor correto a partir do contexto, descrição e lógica de negócio.
Nunca limite a consulta apenas aos exemplos. Se o campo aceitar outros valores (ex: texto livre, múltiplos tipos), utilize a descrição e o contexto para deduzir o valor correto.
Nunca assuma valores genéricos como 'S', 'N', '1', '0' só pelo nome do campo. Sempre valide pelo contexto, descrição e exemplos.
Exemplo INCORRETO: WHERE campo = 'S' (não existe valor 'S' para esse campo)
Exemplo CORRETO: WHERE campo = 'valor_exemplo'
Exemplo CORRETO para flag: WHERE campo_flag = 1
ATENÇÃO: Nunca gere dois SELECTs seguidos na query final. O SELECT principal deve ser sempre separado das definições de CTE.

EXEMPLO GENERALISTA DE PADRÃO CORRETO:
WITH cte_agregacao AS (
    SELECT campo_agrupado, SUM(valor) AS total
    FROM tabela
    GROUP BY campo_agrupado
)
SELECT campo_agrupado, total
FROM cte_agregacao
ORDER BY campo_agrupado
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
