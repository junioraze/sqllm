COMPARACAO_INSTRUCOES = """\n
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
"""

CAMPOS_DESCRICAO = """\n
EXEMPLOS DE PARÂMETROS VÁLIDOS PARA MÚLTIPLAS DIMENSÕES:
- select: ["EXTRACT(MONTH FROM dta_venda) AS mes", "uf", "modelo", "SUM(QTE) AS total_vendido"]
- where: "EXTRACT(YEAR FROM dta_venda) = 2024"
- group_by: ["mes", "uf", "modelo"]
- order_by: ["mes", "uf", "total_vendido DESC"]
- qualify: "ROW_NUMBER() OVER (PARTITION BY mes, uf ORDER BY total_vendido DESC) <= 3"

REGRAS PARA MÚLTIPLAS DIMENSÕES:
1. SEMPRE inclua todos os campos do PARTITION BY no SELECT
2. NUNCA use LIMIT em consultas com PARTITION BY
3. Para gráficos com 3+ dimensões, use COLOR para representar a terceira dimensão
4. Campos no GROUP BY devem estar no SELECT
5. Caso exista campos sem função de agregação, eles devem estar no GROUP BY se existirem campos com função de agregação no SELECT
6. Campos no QUALIFY devem estar no SELECT
7. Caso o usuário não especifique um Ranking, use o padrão de 5 para TOP N
   - Exemplo para o ponto 7: 
                  Se ele solicitar algo semelhante a "Quais os vendedores com melhor desempenho de vendas em 2025?"
                  Subentenda-se que ele quer o TOP 5 de vendedores
                  Perceba que a pergunta pode vir de diversas outras formas, como "Quais as lojas que mais venderam em 2025?"
                  Ou "Quais os modelos mais vendidos em 2025?"
                  Todos os casos qualificam-se como TOP 5 caso um top N não seja especificado
8. Regra para LIKE: para colunas em que se aplica a regra do LIKE, como modelo e cidade, 
   use o operador LIKE no WHERE e use UPPER na coluna e no valor de busca.
   - Exemplo: "WHERE UPPER(modelo) LIKE UPPER('%valor%')"
9. Quando for solicitado algo como vendas das lojas de limoeiro, ou em limoeiro, ou no limeiro ou referente qualquer outra cidade do brasil,
use o LIKE para a cidade:
   - Exemplo: "WHERE UPPER(cidade) LIKE UPPER('%LIMOEIRO%')"
10. Sempre que o usuário fizer referência a um valor textual (ex: nome de modelo, cidade, loja, bairro, razão social), 
    utilize a busca com LIKE e UPPER, mesmo que o valor não esteja completo ou contenha erros de digitação.
    - Exemplo: Se o usuário disser "vendas em limeiro", busque "UPPER(cidade) LIKE UPPER('%LIMEIRO%')"
11. Nunca use igualdade (=) para campos de texto que podem variar, como modelo, cidade, loja, bairro, razão social.
12. Para buscas múltiplas (ex: "vendas em fortaleza e juazeiro"), use múltiplos LIKE com OR:
    - Exemplo: "WHERE (UPPER(cidade) LIKE UPPER('%FORTALEZA%') OR UPPER(cidade) LIKE UPPER('%JUAZEIRO%'))"
                - where: "UPPER(modelo) LIKE UPPER('%COROLLA%')"
                - where: "UPPER(cidade) LIKE UPPER('%LIMOEIRO%')"
                - where: "UPPER(loja) LIKE UPPER('%ARES MOTOS%')"
                - where: "(UPPER(cidade) LIKE UPPER('%FORTALEZA%') OR UPPER(cidade) LIKE UPPER('%JUAZEIRO%'))"

13. Regra para filtro por tipo de veículo (motos ou carros):
    - Sempre que o usuário fizer referência genérica a "motos" ou "carros" (sem especificar modelo), utilize o filtro pela coluna Negocio_CC:
        • Para motos: WHERE Negocio_CC = '2R'
        • Para carros: WHERE Negocio_CC = '4R'
    - Não utilize LIKE ou outros filtros para esse caso, apenas o filtro direto por Negocio_CC.
    - Exemplo:
        Usuário: "Quais as vendas de motos em 2024?"
        WHERE Negocio_CC = '2R' ...outros filtros...
        Usuário: "Quais as vendas de carros em 2024?" 
        WHERE Negocio_CC = '4R' ...outros filtros...
    - Se o usuário especificar modelo, siga as regras de LIKE/UPPER para modelo normalmente.

CAMPOS CHAVES PARA CONSULTA:
- Temporais:
  • dta_venda (DATE): Data da venda (campo principal)
  • dta_operacao (DATE): Data da operação
  • EXTRACT(MONTH FROM dta_venda) as mes: Mês da venda (para agrupamentos)
  • EXTRACT(YEAR FROM dta_venda) as ano: Ano da venda (para agrupamentos)

- Dimensões:
  • modelo (STRING): Modelo do veículo, aqui aplica-se a regra do LIKE para buscas especificas dentro do WHERE
  • uf (STRING): Estado da loja
  • Loja (STRING): Entidade que realizou a venda, aqui aplica-se a regra do LIKE para buscas especificas dentro do WHERE
  • novo_usado (STRING): se o veículo é 'NOVO' ou 'USADO'
  • cidade (STRING): Cidade da loja, aqui aplica-se a regra do LIKE para buscas especificas dentro do WHERE
  • nome_vend (STRING): Vendedor
  • nome_cli (STRING): Cliente da venda
  
- Métricas:
  • val_total (FLOAT): Valor da venda
  • val_ipi (FLOAT): Valor do IPI
  • val_opcionais (FLOAT): Valor dos opcionais
  • QTE (INT): usado para somar sempre que for solicitado a quantidade de veículos vendidos

- Filtros adicionais:
  • des_situacao (STRING): Situação da venda
  • tipo_pagto (STRING): Tipo de pagamento
  
A tabela glinhares.delivery.drvy_VeiculosVendas possui os seguintes campos em sua totalidade:
- dta_operacao: Data da operação de venda.
- des_situacao: Situação da venda.
- razao_social: Razão social do cliente.
- razao_social_origem: Razão social de origem.
- uf: Unidade federativa (estado) do cliente.
- cep: CEP do cliente.
- bairro: Bairro do cliente.
- des_condicao: Condição da venda.
- tipo_pagto: Tipo de pagamento.
- val_ipi: Valor do IPI na venda.
- val_base_pis: Valor base do PIS.
- val_base_cofins: Valor base do COFINS.
- val_opcionais: Valor dos opcionais do veículo.
- Bonus_CaixaDagua: Valor do bônus "Caixa D'Água".
- cgccpf_CLI: CNPJ ou CPF do cliente.
- Val_Tradein: Valor do veículo usado na troca (trade-in).
- dta_Tradein: Data do trade-in.
- DEPRECIACAO_VEICULO: Valor da depreciação do veículo.
- dta_Cartao: Data da operação no cartão.
- Data_Cartao: Data do pagamento no cartão.
- DIAS_CARTAO: Quantidade de dias do cartão.
- Debito_Bandeira: Bandeira do cartão de débito.
- Debito_Valor: Valor pago no débito.
- Debito_Parcelas: Parcelas no débito.
- Debito_Taxa: Taxa do débito.
- Credito_Bandeira: Bandeira do cartão de crédito.
- Credito_Valor: Valor pago no crédito.
- Credito_Parcelas: Parcelas no crédito.
- Credito_Taxa: Taxa do crédito.
- chassi: Chassi do veículo.
- departamento: Código do departamento.
- situacao: Situação do veículo.
- modelo: Modelo do veículo.
- novo_usado: Indica se o veículo é novo ou usado.
- val_compra: Valor de compra do veículo.
- val_custo_contabil: Valor do custo contábil.
- dta_venda: Data da venda.
- val_floor_plan: Valor do floor plan.
- dta_entrada: Data de entrada do veículo.
- dta_fat_fabrica: Data de faturamento de fábrica.
- dta_compra_fabrica: Data de compra de fábrica.
- dta_entrada_estoque: Data de entrada em estoque.
- numero_nota_venda_direta: Número da nota de venda direta.
- empresa: Código da empresa.
- revenda_origem_VV: Código da revenda de origem (VV).
- veiculo: Descrição do veículo.
- revenda: Código da revenda.
- empresa_origem: Código da empresa de origem.
- revenda_origem: Código da revenda de origem.
- cidade: Cidade da loja
- negocio_CC: Tipo de negócio (2R para motos, 4R para carros)
EXEMPLOS DE CONSULTA COM MÚLTIPLAS DIMENSÕES:

1. Top 5 vendedores por mês (2 dimensões):
{
  "select": ["EXTRACT(MONTH FROM dta_venda) AS mes", "nome_vend", "SUM(QTE) AS total"],
  "where": "EXTRACT(YEAR FROM dta_venda) = 2025",
  "group_by": ["mes", "nome_vend"],
  "order_by": ["mes", "total DESC"],
  "qualify": "ROW_NUMBER() OVER (PARTITION BY mes ORDER BY total DESC) <= 5"
}

2. Top 3 modelos por estado e mês (3 dimensões):
{
  "select": ["EXTRACT(MONTH FROM dta_venda) AS mes", "uf", "modelo", "SUM(QTE) AS total"],
  "group_by": ["mes", "uf", "modelo"],
  "order_by": ["mes", "uf", "total DESC"],
  "qualify": "ROW_NUMBER() OVER (PARTITION BY mes, uf ORDER BY total DESC) <= 3"
}
"""
