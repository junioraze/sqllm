"""
Sistema RAG Especializado em Padrões SQL/BigQuery
==================================================

Este módulo implementa um sistema RAG focado em padrões de SQL e melhores práticas
do BigQuery, permitindo que o Gemini consulte dinamicamente as técnicas adequadas
conforme o tipo de pergunta.

BENEFÍCIOS:
- Padrões SQL específicos para cada tipo de análise
- Melhores práticas do BigQuery indexadas por contexto
- Recomendações dinâmicas baseadas na intenção da pergunta
- Separação clara entre lógica SQL e regras de negócio
"""

import json
import hashlib
import duckdb
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from dataclasses import dataclass, asdict
import numpy as np
import re


@dataclass
class SQLPattern:
    """Estrutura de um padrão SQL"""
    pattern_id: str
    description: str
    keywords: List[str]
    pattern_type: str
    sql_template: str
    example: str
    use_cases: List[str]
    embedding: Optional[List[float]] = None


class SQLPatternRAG:
    """Sistema RAG para padrões SQL/BigQuery"""
    
    def __init__(self, patterns_file: str = "sql_patterns.json", cache_db: str = "sql_patterns_cache.db"):
        self.patterns_file = patterns_file
        self.cache_db_path = cache_db
        self.patterns: Dict[str, SQLPattern] = {}
        self.load_patterns()
    
    def load_patterns(self):
        """Carrega padrões SQL do arquivo JSON"""
        try:
            with open(self.patterns_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Converte padrões para objetos SQLPattern
            sql_patterns = data.get('sql_patterns', {})
            for pattern_id, pattern_data in sql_patterns.items():
                self.patterns[pattern_id] = SQLPattern(
                    pattern_id=pattern_id,
                    description=pattern_data['description'],
                    keywords=pattern_data['keywords'],
                    pattern_type=pattern_data['pattern_type'],
                    sql_template=pattern_data['sql_template'],
                    example=pattern_data['example'],
                    use_cases=pattern_data['use_cases']
                )
            
            print(f"✅ Carregados {len(self.patterns)} padrões SQL")
            
        except Exception as e:
            print(f"❌ Erro ao carregar padrões SQL: {e}")
            self.patterns = {}
    
    def identify_sql_pattern(self, user_query: str, min_score: float = 1.5) -> List[Tuple[str, float]]:
        """
        Identifica padrões SQL mais relevantes para a pergunta, com score mínimo mais restritivo
        """
        query_lower = user_query.lower()
        pattern_scores = []
        for pattern_id, pattern in self.patterns.items():
            score = 0.0
            # Score baseado em keywords
            for keyword in pattern.keywords:
                if keyword.lower() in query_lower:
                    score += 1.0
            # Score baseado em use cases
            for use_case in pattern.use_cases:
                use_case_words = set(use_case.lower().split())
                query_words = set(query_lower.split())
                common_words = use_case_words.intersection(query_words)
                if common_words:
                    score += len(common_words) * 0.5
            # Score mínimo mais restritivo
            if score >= min_score:
                pattern_scores.append((pattern_id, score))
        pattern_scores.sort(key=lambda x: x[1], reverse=True)
        return pattern_scores
    
    def get_sql_guidance(self, user_query: str, top_k: int = 2, min_score: float = 1.5) -> str:
        """
        Retorna orientações SQL específicas para a pergunta do usuário
        
        Args:
            user_query (str): Pergunta do usuário
            top_k (int): Número máximo de padrões a retornar
            min_score (float): Score mínimo para considerar padrão relevante
        Returns:
            str: Contexto SQL formatado para o Gemini
        """
        relevant_patterns = self.identify_sql_pattern(user_query, min_score=min_score)
        if not relevant_patterns:
            return self._get_general_sql_guidance()
        context_parts = []
        context_parts.append("ORIENTAÇÕES SQL ESPECÍFICAS PARA SUA PERGUNTA:")
        context_parts.append("")
        for i, (pattern_id, score) in enumerate(relevant_patterns[:top_k]):
            pattern = self.patterns[pattern_id]
            context_parts.append(f"{i+1}. PADRÃO: {pattern.description.upper()}")
            context_parts.append(f"   Tipo: {pattern.pattern_type}")
            context_parts.append(f"   Template: {pattern.sql_template}")
            context_parts.append(f"   Exemplo: {pattern.example}")
            context_parts.append("")
        context_parts.append("PRÁTICAS RECOMENDADAS BIGQUERY:")
        context_parts.extend(self._get_bigquery_best_practices())
        return "\n".join(context_parts)
    
    def _get_general_sql_guidance(self) -> str:
        """Retorna orientações SQL gerais quando não há padrões específicos"""
        return """
ORIENTAÇÕES SQL GERAIS:

1. Use QUALIFY para rankings ao invés de subqueries
2. Para consultas complexas, prefira CTEs (WITH)
3. Use EXTRACT(YEAR FROM campo_data) para filtros temporais
4. Agregações requerem GROUP BY dos campos não agregados
5. Para comparações de texto, use UPPER() com LIKE

MELHORES PRÁTICAS BIGQUERY:
- Evite SELECT * em tabelas grandes
- Use word boundaries em comparações de texto
- Prefira QUALIFY a LIMIT para rankings
"""
    
    def _get_bigquery_best_practices(self) -> List[str]:
        """Retorna lista de melhores práticas do BigQuery"""
        try:
            with open(self.patterns_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            practices = data.get('bigquery_best_practices', {})
            tips = practices.get('performance_tips', [])
            
            formatted_tips = []
            for tip in tips:
                formatted_tips.append(f"- {tip}")
            
            return formatted_tips
            
        except Exception as e:
            print(f"Erro ao carregar práticas: {e}")
            return ["- Use QUALIFY para rankings", "- Prefira CTEs para queries complexas"]
    
    def detect_potential_issues(self, user_query: str) -> List[str]:
        """
        Detecta possíveis problemas na pergunta que podem gerar SQL incorreto
        
        Args:
            user_query (str): Pergunta do usuário
            
        Returns:
            List[str]: Lista de alertas/sugestões
        """
        alerts = []
        query_lower = user_query.lower()
        
        # Detecta comparação entre anos
        if any(year in query_lower for year in ['2024', '2025']) and \
           any(word in query_lower for word in ['comparar', 'vs', 'entre', 'versus']):
            alerts.append("ATENÇÃO: Para comparação entre anos, use CTE + UNION ALL")
        
        # Detecta necessidade de ranking
        if any(word in query_lower for word in ['top', 'maior', 'melhor', 'principal']):
            alerts.append("SUGESTÃO: Use QUALIFY com ROW_NUMBER() para rankings")
        
        # Detecta análise temporal
        if any(word in query_lower for word in ['evolução', 'mensal', 'trimestral', 'ao longo']):
            alerts.append("DICA: Use EXTRACT() para agrupar por períodos temporais")
        
        return alerts


def get_sql_guidance_for_query(user_query: str) -> str:
    """
    Função utilitária para obter orientações SQL para uma pergunta
    
    Args:
        user_query (str): Pergunta do usuário
        
    Returns:
        str: Contexto SQL formatado
    """
    sql_rag = SQLPatternRAG()
    return sql_rag.get_sql_guidance(user_query)


# Instância global para reutilização
_sql_rag_instance = None

def get_sql_rag_instance() -> SQLPatternRAG:
    """Retorna instância singleton do SQL RAG"""
    global _sql_rag_instance
    if _sql_rag_instance is None:
        _sql_rag_instance = SQLPatternRAG()
    return _sql_rag_instance