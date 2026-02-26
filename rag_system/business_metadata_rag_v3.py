"""
Business Metadata RAG v3 - Multi-Factor Table Scoring
Sistema de ranking inteligente de tabelas com 5 dimensões de análise

Melhoria sobre v2: Scoring multi-dimensional para acurácia 95%+
"""

import os
import json
import unicodedata
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime
import re

try:
    from sentence_transformers import SentenceTransformer, util
    _HAS_ST = True
except ImportError:
    _HAS_ST = False


def normalize_text(text: str) -> str:
    """Remove acentos e normaliza texto para matching"""
    if not text:
        return ""
    text = unicodedata.normalize('NFD', text.lower())
    return ''.join(c for c in text if unicodedata.category(c) != 'Mn')


@dataclass
class TableScore:
    """Resultado de pontuação de tabela"""
    table_name: str
    final_score: float
    semantic_score: float
    keyword_score: float
    domain_score: float
    temporal_score: float
    metric_score: float
    confidence: str
    explanation: str = ""


class BusinessMetadataRAGv3:
    """RAG especializado com Multi-Factor Table Scoring"""
    
    def __init__(self, config_path: str = "tables_config.json"):
        self.config_path = self._find_config_path(config_path)
        self.config = self._load_config()
        self.table_metadata = self._extract_metadata()
        
        if _HAS_ST:
            self.embedder = SentenceTransformer("all-MiniLM-L6-v2", device='cpu')
            print("[RAG v3] Modelo sentence-transformers carregado ✅")
            self._precompute_embeddings()
        else:
            print("[RAG v3] Aviso: sentence-transformers não disponível, usando fallback")
            self.embedder = None
    
    def _find_config_path(self, config_path: str) -> str:
        """Procura config em múltiplas localizações (multi-path lookup)"""
        possible_paths = [
            config_path,  # Path fornecido
            os.path.abspath(config_path),  # Caminho absoluto do fornecido
            os.path.join(os.path.dirname(__file__), "..", "config", "tables_config.json"),  # config/
            os.path.join(os.path.dirname(__file__), "..", "tables_config.json"),  # raiz/
            os.path.join(os.getcwd(), "config", "tables_config.json"),  # cwd/config/
            os.path.join(os.getcwd(), "tables_config.json"),  # cwd/
            "tables_config.json",  # cwd fallback
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                print(f"[RAG v3] Config encontrado: {os.path.abspath(path)}")
                return os.path.abspath(path)
        
        # Se nenhum encontrado, retornar o primeiro (vai falhar com mensagem clara)
        print(f"[RAG v3] ⚠️ Nenhum config encontrado nas localizações:")
        for path in possible_paths:
            print(f"          - {os.path.abspath(path)}")
        return os.path.abspath(config_path)
    
    def _load_config(self) -> Dict[str, Any]:
        """Carrega arquivo de configuração"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config não encontrada: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _extract_metadata(self) -> Dict[str, Dict[str, Any]]:
        """Extrai metadados de todas as tabelas"""
        metadata = {}
        
        for table_name, table_config in self.config.items():
            if not isinstance(table_config, dict) or 'metadata' not in table_config:
                continue
            
            # Extrair info de negócio
            meta = table_config.get('metadata', {})
            business_rules = table_config.get('business_rules', {})
            fields = table_config.get('fields', {})
            usage_examples = table_config.get('usage_examples', {})
            
            metadata[table_name] = {
                'table_id': meta.get('table_id', table_name),
                'bigquery_table': meta.get('bigquery_table', ''),
                'description': meta.get('description', ''),
                'domain': meta.get('domain', ''),
                'keywords': meta.get('keywords', []),
                'exclude_keywords': meta.get('exclude_keywords', []),
                'semantic_description': meta.get('semantic_description', ''),
                'critical_rules': business_rules.get('critical_rules', []),
                'query_rules': business_rules.get('query_rules', []),
                'temporal_fields': fields.get('temporal_fields', []),
                'dimension_fields': fields.get('dimension_fields', []),
                'metric_fields': fields.get('metric_fields', []),
                'filter_fields': fields.get('filter_fields', []),
                'usage_examples': usage_examples,
                'field_aliases': meta.get('field_aliases', {})
            }
        
        print(f"[RAG v3] {len(metadata)} tabelas carregadas")
        return metadata
    
    def _precompute_embeddings(self):
        """Pre-computar embeddings para todas as tabelas"""
        self.embeddings = {}
        
        for table_name, table_meta in self.table_metadata.items():
            # Embedding 1: Descrição semântica
            semantic_desc = table_meta.get('semantic_description', '')
            if not semantic_desc:
                semantic_desc = table_meta.get('description', '')
            
            semantic_emb = self.embedder.encode(
                semantic_desc,
                convert_to_tensor=True,
                show_progress_bar=False
            )
            
            # Embedding 2: Keywords
            keywords = " ".join(table_meta.get('keywords', []))
            keyword_emb = self.embedder.encode(
                keywords,
                convert_to_tensor=True,
                show_progress_bar=False
            )
            
            # Embedding 3: Exemplos de uso
            examples_text = self._aggregate_examples(table_meta.get('usage_examples', {}))
            example_emb = self.embedder.encode(
                examples_text,
                convert_to_tensor=True,
                show_progress_bar=False
            )
            
            self.embeddings[table_name] = {
                'semantic': semantic_emb,
                'keywords': keyword_emb,
                'examples': example_emb,
                'description': semantic_desc
            }
        
        print(f"[RAG v3] Embeddings pré-computados ✅")
    
    def _aggregate_examples(self, usage_examples: Dict) -> str:
        """Agregam exemplos de uso para embedding"""
        examples_list = []
        
        for category, examples in usage_examples.items():
            for example in examples:
                if isinstance(example, dict):
                    question = example.get('question', '')
                    if question:
                        examples_list.append(question)
        
        return " ".join(examples_list[:10])  # Limitar a 10
    
    def score_table_for_query(
        self,
        user_query: str,
        top_k: int = 3,
        debug: bool = False
    ) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Pontuação multi-dimensional de tabelas
        
        Dimensões de scoring:
        - Semantic Similarity (40%): similaridade semântica da query com descrição
        - Keyword Matching (30%): match com keywords da tabela
        - Domain Context (15%): contexto de domínio
        - Temporal Keywords (10%): presença de keywords temporais
        - Metric Keywords (5%): presença de keywords de métricas
        
        Retorna lista de tuplas (table_name, scores_dict) ordenada por score
        """
        
        query_lower = user_query.lower()
        query_upper = user_query.upper()
        
        table_scores = []
        
        for table_name, table_meta in self.table_metadata.items():
            scores = {}
            
            # [1] SEMANTIC SIMILARITY (40%)
            if self.embedder:
                query_emb = self.embedder.encode(
                    user_query,
                    convert_to_tensor=True,
                    show_progress_bar=False
                )
                semantic_sim = float(util.pytorch_cos_sim(
                    query_emb,
                    self.embeddings[table_name]['semantic']
                )[0][0])
                
                # Normalizar para 0-1
                semantic_score = max(0, min(1, semantic_sim))
            else:
                # Fallback: usar keyword matching
                keywords = " ".join(table_meta.get('keywords', []))
                semantic_score = self._simple_keyword_match(user_query, keywords)
            
            # [2] KEYWORD MATCHING (30%)
            keywords = table_meta.get('keywords', [])
            query_normalized = normalize_text(user_query)
            keyword_matches = sum(1 for kw in keywords if normalize_text(kw) in query_normalized)
            keyword_score = min(1.0, keyword_matches / max(1, len(keywords)))
            
            # [3] DOMAIN CONTEXT (15%)
            domain = table_meta.get('domain', '')
            domain_words = domain.split('_')
            domain_normalized = normalize_text(domain)
            domain_matches = sum(1 for d in domain_words if normalize_text(d) in query_normalized)
            domain_score = 1.0 if domain_matches > 0 else 0.3
            
            # [4] TEMPORAL KEYWORDS (10%)
            temporal_keywords = [
                'mês', 'ano', 'evolução', 'período', 'mensal', 'anual',
                'data', 'quando', 'histórico', 'temporal', 'série temporal',
                'janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
                'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro'
            ]
            temporal_matches = sum(1 for t in temporal_keywords if t in query_lower)
            has_temporal_fields = len(table_meta.get('temporal_fields', [])) > 0
            
            if temporal_matches > 0:
                temporal_score = 1.0 if has_temporal_fields else 0.6
            else:
                temporal_score = 0.8 if has_temporal_fields else 0.5
            
            # [5] METRIC KEYWORDS (5%)
            metric_keywords = [
                'total', 'valor', 'quantidade', 'contagem', 'média',
                'soma', 'máximo', 'mínimo', 'percentual', '%',
                'agregado', 'agregação', 'ranking', 'top', 'maior',
                'menor', 'mais', 'menos'
            ]
            metric_matches = sum(1 for m in metric_keywords if m in query_lower)
            has_metric_fields = len(table_meta.get('metric_fields', [])) > 0
            
            if metric_matches > 0:
                metric_score = 1.0 if has_metric_fields else 0.7
            else:
                metric_score = 0.8 if has_metric_fields else 0.5
            
            # [X] PENALTY: EXCLUDE KEYWORDS
            exclude_keywords = table_meta.get('exclude_keywords', [])
            if any(normalize_text(ek) in query_normalized for ek in exclude_keywords):
                # Penalidade FORTE - reduzir score em 80%
                semantic_score *= 0.2
                keyword_score *= 0.2
            
            # SCORE FINAL (com pesos)
            final_score = (
                0.40 * semantic_score +
                0.30 * keyword_score +
                0.15 * domain_score +
                0.10 * temporal_score +
                0.05 * metric_score
            )
            
            scores = {
                'score': final_score,
                'semantic': semantic_score,
                'keyword': keyword_score,
                'domain': domain_score,
                'temporal': temporal_score,
                'metric': metric_score,
                'confidence': self._score_to_confidence(final_score)
            }
            
            # Explicação detalhada
            scores['explanation'] = self._build_explanation(
                table_name,
                table_meta,
                scores,
                user_query
            )
            
            table_scores.append((table_name, scores))
            
            if debug:
                print(f"\n📊 {table_name}:")
                print(f"   Semantic:  {semantic_score:.1%}")
                print(f"   Keyword:   {keyword_score:.1%}")
                print(f"   Domain:    {domain_score:.1%}")
                print(f"   Temporal:  {temporal_score:.1%}")
                print(f"   Metric:    {metric_score:.1%}")
                print(f"   FINAL:     {final_score:.1%} ({scores['confidence']})")
        
        # Ordenar por score
        ranked = sorted(table_scores, key=lambda x: x[1]['score'], reverse=True)[:top_k]
        
        if debug:
            print(f"\n🏆 Top {top_k} tabelas:")
            for rank, (table_name, scores) in enumerate(ranked, 1):
                print(f"   {rank}. {table_name}: {scores['score']:.1%} ({scores['confidence']})")
        
        return ranked
    
    def _simple_keyword_match(self, query: str, keywords: str) -> float:
        """Fallback simples para matching sem embeddings"""
        query_lower = query.lower()
        keywords_lower = keywords.lower()
        
        # Contar matches
        words = keywords_lower.split()
        matches = sum(1 for word in words if word in query_lower)
        
        return min(1.0, matches / max(1, len(words)))
    
    def _score_to_confidence(self, score: float) -> str:
        """Converte score numérico para nivel de confiança"""
        if score >= 0.85:
            return "ALTA"
        elif score >= 0.70:
            return "MÉDIA"
        elif score >= 0.55:
            return "BAIXA"
        else:
            return "MUITO_BAIXA"
    
    def _build_explanation(
        self,
        table_name: str,
        table_meta: Dict,
        scores: Dict,
        query: str
    ) -> str:
        """Constrói explicação textual do score"""
        
        explanation = f"Tabela '{table_name}' selecionada porque:\n"
        
        # Melhor dimensão
        best_dim = max(
            [('Semântica', scores['semantic']),
             ('Keywords', scores['keyword']),
             ('Domínio', scores['domain']),
             ('Temporal', scores['temporal']),
             ('Métrica', scores['metric'])],
            key=lambda x: x[1]
        )
        explanation += f"✓ Melhor match em: {best_dim[0]} ({best_dim[1]:.1%})\n"
        
        # Keywords que matcharam
        keywords = table_meta.get('keywords', [])
        matching_keywords = [k for k in keywords if k.lower() in query.lower()]
        if matching_keywords:
            explanation += f"✓ Keywords matchados: {', '.join(matching_keywords[:3])}"
        
        return explanation
    
    def get_best_table(self, user_query: str, debug: bool = False) -> str:
        """Retorna apenas o nome da melhor tabela"""
        ranked = self.score_table_for_query(user_query, top_k=1, debug=debug)
        if ranked:
            return ranked[0][0]
        return None
    
    def get_top_3_tables(self, user_query: str, debug: bool = False) -> List[str]:
        """Retorna lista dos 3 melhores nomes de tabela"""
        ranked = self.score_table_for_query(user_query, top_k=3, debug=debug)
        return [table_name for table_name, _ in ranked]


# Singleton global
_rag_instance = None

def get_rag_v3_instance() -> BusinessMetadataRAGv3:
    """Retorna instância global do RAG v3"""
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = BusinessMetadataRAGv3()
    return _rag_instance


if __name__ == "__main__":
    # Teste
    rag = BusinessMetadataRAGv3()
    
    test_queries = [
        "Qual o total de veículos vendidos por mês?",
        "Quantos contratos de consórcio ativos existem?",
        "Qual é o percentual amortizado dos contratos?",
        "Quantas propostas foram vendidas?",
        "Qual o orçado vs realizado por centro de custo?"
    ]
    
    for query in test_queries:
        print(f"\n{'='*80}")
        print(f"Query: {query}")
        print('='*80)
        ranked = rag.score_table_for_query(query, top_k=3, debug=True)
