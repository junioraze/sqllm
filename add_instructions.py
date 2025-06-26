COMPARACAO_INSTRUCOES = """\n
INSTRUÇÕES PARA ANÁLISE DE DADOS:
1. Você tem liberdade para criar consultas SQL completas
2. Pode usar qualquer campo da tabela
3. Pode criar funções de agregação personalizadas
4. Certifique-se de incluir filtros temporais quando relevante
5. Para análises com múltiplas dimensões (ex: top N por grupo), use QUALIFY ROW_NUMBER() OVER (PARTITION BY ...)
6. Se o usuário solicitar visualização gráfica, inclua no final da resposta:
   GRAPH-TYPE: [tipo] | X-AXIS: [coluna] | Y-AXIS: [coluna] | COLOR: [coluna]
   Tipos suportados: bar, line
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
5. Campos no QUALIFY devem estar no SELECT
6. Caso o usuário não especifique um Ranking, use o padrão de 5 para TOP N
   - Exemplo para o ponto 6: 
                  Se ele solicitar algo semelhante a "Quais os vendedores com melhor desempenho de vendas em 2025?"
                  Subentenda-se que ele quer o TOP 5 de vendedores
                  Perceba que a pergunta pode vir de diversas outras formas, como "Quais as lojas que mais venderam em 2025?"
                  Ou "Quais os modelos mais vendidos em 2025?"
                  Todos os casos qualificam-se como TOP 5 caso um top N não seja especificado
                  
CAMPOS CHAVES PARA CONSULTA:
- Temporais:
  • dta_venda (DATE): Data da venda (campo principal)
  • dta_operacao (DATE): Data da operação
  • EXTRACT(MONTH FROM dta_venda) as mes: Mês da venda (para agrupamentos)
  • EXTRACT(YEAR FROM dta_venda) as ano: Ano da venda (para agrupamentos)

- Dimensões:
  • modelo (STRING): Modelo do veículo
  • uf (STRING): Estado da loja
  • Loja (STRING): Entidade que realizou a venda
  • novo_usado (STRING): se o veículo é 'NOVO' ou 'USADO'
  • cidade (STRING): Cidade da loja
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
