
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
    sql_template: Optional[str] = None
    parameters_template: Optional[dict] = None
    example: Optional[str] = None
    use_cases: Optional[List[str]] = None
    embedding: Optional[List[float]] = None


class SQLPatternRAG:
    """Sistema RAG para padrões SQL/BigQuery"""
    
    def __init__(self, patterns_file: str = "sql_patterns.json", cache_db: str = "sql_patterns_cache.db"):
        self.patterns_file = patterns_file
        self.cache_db_path = cache_db
        self.patterns: Dict[str, SQLPattern] = {}
        self.annoy_dim = 384  # all-MiniLM-L6-v2
        self.annoy_index_path = self.cache_db_path.replace('.db', '.ann')
        self.annoy_index = None
        self._annoy_metadata = {}  # idx -> pattern_id
        self.load_patterns()
    
    def load_patterns(self):
        """Carrega padrões SQL do arquivo JSON e inicializa Annoy do zero, sempre que o sistema inicia. Persiste metadados."""
        try:
            import os, json
            from annoy import AnnoyIndex
            import numpy as np
            self.annoy_meta_path = self.cache_db_path.replace('.db', '.meta.json')
            # Remove arquivos antigos para garantir index limpo
            if os.path.exists(self.annoy_index_path):
                os.remove(self.annoy_index_path)
            if os.path.exists(self.annoy_meta_path):
                os.remove(self.annoy_meta_path)
            with open(self.patterns_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Converte padrões para objetos SQLPattern
            sql_patterns = data.get('sql_patterns', {})
            annoy_index = AnnoyIndex(self.annoy_dim, 'angular')
            annoy_metadata = {}
            idx = 0
            for pattern_id, pattern_data in sql_patterns.items():
                # keywords e use_cases: garantir que são listas
                keywords = pattern_data.get('keywords', [])
                if not isinstance(keywords, list):
                    keywords = [keywords] if keywords else []
                use_cases = pattern_data.get('use_cases', [])
                if not isinstance(use_cases, list):
                    use_cases = [use_cases] if use_cases else []

                # function_call_example: pode ser dict, list, ou outro
                fc = pattern_data.get('function_call_example')
                function_call_str = None
                if fc is not None:
                    if isinstance(fc, (dict, list)):
                        try:
                            function_call_str = json.dumps(fc, ensure_ascii=False)
                        except Exception:
                            function_call_str = str(fc)
                    else:
                        function_call_str = str(fc)

                self.patterns[pattern_id] = SQLPattern(
                    pattern_id=pattern_id,
                    description=pattern_data.get('description', ''),
                    keywords=keywords,
                    pattern_type=pattern_data.get('pattern_type', ''),
                    sql_template=pattern_data.get('sql_template'),
                    parameters_template=pattern_data.get('parameters_template'),
                    example=function_call_str,
                    use_cases=use_cases
                )
                # Gera embedding e adiciona ao Annoy
                emb = self._generate_embedding(pattern_data.get('description', ''))
                if emb and len(emb) == self.annoy_dim:
                    annoy_index.add_item(idx, np.array(emb, dtype=np.float32))
                    annoy_metadata[idx] = {
                        "pattern_id": pattern_id,
                        "description": pattern_data.get('description', ''),
                        "pattern_type": pattern_data.get('pattern_type', ''),
                    }
                    idx += 1
            if idx > 0:
                annoy_index.build(10)
                annoy_index.save(self.annoy_index_path)
                with open(self.annoy_meta_path, 'w', encoding='utf-8') as f:
                    json.dump(annoy_metadata, f, ensure_ascii=False)
                self.annoy_index = annoy_index
                self._annoy_metadata = annoy_metadata
            print(f"Carregados {len(self.patterns)} padrões SQL e Annoy index inicializado")
        except Exception as e:
            print(f"Erro ao carregar padrões SQL: {e}")
            self.patterns = {}

    def _generate_embedding(self, text: str) -> List[float]:
        """Gera embedding para um texto usando sentence-transformers"""
        if not hasattr(self, 'st_model') or not getattr(self, '_has_st', False):
            return []
        try:
            emb = self.st_model.encode([text], show_progress_bar=False)
            return emb[0].tolist() if hasattr(emb[0], 'tolist') else list(emb[0])
        except Exception as e:
            return []
    
    def identify_sql_pattern(self, user_query: str, min_score: float = 1.5) -> List[Tuple[str, float]]:
        """
        Identifica padrões SQL mais relevantes usando Annoy para busca vetorial.
        """
        from annoy import AnnoyIndex
        import numpy as np
        query_emb = self._generate_embedding(user_query)
        if not query_emb or not self.annoy_index:
            return []
        idxs, dists = self.annoy_index.get_nns_by_vector(np.array(query_emb, dtype=np.float32), 5, include_distances=True)
        results = []
        for idx, dist in zip(idxs, dists):
            pattern_id = self._annoy_metadata.get(idx)
            if pattern_id:
                score = max(0, 2.5 - dist)  # Score artificial baseado na distância angular
                if score >= min_score:
                    results.append((pattern_id, score))
        return results
    
    def get_sql_guidance(self, user_query: str, top_k: int = 2, min_score: float = 1.5) -> str:
        """
        Retorna orientações SQL específicas para a pergunta do usuário
        Agora exibe function_call_example como string ao invés de sql_example.
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
            # Exibe function_call_example como string
            if pattern.example is not None:
                context_parts.append(f"   Function Call Example: {pattern.example}")
                if pattern.example is not None:
                    context_parts.append(f"   Function Call Example: {pattern.example}")
                else:
                    context_parts.append("   Function Call Example: None")
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
    Função utilitária para obter orientações SQL para uma pergunta usando singleton
    """
    sql_rag = get_sql_rag_instance()
    return sql_rag.get_sql_guidance(user_query)

# Instância global
_sql_rag_instance = None

def get_sql_rag_instance() -> SQLPatternRAG:
    """Retorna instância singleton do SQL RAG"""
    global _sql_rag_instance
    if _sql_rag_instance is None:
        print("🔄 Inicializando SQLPatternRAG singleton...")
        _sql_rag_instance = SQLPatternRAG()
        print("✅ SQLPatternRAG inicializado!")
    return _sql_rag_instance