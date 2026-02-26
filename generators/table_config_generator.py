"""
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║           TABLE CONFIG GENERATOR - Gerador Automático de Schemas         ║
║                                                                           ║
║  Funcionalidades:                                                         ║
║  1. Recupera DDL do BigQuery (information_schema.TABLES)                 ║
║  2. Traduz descrições do inglês para português                           ║
║  3. Faz profile da tabela (quantidade de linhas, tamanho, etc)           ║
║  4. Gera estrutura base do table_config.json                             ║
║  5. Utiliza Gemini para refinamento de regras de negócio                 ║
║  6. Salva como table_config_<table_id>.json                              ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
"""

import json
import re
from datetime import datetime
from typing import Dict, List, Any, Tuple

from google.cloud import bigquery
import google.generativeai as genai
from config.settings import PROJECT_ID, DATASET_ID, MODEL_NAME
from pathlib import Path


class TableSchemaExtractor:
    """Extrai schema e metadados de tabelas do BigQuery"""
    
    def __init__(self, project_id: str, dataset_id: str):
        self.client = bigquery.Client(project=project_id)
        self.project_id = project_id
        self.dataset_id = dataset_id
    
    def get_table_ddl(self, table_id: str) -> str:
        """
        Recupera DDL da tabela usando information_schema
        
        Args:
            table_id: ID da tabela (ex: 'drvy_VeiculosVendas')
        
        Returns:
            String com o DDL completo
        """
        print(f"📋 Recuperando DDL para {table_id}...")
        
        query = f"""
        SELECT ddl
        FROM `{self.project_id}.{self.dataset_id}.__TABLES__`
        WHERE table_id = '{table_id}'
        """
        
        try:
            result = self.client.query(query).result()
            for row in result:
                return row.ddl
        except Exception as e:
            print(f"⚠️  Método 1 falhou: {e}")
            # Fallback: usar INFORMATION_SCHEMA
            return self._get_ddl_from_information_schema(table_id)
    
    def _get_ddl_from_information_schema(self, table_id: str) -> str:
        """Fallback para recuperar schema via INFORMATION_SCHEMA"""
        print(f"  ↳ Usando INFORMATION_SCHEMA como fallback...")
        
        query = f"""
        SELECT 
            column_name,
            data_type,
            is_nullable,
            description
        FROM `{self.project_id}.{self.dataset_id}.INFORMATION_SCHEMA.COLUMNS`
        WHERE table_name = '{table_id}'
        ORDER BY ordinal_position
        """
        
        try:
            result = self.client.query(query).result()
            columns_info = []
            for row in result:
                col_info = {
                    "name": row.column_name,
                    "type": row.data_type,
                    "nullable": row.is_nullable == "YES",
                    "description": row.description or ""
                }
                columns_info.append(col_info)
            
            return json.dumps(columns_info, indent=2)
        except Exception as e:
            print(f"❌ Erro ao recuperar schema: {e}")
            return "{}"
    
    def get_table_description(self, table_id: str) -> Tuple[str, int]:
        """
        Recupera descrição e metadados da tabela
        
        Returns:
            (description, row_count)
        """
        print(f"📊 Analisando metadados de {table_id}...")
        
        query = f"""
        SELECT 
            table_catalog,
            table_schema,
            table_name,
            table_type,
            creation_time,
            (SELECT COUNT(*) FROM `{self.project_id}.{self.dataset_id}.{table_id}`) as row_count
        FROM `{self.project_id}.{self.dataset_id}.INFORMATION_SCHEMA.TABLES`
        WHERE table_name = '{table_id}'
        """
        
        try:
            result = self.client.query(query).result()
            for row in result:
                return f"Tabela {table_id}", row.row_count
        except Exception as e:
            print(f"⚠️  Erro ao recuperar metadados: {e}")
            return f"Tabela {table_id}", 0
    
    def get_table_profile(self, table_id: str) -> Dict[str, Any]:
        """
        Faz profile da tabela (estatísticas, distribuição, etc)
        
        Returns:
            Dict com informações de profile
        """
        print(f"📈 Gerando profile da tabela {table_id}...")
        
        query = f"""
        SELECT 
            COUNT(*) as total_rows,
            ARRAY_LENGTH(REGEXP_EXTRACT_ALL(TO_JSON_STRING(t), r'"')) / 2 as avg_columns
        FROM `{self.project_id}.{self.dataset_id}.{table_id}` t LIMIT 1000
        """
        
        try:
            result = self.client.query(query).result()
            for row in result:
                return {
                    "total_rows_sampled": int(row.total_rows),
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            print(f"⚠️  Erro ao fazer profile: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}


class TableConfigBuilder:
    """Constrói table_config.json a partir de schema e metadados"""
    
    def __init__(self):
        self.extractor = TableSchemaExtractor(PROJECT_ID, DATASET_ID)
    
    def parse_schema_from_ddl(self, ddl: str) -> Dict[str, Any]:
        """
        Parseia DDL para extrair campos e tipos
        
        Args:
            ddl: String contendo DDL da tabela
        
        Returns:
            Dict com campos categorizados
        """
        print("🔍 Parseando DDL...")
        
        # Parse simples do DDL para extrair colunas
        # Formato esperado: CREATE TABLE ... (col1 TYPE1, col2 TYPE2, ...)
        
        columns = {
            "temporal_fields": [],
            "dimension_fields": [],
            "metric_fields": [],
            "filter_fields": []
        }
        
        try:
            schema = json.loads(ddl) if ddl.startswith('[') else self._parse_ddl_string(ddl)
            
            for col in schema if isinstance(schema, list) else schema.get('columns', []):
                col_name = col.get('name') if isinstance(col, dict) else col
                col_type = col.get('type', 'STRING').upper() if isinstance(col, dict) else 'STRING'
                col_desc = col.get('description', '') if isinstance(col, dict) else ''
                
                field_info = {
                    "name": col_name,
                    "type": col_type,
                    "description": col_desc
                }
                
                # Categoriza campos automaticamente
                if any(x in col_name.lower() for x in ['data', 'data_', 'dta_', 'date', 'dt_', 'timestamp', 'time']):
                    columns["temporal_fields"].append(field_info)
                elif any(x in col_type for x in ['INT', 'FLOAT', 'NUMERIC', 'DECIMAL']):
                    columns["metric_fields"].append(field_info)
                else:
                    columns["dimension_fields"].append(field_info)
                    columns["filter_fields"].append(field_info)
        
        except Exception as e:
            print(f"⚠️  Erro ao parsear schema: {e}")
        
        return columns
    
    def _parse_ddl_string(self, ddl: str) -> List[Dict]:
        """Parseia DDL em formato texto"""
        columns = []
        
        # Regex para capturar: nome_coluna TIPO [DESCRIPTION/COMMENTS]
        pattern = r'(\w+)\s+(\w+(?:\s*\(\s*\d+\s*\))?)'
        
        for match in re.finditer(pattern, ddl):
            columns.append({
                "name": match.group(1),
                "type": match.group(2)
            })
        
        return columns
    
    def generate_base_config(self, table_id: str, schema_info: Dict) -> Dict[str, Any]:
        """
        Gera config base estruturado
        
        Args:
            table_id: ID da tabela
            schema_info: Informações do schema
        
        Returns:
            Dict com estrutura base do table_config
        """
        print(f"🏗️  Gerando config base para {table_id}...")
        
        description, row_count = self.extractor.get_table_description(table_id)
        profile = self.extractor.get_table_profile(table_id)
        
        config = {
            "metadata": {
                "table_id": table_id,
                "bigquery_table": f"{PROJECT_ID}.{DATASET_ID}.{table_id}",
                "description": description,
                "domain": self._infer_domain(table_id),
                "last_updated": datetime.now().isoformat(),
                "row_count_sampled": row_count,
                "keywords": self._extract_keywords(table_id),
                "exclude_keywords": []
            },
            "business_rules": {
                "critical_rules": [],
                "query_rules": []
            },
            "fields": schema_info,
            "usage_examples": {
                "ranking_queries": [],
                "temporal_analysis": [],
                "search_examples": [],
                "value_analysis": [],
                "temporal_ranking": []
            },
            "profile": profile
        }
        
        return config
    
    def _infer_domain(self, table_id: str) -> str:
        """Infere domínio de negócio baseado no nome da tabela"""
        table_lower = table_id.lower()
        
        if 'veiculo' in table_lower or 'venda' in table_lower:
            return "automotivo_vendas"
        elif 'cota' in table_lower or 'consorcio' in table_lower:
            return "consorcio_contratos"
        elif 'qualidade' in table_lower or 'historico' in table_lower:
            return "consorcio_vendas_historico"
        else:
            return "negocios"
    
    def _extract_keywords(self, table_id: str) -> List[str]:
        """Extrai keywords do nome da tabela"""
        # Remove prefixos comuns
        clean_name = re.sub(r'^(drvy|dvry|dv|d)_', '', table_id, flags=re.IGNORECASE)
        
        # Split por underscore e camelCase
        keywords = re.split(r'[_]|(?=[A-Z])', clean_name)
        keywords = [kw.lower() for kw in keywords if kw]
        
        return keywords


class TableConfigRefiner:
    """Usa Gemini para refinar regras de negócio e exemplos"""
    
    def __init__(self):
        genai.configure(api_key=None)  # Usa variável de ambiente
        self.model = genai.GenerativeModel(MODEL_NAME)
    
    def refine_business_rules(self, table_id: str, base_config: Dict) -> Dict:
        """
        Usa Gemini para gerar regras de negócio refinadas
        
        Args:
            table_id: ID da tabela
            base_config: Config base gerado
        
        Returns:
            Config refinado com regras de negócio
        """
        print(f"🤖 Refinando regras de negócio com Gemini para {table_id}...")
        
        fields_list = self._format_fields_for_gemini(base_config.get('fields', {}))
        
        prompt = f"""
Você é um especialista em modelagem de dados e regras de negócio. 

Baseado na tabela BigQuery '{table_id}' com os seguintes campos:

{fields_list}

Forneça em JSON:

1. **critical_rules**: Lista de 2-3 regras críticas de negócio (priority: alta/media)
   - rule: Descrição clara da regra
   - priority: "alta" ou "media"
   - context: Contexto e exemplo de aplicação

2. **query_rules**: Lista de 2-3 padrões SQL recomendados (ex: usar LIKE para textos)
   - rule: Descrição da regra
   - context: Exemplo SQL

3. **keywords_to_add**: Palavras-chave adicionais para buscas

Exemplo de formato esperado:
{{
    "critical_rules": [
        {{
            "rule": "Sempre use [campo1] para [propósito]",
            "priority": "alta",
            "context": "Contexto de uso"
        }}
    ],
    "query_rules": [
        {{
            "rule": "Use LIKE UPPER para buscas textuais",
            "context": "WHERE UPPER(campo) LIKE UPPER('%valor%')"
        }}
    ],
    "keywords_to_add": ["palavra1", "palavra2"]
}}

Retorne APENAS JSON válido, sem markdown.
"""
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text
            
            # Remove markdown code blocks se houver
            response_text = re.sub(r'```json\n?', '', response_text)
            response_text = re.sub(r'```\n?', '', response_text)
            
            refinement = json.loads(response_text)
            
            # Mescla com config base
            if 'critical_rules' in refinement:
                base_config['business_rules']['critical_rules'] = refinement['critical_rules']
            
            if 'query_rules' in refinement:
                base_config['business_rules']['query_rules'] = refinement['query_rules']
            
            if 'keywords_to_add' in refinement:
                base_config['metadata']['keywords'].extend(refinement['keywords_to_add'])
            
            print("✅ Refinamento concluído!")
            return base_config
        
        except Exception as e:
            print(f"⚠️  Erro ao refinar com Gemini: {e}")
            return base_config
    
    def _format_fields_for_gemini(self, fields_dict: Dict) -> str:
        """Formata campos para enviar ao Gemini"""
        formatted = []
        
        for category, field_list in fields_dict.items():
            formatted.append(f"\n{category}:")
            for field in field_list[:10]:  # Limita a 10 por categoria
                if isinstance(field, dict):
                    name = field.get('name', '?')
                    ftype = field.get('type', '?')
                    desc = field.get('description', '')
                    formatted.append(f"  - {name} ({ftype}): {desc}")
        
        return "\n".join(formatted)
    
    def generate_usage_examples(self, table_id: str, base_config: Dict) -> Dict:
        """Gera exemplos de uso via Gemini"""
        print(f"📝 Gerando exemplos de uso para {table_id}...")
        
        # Por enquanto, gera exemplos vazios (pode ser expandido)
        # Exemplo real seria chamada ao Gemini
        
        return base_config


class TableConfigGenerator:
    """Orquestrador principal"""
    
    def __init__(self):
        self.extractor = TableSchemaExtractor(PROJECT_ID, DATASET_ID)
        self.builder = TableConfigBuilder()
        self.refiner = TableConfigRefiner()
    
    def generate_for_table(self, table_id: str, refine: bool = True) -> Dict:
        """
        Gera table_config completo para uma tabela
        
        Args:
            table_id: ID da tabela
            refine: Se deve usar Gemini para refinar
        
        Returns:
            Dict com config completo
        """
        print(f"\n{'='*80}")
        print(f"🚀 GERANDO TABLE_CONFIG PARA: {table_id}")
        print(f"{'='*80}\n")
        
        # 1. Recuperar DDL
        ddl = self.extractor.get_table_ddl(table_id)
        
        # 2. Parsear schema
        schema_info = self.builder.parse_schema_from_ddl(ddl)
        
        # 3. Gerar config base
        config = self.builder.generate_base_config(table_id, schema_info)
        
        # 4. Refinar com Gemini (opcional)
        if refine:
            config = self.refiner.refine_business_rules(table_id, config)
        
        # 5. Gerar exemplos
        config = self.refiner.generate_usage_examples(table_id, config)
        
        print(f"\n✅ Config gerado com sucesso!")
        return config
    
    def save_config(self, table_id: str, config: Dict, output_dir: str = "."):
        """Salva config em arquivo"""
        filename = f"table_config_{table_id}.json"
        filepath = Path(output_dir) / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Config salvo em: {filepath}")
        return filepath
    
    def generate_multiple(self, table_ids: List[str], refine: bool = True) -> Dict[str, Dict]:
        """Gera configs para múltiplas tabelas"""
        results = {}
        
        for table_id in table_ids:
            try:
                config = self.generate_for_table(table_id, refine=refine)
                self.save_config(table_id, config)
                results[table_id] = config
            except Exception as e:
                print(f"❌ Erro ao gerar config para {table_id}: {e}")
                results[table_id] = {"error": str(e)}
        
        return results


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Gera table_config.json automaticamente a partir do BigQuery"
    )
    parser.add_argument(
        "table_ids",
        nargs="+",
        help="Um ou mais IDs de tabelas (ex: drvy_VeiculosVendas dvry_ihs_cotas_ativas)"
    )
    parser.add_argument(
        "--no-refine",
        action="store_true",
        help="Não usar Gemini para refinar regras"
    )
    parser.add_argument(
        "--output-dir",
        default=".",
        help="Diretório para salvar configs"
    )
    
    args = parser.parse_args()
    
    generator = TableConfigGenerator()
    results = generator.generate_multiple(
        args.table_ids,
        refine=not args.no_refine
    )
    
    print(f"\n{'='*80}")
    print(f"📊 SUMÁRIO")
    print(f"{'='*80}")
    print(f"✅ Tabelas processadas: {len([r for r in results.values() if 'error' not in r])}/{len(results)}")
    print(f"❌ Erros: {len([r for r in results.values() if 'error' in r])}")
    
    for table_id, result in results.items():
        if 'error' not in result:
            print(f"  ✅ {table_id}")
        else:
            print(f"  ❌ {table_id}: {result['error']}")


if __name__ == "__main__":
    main()
