#!/usr/bin/env python3
"""
Script para testar a formatação de IA em todas as variações
"""

from utils import format_text_with_ia_highlighting

def test_ia_formatting():
    """Testa todas as variações de IA"""
    
    test_cases = [
        "Sistema de IA para análise",
        "Assistente com ia avançada", 
        "Tecnologia Ia moderna",
        "Sistema iA inteligente",
        "IA e ia funcionando juntos",
        "Login IA Sistema",
        "Faça sua pergunta para a IA",
        "Sistema de IA, ia, Ia e iA funcionando"
    ]
    
    print("=== TESTE DE FORMATAÇÃO IA ===\n")
    
    for i, text in enumerate(test_cases, 1):
        formatted = format_text_with_ia_highlighting(text)
        print(f"Teste {i}:")
        print(f"Original: {text}")
        print(f"Formatado: {formatted}")
        print("-" * 50)

if __name__ == "__main__":
    test_ia_formatting()
