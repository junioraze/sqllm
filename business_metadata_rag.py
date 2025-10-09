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
        """Inicializa banco de cache"""
        with duckdb.connect(self.cache_db_path) as conn:
            # Cache de metadados
            conn.execute("""
                CREATE TABLE IF NOT EXISTS business_metadata_v2 (
                    table_name VARCHAR PRIMARY KEY,
                    table_id VARCHAR NOT NULL,
                    bigquery_table VARCHAR NOT NULL,
                    description VARCHAR NOT NULL,
                    domain VARCHAR NOT NULL,
                    business_context TEXT NOT NULL,
                    full_content TEXT NOT NULL,
                    content_hash VARCHAR NOT NULL,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Cache de embeddings
            conn.execute("""
                CREATE TABLE IF NOT EXISTS business_embeddings_v2 (
                    id VARCHAR PRIMARY KEY,
                    table_name VARCHAR NOT NULL,
                    content_hash VARCHAR NOT NULL,
                    embedding_json TEXT NOT NULL,
                    similarity_threshold DOUBLE DEFAULT 0.7,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (table_name) REFERENCES business_metadata_v2(table_name)
                )
            """)
    
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

        # CORREÇÃO: Seu JSON tem tabelas no nível raiz
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
        """Cria contexto de negócio otimizado para o RAG, incluindo orientação de conversão se houver"""
        metadata = table_config.get('metadata', {})
        business_rules = table_config.get('business_rules', {})
        fields = table_config.get('fields', {})

        # Regras críticas
        critical_rules = []
        for rule in business_rules.get('critical_rules', []):
            rule_text = rule.get('rule', rule.get('description', ''))
            context = rule.get('context', '')
            critical_rules.append(f"• {rule_text}: {context}")

        # Campos principais do formato v2
        principal_fields = []

        # Campos temporais (formato v2) - inclui orientação de conversão se houver
        for field in fields.get('temporal_fields', []):
            name = field.get('name')
            desc = field.get('description')
            extracts = field.get('common_extracts', [])
            conversion = field.get('conversion', None)
            if conversion:
                principal_fields.append(f"• {name}: {desc} [⚠️ Para SQL: SEMPRE use {conversion} ao invés de {name}]")
            else:
                principal_fields.append(f"• {name}: {desc}")
            if extracts:
                principal_fields.append(f"  Extrações: {', '.join(extracts[:3])}")

        # Campos de dimensão (formato v2)
        for field in fields.get('dimension_fields', []):
            name = field.get('name')
            desc = field.get('description')
            pattern = field.get('search_pattern', '')
            principal_fields.append(f"• {name}: {desc}")
            if pattern:
                principal_fields.append(f"  Padrão: {pattern}")

        # Campos métricos (formato v2)
        for field in fields.get('metric_fields', []):
            name = field.get('name')
            desc = field.get('description')
            priority = field.get('priority', '')
            principal_fields.append(f"• {name}: {desc}")
            if priority == 'alta':
                principal_fields.append(f"  ⚠️ PRIORIDADE ALTA")

        context = f"""
Tabela: {table_name} ({metadata.get('bigquery_table', table_name)})
Descrição: {metadata.get('description', '')}
Domínio: {metadata.get('domain', '')}

=== REGRAS CRÍTICAS ===
{chr(10).join(critical_rules[:8])}

=== CAMPOS PRINCIPAIS ===
{chr(10).join(principal_fields[:15])}
""".strip()
        return context

    def _create_full_content(self, table_name: str, table_config: Dict[str, Any]) -> str:
        """Cria conteúdo completo para embedding"""
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
        
        # Extrai todos os campos
        all_fields = []
        for category_fields in fields.values():
            if isinstance(category_fields, list):
                for field in category_fields:
                    if isinstance(field, dict):
                        all_fields.append(f"{field.get('field', '')} {field.get('description', '')}")
        
        # Extrai exemplos
        all_examples = []
        for category_examples in usage_examples.values():
            if isinstance(category_examples, list):
                for example in category_examples:
                    if isinstance(example, dict):
                        all_examples.append(example.get('description', ''))
        
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
    
    def store_metadata(self, metadata: TableMetadata) -> bool:
        """Armazena metadados no cache"""
        try:
            content_hash = hashlib.md5(metadata.full_content.encode()).hexdigest()
            with duckdb.connect(self.cache_db_path) as conn:
                # Verifica se já existe e se precisa atualizar
                existing = conn.execute(
                    "SELECT content_hash FROM business_metadata_v2 WHERE table_name = ?",
                    [metadata.table_name]
                ).fetchone()
                if existing and existing[0] == content_hash:
                    return True  # Não mudou, não precisa atualizar
                # Remove registros antigos
                conn.execute("DELETE FROM business_embeddings_v2 WHERE table_name = ?", [metadata.table_name])
                conn.execute("DELETE FROM business_metadata_v2 WHERE table_name = ?", [metadata.table_name])
                # Insere metadados
                conn.execute("""
                    INSERT INTO business_metadata_v2 
                    (table_name, table_id, bigquery_table, description, domain, business_context, full_content, content_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    metadata.table_name, metadata.table_id, metadata.bigquery_table,
                    metadata.description, metadata.domain, metadata.business_context,
                    metadata.full_content, content_hash
                ])
                # Gera e armazena embedding
                embedding = self._generate_embedding(metadata.full_content)
                if embedding and len(embedding) > 0:
                    embedding_id = f"{metadata.table_name}_{content_hash}"
                    conn.execute("""
                        INSERT INTO business_embeddings_v2 
                        (id, table_name, content_hash, embedding_json)
                        VALUES (?, ?, ?, ?)
                    """, [
                        embedding_id, metadata.table_name, content_hash, json.dumps(embedding)
                    ])
                return True
        except Exception as e:
            return False
    
    def update_metadata_cache(self):
        """Atualiza cache completo de metadados"""
        try:
            metadata_list = self.extract_table_metadata()
            
            with duckdb.connect(self.cache_db_path) as conn:
                for metadata in metadata_list:
                    success = self.store_metadata(metadata)
                    status = "[OK]" if success else "[ERRO]"
                    print(f"{status} {metadata.table_name}")
                
                print(f"[OK] Cache atualizado para {len(metadata_list)} tabelas")
                
        except Exception as e:
            print(f"Erro ao atualizar cache: {e}")
    
    def retrieve_relevant_context(self, user_query: str, max_results: int = 3, similarity_threshold: float = 0.3) -> List[str]:
        """Recupera contexto relevante baseado na consulta do usuário e exibe o que será enviado ao modelo"""
        try:
            metadata_list = self.extract_table_metadata()
            query_embedding = self._generate_embedding(user_query)
            if not query_embedding:
                return []

            contexts = []
            with duckdb.connect(self.cache_db_path) as conn:
                results = conn.execute("""
                    SELECT m.table_name, m.business_context, e.embedding_json
                    FROM business_metadata_v2 m
                    JOIN business_embeddings_v2 e ON m.table_name = e.table_name
                    ORDER BY m.table_name
                """).fetchall()

                similarities = []
                for table_name, business_context, embedding_json in results:
                    try:
                        stored_embedding = json.loads(embedding_json)
                        similarity = self._cosine_similarity(query_embedding, stored_embedding)
                        if similarity >= similarity_threshold:
                            similarities.append((similarity, table_name, business_context))
                    except:
                        continue

                similarities.sort(reverse=True)
                for similarity, table_name, business_context in similarities[:max_results]:
                    contexts.append(f"=== {table_name} ===\n{business_context}")

            return contexts
        except Exception as e:
            return []


def get_optimized_business_context(user_query: str, max_results: int = 2) -> str:
    """Função de conveniência para obter contexto otimizado"""
    try:
        rag = BusinessMetadataRAGV2()
        # Verifica se há cache válido
        with duckdb.connect(rag.cache_db_path) as conn:
            count = conn.execute("SELECT COUNT(*) FROM business_metadata_v2").fetchone()[0]
            if count == 0:
                print("Cache vazio, atualizando...")
                rag.update_metadata_cache()
        # Mais permissivo: mais exemplos e menor threshold
        contexts = rag.retrieve_relevant_context(user_query, max_results=5, similarity_threshold=0.15)
        if not contexts:
            return "Nenhum contexto relevante encontrado."
        # Estimativa de tokens (aproximadamente 4 caracteres por token)
        full_context = "\n\n".join(contexts)
        estimated_tokens = len(full_context) // 4
        result = f"""=== METADADOS RELEVANTES PARA SUA CONSULTA ===\n\n{chr(10).join(contexts)}\n\n=== EXEMPLOS RELEVANTES ===\n1. Para consultas com múltiplas dimensões, use QUALIFY com ROW_NUMBER()\n2. Para comparações temporais, use EXTRACT(YEAR/MONTH FROM nf_dtemis)\n3. SEMPRE use 'nf_vl' para valores monetários\n4. Para buscas de texto, use UPPER(campo) LIKE UPPER('%valor%')\n\nTokens estimados: {estimated_tokens}\nTabelas relevantes: {', '.join([ctx.split('===')[1].strip() for ctx in contexts if '===' in ctx])}\n"""
        return result
    except Exception as e:
        return f"Erro ao obter contexto: {e}"


# Instância global para uso no sistema
business_rag = BusinessMetadataRAGV2()

def setup_business_rag():
    """Inicializa o sistema RAG de negócios"""
    print("🔄 Inicializando Business RAG v2...")
    business_rag.update_metadata_cache()
    print("✅ Business RAG v2 inicializado!")


if __name__ == "__main__":
    # Teste básico
    rag = BusinessMetadataRAGV2()
    rag.update_metadata_cache()
    
    context = get_optimized_business_context("vendas por vendedor")
    print(context)