# add_instructions.py
COMPARACAO_INSTRUCOES = """\n
INSTRUÇÕES PARA ANÁLISE DE DADOS:
1. Você tem liberdade para criar consultas SQL completas
2. Pode usar qualquer campo da tabela
3. Pode criar funções de agregação personalizadas
4. Certifique-se de incluir filtros temporais quando relevante
5. Se o usuário solicitar visualização gráfica, inclua no final da resposta:
   GRAPH-TYPE: [tipo] | X-AXIS: [coluna] | Y-AXIS: [coluna]
   Tipos suportados: bar, line, pie
"""

CAMPOS_DESCRICAO = """\n
EXEMPLOS DE PARÂMETROS VÁLIDOS:
- select: ["modelo", "SUM(QTE) as total_vendido"]
- where: "dta_venda BETWEEN '2025-01-01' AND '2025-12-31'"
- group_by: ["modelo", "uf"]  # NUNCA inclua funções aqui!
- order_by: ["total_vendido DESC"] # NUNCA inclua funções aqui!
- limit: 10 #ESTE CAMPO DEVE SER UM NÚMERO INTEIRO

CAMPOS CHAVES PARA CONSULTA:
- Temporais:
  • dta_venda (DATE): Data da venda (campo principal)
  • dta_operacao (DATE): Data da operação

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
"""
