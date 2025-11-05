"""
Query Validator com Retry Automático
====================================

Pipeline de validação de queries SQL geradas pelo Gemini:
1. Valida sintaxe com sqlparse
2. Se falhar, envia para Gemini refinar (até 2 tentativas)
3. Só retorna query completa e válida
"""

import sqlparse
import re
import json
from typing import Dict, Tuple, Optional
import google.generativeai as genai
from config.settings import MODEL_NAME
from llm_handlers.prompt_rules import get_sql_refinement_instruction

class QueryValidator:
    """Valida e refina queries SQL com retry automático"""
    
    def __init__(self, model=None, max_retries: int = 2):
        self.model = model
        self.max_retries = max_retries
        self.validation_history = []
    
    def is_query_complete(self, query: str) -> bool:
        """
        Verifica se a query tem CTEs mas falta SELECT final.
        
        Retorna: True se query está COMPLETA (pronta para executar)
        """
        query_upper = query.upper().strip()
        
        # Query sem WITH é sempre simples (SELECT ... FROM ...)
        if 'WITH ' not in query_upper:
            return 'SELECT' in query_upper and 'FROM' in query_upper
        
        # Se tem WITH, precisa terminar com SELECT ... FROM
        # Procura pelo padrão: ") SELECT ... FROM"
        pattern = r'\)\s*SELECT\s+.+FROM\s+\w+\s*(?:WHERE|ORDER BY|;|$)'
        has_final_select = re.search(pattern, query_upper, re.DOTALL) is not None
        
        return has_final_select
    
    def validate_syntax(self, query: str) -> Tuple[bool, Optional[str]]:
        """
        Valida sintaxe SQL usando sqlparse.
        
        Retorna: (is_valid, error_message)
        """
        try:
            # Remove comentários antes de validar
            query_clean = re.sub(r'--.*?(\n|$)', '', query)
            query_clean = re.sub(r'/\*.*?\*/', '', query_clean, flags=re.DOTALL)
            
            parsed = sqlparse.parse(query_clean)
            
            if not parsed:
                return False, "Query vazia ou inválida."
            
            # Verifica tokens básicos
            tokens = [t for t in parsed[0].tokens if not t.is_whitespace]
            if not tokens:
                return False, "Nenhum token SQL encontrado."
            
            # Verifica estrutura básica
            first_keyword = str(tokens[0]).upper().strip()
            if first_keyword not in ('WITH', 'SELECT', 'INSERT', 'UPDATE', 'DELETE'):
                return False, f"Primeiro token inválido: {first_keyword}"
            
            # Se tem WITH, verifica se há SELECT após CTEs
            if first_keyword == 'WITH':
                if not self.is_query_complete(query_clean):
                    return False, "Query tem CTEs mas falta SELECT final."
            
            return True, None
            
        except Exception as e:
            return False, f"Erro ao parsear SQL: {str(e)}"
    
    def auto_complete_query(self, query: str) -> str:
        """
        Se a query tem CTEs mas falta SELECT final, adiciona automaticamente.
        
        Exemplo:
            Input: "WITH cte_x AS (...), cte_y AS (...)"
            Output: "WITH cte_x AS (...), cte_y AS (...) SELECT * FROM cte_y"
        """
        query_upper = query.upper().strip()
        
        # Se não tem WITH, nada a completar
        if 'WITH ' not in query_upper:
            return query
        
        # Se já está completo, retorna como está
        if self.is_query_complete(query):
            return query
        
        # Tenta extrair o nome da última CTE
        # Procura por padrão: "cte_name AS (...)"
        cte_pattern = r'(\w+)\s+AS\s*\('
        matches = list(re.finditer(cte_pattern, query, re.IGNORECASE))
        
        if not matches:
            return query  # Não conseguiu extrair, retorna original
        
        # Pega o último CTE (último match)
        last_cte_name = matches[-1].group(1)
        
        # Adiciona SELECT * FROM ultima_cte
        completed_query = f"{query.rstrip()} SELECT * FROM {last_cte_name}"
        
        print(f"[AUTO-COMPLETE] Query incompleta detectada. Adicionado: SELECT * FROM {last_cte_name}")
        return completed_query
    
    def validate_query(self, query: str, user_question: str = "") -> Dict:
        """
        Valida query e retorna resultado estruturado.
        
        Retorna dict com:
        - is_valid (bool)
        - query (str): query validada/corrigida
        - errors (list): lista de erros encontrados
        - auto_completed (bool): se foi auto-completada
        """
        result = {
            "is_valid": False,
            "query": query,
            "errors": [],
            "auto_completed": False,
            "validation_step": "initial"
        }
        
        # STEP 1: Verifica se está completo
        if not self.is_query_complete(query):
            print("[VALIDATION] Query incompleta detectada (falta SELECT final)")
            result["errors"].append("Query incompleta: falta SELECT final após CTEs")
            
            # Tenta auto-completar
            try:
                completed = self.auto_complete_query(query)
                if completed != query:
                    result["query"] = completed
                    result["auto_completed"] = True
                    query = completed
                    print("[AUTO-COMPLETE] ✅ Query auto-completada com sucesso")
            except Exception as e:
                result["errors"].append(f"Erro ao auto-completar: {str(e)}")
        
        # STEP 2: Valida sintaxe com sqlparse
        is_valid, error_msg = self.validate_syntax(query)
        result["validation_step"] = "syntax_check"
        
        if not is_valid:
            print(f"[VALIDATION] ❌ Erro de sintaxe: {error_msg}")
            result["errors"].append(f"Erro de sintaxe: {error_msg}")
            result["is_valid"] = False
        else:
            print("[VALIDATION] ✅ Sintaxe SQL válida")
            result["is_valid"] = True
            result["validation_step"] = "passed"
        
        return result
    
    def refine_with_gemini(self, 
                          query: str, 
                          error_message: str,
                          user_question: str,
                          retry_count: int = 1) -> Optional[str]:
        """
        Envia query com erro para Gemini refinar.
        
        Usado quando validação falha - Gemini recebe contexto do erro e monta query corrigida.
        
        Retorna: query refinada ou None se falhar
        """
        if not self.model:
            print("[REFINE] ❌ Modelo não inicializado")
            return None
        
        print(f"\n[REFINE] Tentativa {retry_count}/{self.max_retries} de refino com Gemini")
        print(f"[REFINE] Erro encontrado: {error_message}")
        
        # Monta prompt de refino
        refinement_prompt = f"""
Você é um especialista em SQL BigQuery que refina queries problemáticas.

PERGUNTA ORIGINAL DO USUÁRIO:
{user_question}

QUERY COM ERRO:
```sql
{query}
```

ERRO ENCONTRADO:
{error_message}

SUAS TAREFAS:
1. Analisar o erro na query
2. Manter a mesma lógica e intenção da query original
3. Corrigir APENAS os problemas de sintaxe ou estrutura
4. Garantir que a query esteja COMPLETA (WITH cte_name AS (...) SELECT ... FROM cte_name)
5. NÃO ADICIONAR comentários SQL (-- ou /* */)
6. Retornar APENAS a query SQL corrigida, sem explicações

QUERY CORRIGIDA:
"""
        
        try:
            response = self.model.generate_content(refinement_prompt)
            
            if hasattr(response, 'text') and response.text:
                refined_query = response.text.strip()
                
                # Remove markdown code blocks se presentes
                refined_query = re.sub(r'```sql\n?', '', refined_query)
                refined_query = re.sub(r'```\n?', '', refined_query)
                refined_query = refined_query.strip()
                
                print(f"[REFINE] ✅ Query refinada recebida do Gemini")
                return refined_query
            else:
                print("[REFINE] ❌ Resposta vazia do Gemini")
                return None
                
        except Exception as e:
            print(f"[REFINE] ❌ Erro ao chamar Gemini: {str(e)}")
            return None
    
    def validate_and_refine(self, 
                           query: str,
                           user_question: str = "",
                           gemini_model = None) -> Dict:
        """
        Pipeline completo: valida + tenta refinar automaticamente (até 2 vezes).
        
        Retorna dict com:
        - is_valid (bool)
        - query (str): query final
        - retry_count (int): quantas tentativas foram feitas
        - history (list): histórico de tentativas
        """
        self.model = gemini_model or self.model
        
        history = []
        current_query = query
        
        for attempt in range(self.max_retries + 1):  # +1 para validação inicial
            print(f"\n{'='*60}")
            print(f"[ATTEMPT {attempt + 1}] Validando query...")
            print(f"{'='*60}")
            
            # Valida query atual
            validation = self.validate_query(current_query, user_question)
            history.append({
                "attempt": attempt + 1,
                "query": current_query,
                "validation": validation
            })
            
            if validation["is_valid"]:
                print(f"\n✅ Query VÁLIDA na tentativa {attempt + 1}")
                return {
                    "is_valid": True,
                    "query": validation["query"],
                    "retry_count": attempt,
                    "history": history,
                    "success_message": f"Query validada com sucesso em {attempt + 1} tentativa(s)"
                }
            
            # Se falhou e temos tentativas restantes, pede refino ao Gemini
            if attempt < self.max_retries:
                error_msg = "; ".join(validation["errors"])
                refined = self.refine_with_gemini(
                    current_query,
                    error_msg,
                    user_question,
                    attempt + 1
                )
                
                if refined and refined != current_query:
                    current_query = refined
                    continue
                else:
                    print(f"[REFINE] ❌ Não conseguiu refinar, encerrando")
                    break
        
        # Se chegou aqui, falhou em todas as tentativas
        print(f"\n❌ Query NÃO VALIDOU após {self.max_retries + 1} tentativas")
        return {
            "is_valid": False,
            "query": current_query,
            "retry_count": self.max_retries,
            "history": history,
            "error_message": f"Query falhou na validação após {self.max_retries} tentativas de refino",
            "final_errors": validation["errors"]
        }


# Função utilitária para uso rápido
def validate_and_build_query(query: str, 
                             user_question: str = "",
                             gemini_model = None,
                             max_retries: int = 2) -> Dict:
    """
    Função helper para validar e refinar query em uma única chamada.
    
    Uso:
        result = validate_and_build_query(query, user_question, model)
        if result['is_valid']:
            final_query = result['query']
            # executar no BigQuery
        else:
            print(f"Erro: {result['error_message']}")
    """
    validator = QueryValidator(model=gemini_model, max_retries=max_retries)
    return validator.validate_and_refine(query, user_question, gemini_model)
