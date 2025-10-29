"""
Business Metadata RAG - Sistema de Recuperação de Metadados de Negócio
Versão 2.0 - Estrutura JSON aprimorada
"""

import os
import json
import hashlib
import duckdb
 # Removido: import google.generativeai as genai
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import math


@dataclass
class TableMetadata:
    """Estrutura otimizada para metadados de tabela"""
    table_name: str
    table_id: str
    bigquery_table: str
    description: str
    domain: str
    
    # Regras organizadas por prioridade
    critical_rules: List[Dict[str, Any]] = field(default_factory=list)
    query_rules: List[Dict[str, Any]] = field(default_factory=list)
    
    # Campos organizados por categoria
    temporal_fields: List[Dict[str, Any]] = field(default_factory=list)
    dimension_fields: List[Dict[str, Any]] = field(default_factory=list)
    metric_fields: List[Dict[str, Any]] = field(default_factory=list)
    filter_fields: List[Dict[str, Any]] = field(default_factory=list)
    
    # Exemplos organizados por tipo
    usage_examples: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    
    # Contexto otimizado para RAG
    business_context: str = ""
    full_content: str = ""
    last_updated: datetime = field(default_factory=datetime.now)


class BusinessMetadataRAGV2:
    """Sistema RAG melhorado para metadados de negócio"""
    
    def __init__(self, config_path: str = "tables_config.json", cache_db_path: str = "cache.db"):
        self.config_path = config_path
        self.cache_db_path = cache_db_path
        self.embedding_model = "all-MiniLM-L6-v2"
        self._init_cache_db()
        self._load_sentence_transformer()

    def _load_sentence_transformer(self):
        try:
            from sentence_transformers import SentenceTransformer
            self.st_model = SentenceTransformer(self.embedding_model)
            self._has_st = True
            print(f"[RAG] Modelo sentence-transformers carregado com sucesso: {self.embedding_model}")
        except Exception as e:
            print(f"[RAG][FATAL] Erro ao carregar modelo sentence-transformers: {e}")
            self._has_st = False
            raise RuntimeError(f"[RAG][FATAL] Não foi possível carregar o modelo sentence-transformers: {e}")
    
    def _init_cache_db(self):
        """Inicializa Annoy index para embeddings e carrega metadados"""
        from annoy import AnnoyIndex
        import os, json
        self.annoy_dim = 384  # all-MiniLM-L6-v2
        self.annoy_index_path = self.cache_db_path.replace('.db', '.ann')
        self.annoy_meta_path = self.cache_db_path.replace('.db', '.meta.json')
        self.annoy_index = AnnoyIndex(self.annoy_dim, 'angular')
        if os.path.exists(self.annoy_index_path):
            self.annoy_index.load(self.annoy_index_path)
        if os.path.exists(self.annoy_meta_path):
            with open(self.annoy_meta_path, 'r', encoding='utf-8') as f:
                self._annoy_metadata = json.load(f)
            print(f"[Annoy] Metadados carregados: {self._annoy_metadata}")
        else:
            self._annoy_metadata = {}
            print(f"[Annoy] Nenhum metadado encontrado em {self.annoy_meta_path}")
    
    def load_config(self) -> Dict[str, Any]:
        """Carrega configuração do arquivo JSON"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Arquivo de configuração não encontrado: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def extract_table_metadata(self) -> List[TableMetadata]:
        """Extrai metadados das tabelas da configuração JSON - VERSÃO CORRIGIDA"""
        config = self.load_config()
        metadata_list = []

        # CORREÇÃO: JSON tem tabelas no nível raiz
        tables_data = config

        for table_name, table_config in tables_data.items():
            # Verifica se é uma tabela válida (tem metadados)
            if not isinstance(table_config, dict) or 'metadata' not in table_config:
                print(f"[RAG] Ignorando chave não-tabela: {table_name}")
                continue

            print(f"[RAG] Processando tabela: {table_name}")

            metadata_section = table_config.get('metadata', {})
            business_rules = table_config.get('business_rules', {})
            fields = table_config.get('fields', {})
            usage_examples = table_config.get('usage_examples', {})

            # Cria contexto de negócio otimizado
            business_context = self._create_business_context(table_name, table_config)

            # Conteúdo completo para embedding
            full_content = self._create_full_content(table_name, table_config)

            metadata = TableMetadata(
                table_name=table_name,
                table_id=metadata_section.get('table_id', table_name),
                bigquery_table=metadata_section.get('bigquery_table', ''),
                description=metadata_section.get('description', ''),
                domain=metadata_section.get('domain', ''),
                critical_rules=business_rules.get('critical_rules', []),
                query_rules=business_rules.get('query_rules', []),
                temporal_fields=fields.get('temporal_fields', []),
                dimension_fields=fields.get('dimension_fields', []),
                metric_fields=fields.get('metric_fields', []),
                filter_fields=fields.get('filter_fields', []),
                usage_examples=usage_examples,
                business_context=business_context,
                full_content=full_content,
                last_updated=datetime.now()
            )

            metadata_list.append(metadata)

        print(f"[RAG] Total de tabelas processadas: {len(metadata_list)}")
        return metadata_list
    
    def _create_business_context(self, table_name: str, table_config: Dict[str, Any]) -> str:
        """Cria contexto de negócio otimizado para o RAG, listando explicitamente todos os campos válidos (apenas do tables_config.json). Nunca inclua nomes de coluna em outro local!"""
        metadata = table_config.get('metadata', {})
        business_rules = table_config.get('business_rules', {})
        fields = table_config.get('fields', {})

        # Regras críticas
        critical_rules = []
        for rule in business_rules.get('critical_rules', []):
            rule_text = rule.get('rule', rule.get('description', ''))
            context = rule.get('context', '')
            critical_rules.append(f"• {rule_text}: {context}")

        # Listar todos os campos válidos por categoria, incluindo descrição
        def list_fields(cat, label):
            return [
                f"[{label}] {field.get('name')} ({field.get('type')}) — {field.get('description', '').strip()}"
                for field in fields.get(cat, [])
            ]

        temporal_fields = list_fields('temporal_fields', 'temporal')
        dimension_fields = list_fields('dimension_fields', 'dimension')
        metric_fields = list_fields('metric_fields', 'metric')
        filter_fields = list_fields('filter_fields', 'filter')

        context = f"""
Tabela: {table_name} ({metadata.get('bigquery_table', table_name)})
Descrição: {metadata.get('description', '')}
Domínio: {metadata.get('domain', '')}

=== REGRAS CRÍTICAS ===
{chr(10).join(critical_rules[:8])}

=== LISTA DE CAMPOS VÁLIDOS (use apenas estes nomes, nunca invente ou altere. Não utilize nomes de coluna que não estejam abaixo!) ===
{chr(10).join(temporal_fields)}
{chr(10).join(dimension_fields)}
{chr(10).join(metric_fields)}
{chr(10).join(filter_fields)}
""".strip()
        return context

    def _create_full_content(self, table_name: str, table_config: Dict[str, Any]) -> str:
        """Cria conteúdo completo para embedding, usando function_call_example como exemplo relevante"""
        metadata = table_config.get('metadata', {})
        business_rules = table_config.get('business_rules', {})
        fields = table_config.get('fields', {})
        usage_examples = table_config.get('usage_examples', {})

        # Extrai todas as regras
        all_rules = []
        for rule in business_rules.get('critical_rules', []):
            all_rules.append(rule.get('description', ''))
        for rule in business_rules.get('query_rules', []):
            all_rules.append(rule.get('description', ''))

        # Extrai todos os campos (usando 'name' corretamente)
        all_fields = []
        if isinstance(fields, dict):
            field_sources = fields.values()
        elif isinstance(fields, list):
            field_sources = fields
        else:
            field_sources = []
        for category_fields in field_sources:
            if isinstance(category_fields, list):
                for field in category_fields:
                    if isinstance(field, dict):
                        all_fields.append(f"{field.get('name', '')} {field.get('description', '')}")
            elif isinstance(category_fields, dict):
                all_fields.append(f"{category_fields.get('name', '')} {category_fields.get('description', '')}")

        # Extrai exemplos: usa apenas function_call_example como string, sem fallback
        all_examples = []
        if isinstance(usage_examples, dict):
            example_sources = usage_examples.values()
        elif isinstance(usage_examples, list):
            example_sources = usage_examples
        else:
            example_sources = []
        for category_examples in example_sources:
            if isinstance(category_examples, list):
                for example in category_examples:
                    if isinstance(example, dict):
                        fc = example.get('function_call_example')
                        if fc is not None:
                            try:
                                fc_str = json.dumps(fc, ensure_ascii=False)
                            except Exception:
                                fc_str = str(fc)
                            all_examples.append(fc_str)
            elif isinstance(category_examples, dict):
                fc = category_examples.get('function_call_example')
                if fc is not None:
                    try:
                        fc_str = json.dumps(fc, ensure_ascii=False)
                    except Exception:
                        fc_str = str(fc)
                    all_examples.append(fc_str)

        content = f"""
        Tabela: {table_name}
        Descrição: {metadata.get('description', '')}
        Domínio: {metadata.get('domain', '')}

        Regras: {' '.join(all_rules)}

        Campos: {' '.join(all_fields)}

        Exemplos: {' '.join(all_examples)}
        """.strip()

        return content
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Gera embedding para um texto usando sentence-transformers"""
        if not hasattr(self, 'st_model') or not self._has_st:
            return []
        try:
            emb = self.st_model.encode([text], show_progress_bar=False)
            return emb[0].tolist() if hasattr(emb[0], 'tolist') else list(emb[0])
        except Exception as e:
            return []
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calcula similaridade cosseno entre dois vetores"""
        if not a or not b or len(a) != len(b):
            return 0.0
        
        dot_product = sum(x * y for x, y in zip(a, b))
        norm1 = math.sqrt(sum(x * x for x in a))
        norm2 = math.sqrt(sum(x * x for x in b))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    

    def store_metadata(self, metadata: TableMetadata, annoy_index, annoy_metadata, idx) -> bool:
        """Armazena metadados e embedding no Annoy (novo index em memória)"""
        try:
            import numpy as np
            embedding = self._generate_embedding(metadata.full_content)
            if embedding and len(embedding) > 0:
                annoy_index.add_item(idx, np.array(embedding, dtype=np.float32))
                annoy_metadata[idx] = (metadata.table_name, metadata.business_context)
            return True
        except Exception as e:
            print(f"[Annoy] Erro ao armazenar embedding: {e}")
            return False
    

    def update_metadata_cache(self):
        """Atualiza cache completo de metadados (recria Annoy do zero e salva metadados)"""
        try:
            from annoy import AnnoyIndex
            import numpy as np, json, os
            metadata_list = self.extract_table_metadata()
            annoy_index = AnnoyIndex(self.annoy_dim, 'angular')
            annoy_metadata = {}
            idx = 0
            for metadata in metadata_list:
                success = self.store_metadata(metadata, annoy_index, annoy_metadata, idx)
                status = "[OK]" if success else "[ERRO]"
                print(f"{status} {metadata.table_name}")
                if success:
                    idx += 1
            if idx > 0:
                annoy_index.build(10)
                annoy_index.save(self.annoy_index_path)
                with open(self.annoy_meta_path, 'w', encoding='utf-8') as f:
                    json.dump(annoy_metadata, f, ensure_ascii=False)
                print(f"[Annoy] Metadados salvos: {annoy_metadata}")
                self.annoy_index = annoy_index
                self._annoy_metadata = annoy_metadata
            print(f"[OK] Cache atualizado para {idx} tabelas")
        except Exception as e:
            print(f"Erro ao atualizar cache: {e}")
    
    def retrieve_relevant_context(self, user_query: str, max_results: int = 3, similarity_threshold: float = 0.3) -> List[str]:
        """Recupera contexto relevante usando Annoy, com logging e threshold adaptativo"""
        try:
            from annoy import AnnoyIndex
            import numpy as np
            # Se metadados não carregados ou vazios, recarrega
            if not hasattr(self, '_annoy_metadata') or not self._annoy_metadata:
                print("[Annoy] _annoy_metadata vazio ou não carregado, forçando recarregamento...")
                self._init_cache_db()
                print(f"[Annoy] _annoy_metadata após recarga: {self._annoy_metadata}")
            query_embedding = self._generate_embedding(user_query)
            if not query_embedding:
                print("[Annoy] Embedding da query não gerado.")
                return []
            idxs, dists = self.annoy_index.get_nns_by_vector(np.array(query_embedding, dtype=np.float32), max_results, include_distances=True)
            print(f"[Annoy] Embedding da query: {query_embedding[:8]}... (dim={len(query_embedding)})")
            print(f"[Annoy] idxs encontrados: {idxs}")
            print(f"[Annoy] dists: {dists}")
            contexts = []
            for idx, dist in zip(idxs, dists):
                meta = self._annoy_metadata.get(str(idx)) if isinstance(self._annoy_metadata, dict) else None
                print(f"[Annoy] idx={idx} meta={meta} dist={dist}")
                if meta is not None:
                    table_name, business_context = meta
                    print(f"[Annoy] Distância para {table_name}: {dist}")
                    if dist <= similarity_threshold or len(contexts) == 0:
                        # Sempre retorna pelo menos o mais próximo
                        contexts.append(f"=== {table_name} ===\n{business_context}")
            if not contexts:
                # Se nada passou pelo threshold, retorna o mais próximo
                if idxs:
                    idx = idxs[0]
                    meta = self._annoy_metadata.get(str(idx)) if isinstance(self._annoy_metadata, dict) else None
                    print(f"[Annoy] Forçando retorno do mais próximo: idx={idx} meta={meta} dist={dists[0]}")
                    if meta is not None:
                        table_name, business_context = meta
                        contexts.append(f"=== {table_name} ===\n{business_context}")
            return contexts
        except Exception as e:
            print(f"[Annoy] Erro ao buscar contexto: {e}")
            return []


def get_optimized_business_context(user_query: str, max_results: int = 2) -> str:
    """Função de conveniência para obter contexto otimizado"""
    try:
        rag = BusinessMetadataRAGV2()
        # Mais permissivo: mais exemplos e menor threshold
        contexts = rag.retrieve_relevant_context(user_query, max_results=5, similarity_threshold=0.15)
        if not contexts:
            return "Nenhum contexto relevante encontrado."
        # Estimativa de tokens (aproximadamente 4 caracteres por token)
        full_context = "\n\n".join(contexts)
        estimated_tokens = len(full_context) // 4
        result = f"""=== METADADOS RELEVANTES PARA SUA CONSULTA ===\n\n{chr(10).join(contexts)}\n\n=== EXEMPLOS RELEVANTES ===\n1. Para consultas com múltiplas dimensões, use QUALIFY com ROW_NUMBER()\n2. Para comparações temporais, use EXTRACT(YEAR/MONTH FROM <<variavel_periodo>>)\n3. Para buscas de texto, use UPPER(campo) LIKE UPPER('%valor%')\n\nTokens estimados: {estimated_tokens}\nTabelas relevantes: {', '.join([ctx.split('===')[1].strip() for ctx in contexts if '===' in ctx])}\n"""
        return result
    except Exception as e:
        return f"Erro ao obter contexto: {e}"



# Singleton para BusinessMetadataRAGV2
_business_rag_instance = None

def get_business_rag_instance() -> BusinessMetadataRAGV2:
    """Retorna instância singleton do Business RAG"""
    global _business_rag_instance
    if _business_rag_instance is None:
        print("Inicializando BusinessMetadataRAGV2 singleton...")
        _business_rag_instance = BusinessMetadataRAGV2()
        _business_rag_instance.update_metadata_cache()
        print("BusinessMetadataRAGV2 inicializado!")
    return _business_rag_instance

def setup_business_rag():
    """Inicializa o sistema RAG de negócios (mantido para compatibilidade)"""
    get_business_rag_instance()


if __name__ == "__main__":
    # Teste básico
    rag = BusinessMetadataRAGV2()
    rag.update_metadata_cache()
    
    context = get_optimized_business_context("vendas por vendedor")
    print(context)