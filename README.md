# SQL Talk Extended Conjecto: Natural Language to BigQuery with Gemini's Function Calling

|           |                                                     |
| --------- | --------------------------------------------------- |
| Author(s) | [Kristopher Overholt](https://github.com/koverholt) |
| Extender | [Helmiton Junior](https://github.com/junioraze)

# Consultas Inteligentes de Vendas de Veículos

Este projeto é uma aplicação Streamlit que permite ao usuário consultar, comparar e analisar dados de vendas de veículos utilizando linguagem natural. O sistema utiliza o modelo Gemini (Google Generative AI) com function calling para interpretar perguntas, gerar queries SQL dinâmicas para BigQuery e retornar respostas analíticas e explicativas, inclusive para comparações temporais e agrupamentos.

## Principais Funcionalidades

- **Consultas por linguagem natural:** Pergunte em português sobre vendas, modelos, regiões, períodos, etc.
- **Comparações temporais:** Compare períodos, anos, meses, UFs, modelos ou lojas facilmente.
- **Agrupamentos dinâmicos:** Agrupe resultados por ano, mês, UF, modelo ou loja.
- **Respostas analíticas:** O modelo Gemini refina e explica os resultados, entregando insights claros e estruturados.
- **Interface amigável:** Visualização de perguntas e respostas em formato de chat, com histórico.

## Como Funciona

1. O usuário faz uma pergunta sobre vendas de veículos na interface Streamlit.
2. O Gemini interpreta a pergunta e, se necessário, solicita uma consulta SQL via function calling.
3. O backend executa a query no BigQuery e retorna os dados.
4. O resultado é enviado de volta ao Gemini, junto com a pergunta e as instruções do sistema, para que ele gere uma resposta analítica, comparativa e didática.
5. A resposta final é exibida ao usuário, junto com a tabela de dados.

## Requisitos

- Python 3.9+
- Conta Google Cloud com acesso ao BigQuery
- Credenciais de serviço do Google Cloud (JSON)
- Dependências Python (veja abaixo)

## Instalação

1. Clone este repositório:
    ```bash
    git clone https://github.com/seu-usuario/seu-repo.git
    cd seu-repo/python/sqllm
    ```

2. Instale as dependências:
    ```bash
    pip install -r requirements.txt
    ```

3. Configure as variáveis de ambiente:
    - Crie um arquivo `.env` na raiz do projeto.  
      **O arquivo `.env` já está configurado para não expor nenhuma informação sensível.**  
      Exemplo de conteúdo:
      ```
      GOOGLE_APPLICATION_CREDENTIALS=/caminho/para/seu/arquivo-credencial.json
      ```

4. Ajuste o arquivo `add_instructions.py` conforme necessário para refletir as regras e descrições dos campos da sua tabela.

## Como Executar

```bash
streamlit run app.py
```

Acesse a interface no navegador pelo endereço exibido no terminal (geralmente http://localhost:8501).

## Exemplos de Perguntas

- `Qual o total vendido em 2024?`
- `Quais os modelos mais vendidos por UF?`
- `Total vendido por UF e mês em 2023`
- `Total vendido por modelo em janeiro de 2024 na loja 5`
- `Compare as vendas de 2023 e 2024 por mês`

## Estrutura do Projeto

📂 sqllm/
├── 📄 __init__.py
├── 📄 add_instructions.py # Instruções extras
├── 📄 main.py             # Ponto de entrada principal
├── 📄 database.py         # Funções de banco de dados
├── 📄 gemini_handler.py   # Lógica de interação com o Gemini
├── 📄 utils.py            # Funções utilitárias
└── 📄 config.py           # Configurações e constantes

## Observações Técnicas

- O modelo Gemini é utilizado com function calling para garantir precisão na geração de queries SQL.
- O sistema só permite agrupamentos e filtros por ano, mês, UF, modelo e loja, conforme regras de negócio.
- O resultado das queries é enviado de volta ao Gemini para refino e explicação, garantindo respostas analíticas e didáticas.
- O histórico do chat é mantido para melhor experiência do usuário.
- O arquivo `.env` está preparado para não expor dados sensíveis.

## Contribuição

Contribuições são bem-vindas! Abra uma issue ou envie um pull request.

## Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](../LICENSE) para mais detalhes.

---

Se tiver dúvidas ou sugestões, fique à vontade para abrir uma issue ou entrar em contato.