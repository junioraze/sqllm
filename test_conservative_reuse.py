#!/usr/bin/env python3
"""
Teste da nova filosofia conservadora de reutilização de dados
"""

def test_reuse_philosophy():
    """
    Testa cenários de reutilização com a nova filosofia conservadora
    """
    
    print("🧪 Testando nova filosofia de reutilização conservadora...")
    
    # Cenários que DEVEM reutilizar (casos simples)
    should_reuse_cases = [
        {
            "previous": "Demonstre os modelos vendidos no ceará em 2023",
            "current": "Gere um Excel desses dados",
            "reason": "Exportação dos mesmos dados"
        },
        {
            "previous": "Vendas por modelo em 2023",
            "current": "Qual modelo teve mais vendas?",
            "reason": "Análise textual dos dados existentes"
        },
        {
            "previous": "Top 10 vendedores de janeiro",
            "current": "Crie um gráfico em barras desses dados",
            "reason": "Visualização dos dados existentes"
        },
        {
            "previous": "Faturamento por região",
            "current": "Resuma esses resultados",
            "reason": "Reformulação dos dados existentes"
        }
    ]
    
    # Cenários que NÃO devem reutilizar (casos complexos)
    should_not_reuse_cases = [
        {
            "previous": "Vendas de carros em 2023",
            "current": "Compare com as vendas de 2024",
            "reason": "Requer novos dados (2024)"
        },
        {
            "previous": "Vendas no Ceará",
            "current": "Some com as vendas de São Paulo",
            "reason": "Requer novos dados (SP) e agregação"
        },
        {
            "previous": "Todos os modelos vendidos",
            "current": "Mostre apenas os modelos Honda",
            "reason": "Filtro diferente, melhor nova consulta SQL"
        },
        {
            "previous": "Vendas mensais de 2023",
            "current": "Calcule a média trimestral",
            "reason": "Manipulação/agregação de dados"
        },
        {
            "previous": "Top 5 vendedores",
            "current": "Agora mostre os piores 5",
            "reason": "Critério diferente, requer nova consulta"
        }
    ]
    
    print("\n✅ CASOS QUE DEVEM REUTILIZAR (simples):")
    for i, case in enumerate(should_reuse_cases, 1):
        print(f"{i}. Anterior: '{case['previous']}'")
        print(f"   Atual: '{case['current']}'")
        print(f"   ✅ REUTILIZAR: {case['reason']}\n")
    
    print("❌ CASOS QUE NÃO DEVEM REUTILIZAR (complexos):")
    for i, case in enumerate(should_not_reuse_cases, 1):
        print(f"{i}. Anterior: '{case['previous']}'")
        print(f"   Atual: '{case['current']}'")
        print(f"   ❌ NOVA CONSULTA: {case['reason']}\n")
    
    print("🎯 FILOSOFIA IMPLEMENTADA:")
    print("- ✅ Reutilização conservadora: apenas exportação e análise textual")
    print("- ❌ Nova consulta: manipulação, agregação, filtros diferentes")
    print("- 🧠 Contexto do chat: permite que Gemini entenda comparações/agregações")
    print("- ⚡ Performance: evita complexidade desnecessária no frontend")
    
    print("\n🚀 Sistema configurado para ser conservador e eficiente!")

if __name__ == "__main__":
    test_reuse_philosophy()
