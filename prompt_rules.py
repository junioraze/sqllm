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
- Só gere visualização gráfica se explicitamente solicitado pelo usuário.
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
- Limpeza/conversão (ex: CAST, EXTRACT, UPPER, filtros) — nomeie como cte_limpeza, cte_preparacao. Campos que vao na instrução com o parametro conversion (normalmente campos TIMESTAMP) devem ser convertidos se utilizados. 
- Agregação (ex: SUM, COUNT, AVG, GROUP BY) — nomeie como cte_agregacao, cte_agrupamento.
- Ranking/window (ex: ROW_NUMBER, DENSE_RANK) — nomeie como cte_ranking, cte_final.
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
ATENÇÃO: Nunca gere dois SELECTs seguidos na query final. O SELECT principal deve ser sempre separado das definições de CTE.
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
- Cada CTE que tenha dependencia de outra CTE só pode projetar campos simples ou aliases definidos nas CTEs (ex: total, quantidade, valor_normalizado). Precisamos manter as referências corretas das colunas de cada CTE para evitar quebra. 
- Cada CTE que tenha dependencia de outra CTE NUNCA deve conter funções/extratos sobre campos que já foram convertidos em aliases nas CTEs. Use apenas os aliases definidos e as colunas que nao foram alteradas o nome mas estao presente na CTE consultada.


REGRAS CRÍTICAS PARA O SELECT FINAL:
- O SELECT final NUNCA deve conter GROUP BY ou agregação (SUM, COUNT, AVG, etc). Toda agregação deve ocorrer dentro de uma CTE específica.
- O SELECT final só pode projetar campos simples ou aliases definidos nas CTEs (ex: total, quantidade, valor_normalizado). Nunca inclua funções de agregação, expressões ou cálculos no SELECT final.
- O SELECT final NUNCA deve conter funções/extratos sobre campos que já foram convertidos em aliases nas CTEs. Use apenas os aliases definidos e as colunas que nao foram alteradas o nome mas estao presente na CTE consultada.
- Se precisar de um valor agregado, defina o alias na CTE e use apenas o alias no SELECT final.
- O SELECT final apenas projeta os campos agregados e agrupados definidos nas CTEs e ordena para garantir o eixo X correto no gráfico.
- Nunca gere dois SELECTs seguidos na query final; o SELECT principal deve ser separado das definições de CTE.

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
