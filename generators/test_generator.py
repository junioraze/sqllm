"""
Gerador Completo de Table Config com Gemini 2.5 Pro
Gera arquivo test_output_<table>.json com TODOS os campos necessarios
"""

import json
import sys
import os
from typing import Dict, List, Any
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import google_auth
import google.generativeai as genai
from google.cloud import bigquery
from config.settings import PROJECT_ID, DATASET_ID, TABLES_CONFIG


class CompleteTableConfigGenerator:
    """Gera arquivo test_output completo com TODOS os campos necessarios"""
    
    def __init__(self):
        self.project_id = PROJECT_ID
        self.dataset_id = DATASET_ID
        self.model_name = "gemini-2.5-pro"
        self.tables_config_path = self._find_config_path()
        
        if not self.tables_config_path:
            raise FileNotFoundError("tables_config.json nao encontrado")
        
        print(f"\n{'='*70}")
        print(f"GERADOR COMPLETO DE TABLE CONFIG")
        print(f"{'='*70}")
        print(f"Project: {self.project_id}")
        print(f"Dataset: {self.dataset_id}")
        print(f"Model:   {self.model_name}")
        print(f"{'='*70}\n")
        
        self.tables_config = self._load_config()
        self.model = genai.GenerativeModel(self.model_name)
        self.bq_client = bigquery.Client(project=self.project_id)
    
    def _find_config_path(self) -> str:
        """Multi-path lookup para tables_config.json"""
        possible_paths = [
            os.path.join(os.path.dirname(__file__), "..", "config", "tables_config.json"),
            os.path.join(os.getcwd(), "config", "tables_config.json"),
            "config/tables_config.json",
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return os.path.abspath(path)
        return None
    
    def _load_config(self) -> Dict[str, Any]:
        """Carrega tabelas do config"""
        with open(self.tables_config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _get_table_summary(self, table_id: str) -> Dict[str, Any]:
        """Consulta BigQuery para dados reais da tabela"""
        print(f"  Consultando BigQuery...")
        
        summary = {"row_count": 0, "sample_data": [], "error": None}
        
        try:
            table_ref = f"{self.project_id}.{self.dataset_id}.{table_id}"
            
            try:
                result = self.bq_client.query(f"SELECT COUNT(*) as cnt FROM `{table_ref}`").result()
                for row in result:
                    summary["row_count"] = row.cnt
                print(f"    Registros: {summary['row_count']:,}")
            except Exception as e:
                print(f"    Aviso: {e}")
            
            try:
                result = self.bq_client.query(f"SELECT * FROM `{table_ref}` LIMIT 3").result()
                for row in result:
                    summary["sample_data"].append(dict(row))
                print(f"    Amostra: OK")
            except Exception as e:
                print(f"    Aviso: {e}")
            
            return summary
        except Exception as e:
            summary["error"] = str(e)
            return summary
    
    def _generate_usage_examples(self, table_id: str, original_config: Dict[str, Any]) -> Dict[str, Any]:
        """Gera usage_examples com Gemini (tabela-level, não field-level)"""
        
        print(f"  Gerando exemplos de uso...")
        
        metadata = original_config.get("metadata", {})
        domain = metadata.get("domain", "")
        keywords = metadata.get("keywords", [])
        fields = original_config.get("fields", {})
        
        fields_text = ""
        for field_type, field_list in fields.items():
            if field_list:
                for field in field_list[:5]:  # Limita a 5 por categoria
                    name = field.get('name')
                    ftype = field.get('type')
                    fields_text += f"- {name} ({ftype})\n"
        
        prompt = f"""Gere exemplos de perguntas de negócio para BigQuery.

TABELA: {table_id}
DOMINIO: {domain}
TOP KEYWORDS: {', '.join(keywords[:8]) if keywords else 'N/A'}

CAMPOS DISPONIVEIS:
{fields_text}

Retorne JSON com 3-5 exemplos por categoria (APENAS perguntas curtas):

{{
  "ranking_queries": [
    {{"question": "Top 5 ...", "short_desc": "..."}}
  ],
  "temporal_analysis": [
    {{"question": "Evolução mensal de...", "short_desc": "..."}}
  ],
  "search_examples": [
    {{"question": "Buscar registros...", "short_desc": "..."}}
  ]
}}

RETORNE APENAS JSON, SEM EXPLICACOES.
"""
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text
            
            import re
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                result = json.loads(json_match.group())
                print(f"    OK")
                return result
            return {"ranking_queries": [], "temporal_analysis": [], "search_examples": []}
        except Exception as e:
            print(f"    Erro: {e}")
            return {"ranking_queries": [], "temporal_analysis": [], "search_examples": []}
    
    def _generate_complete_config(self, table_id: str, original_config: Dict[str, Any]) -> Dict[str, Any]:
        """Usa Gemini para gerar config COMPLETO - apenas campos necessarios pro RAG"""
        
        print(f"  Chamando Gemini 2.5 Pro...")
        
        metadata = original_config.get("metadata", {})
        domain = metadata.get("domain", "")
        keywords = metadata.get("keywords", [])
        fields = original_config.get("fields", {})
        
        fields_text = ""
        for field_type, field_list in fields.items():
            if field_list:
                fields_text += f"{field_type}:\n"
                for field in field_list:
                    name = field.get('name')
                    ftype = field.get('type')
                    fields_text += f"  - {name} ({ftype})\n"
        
        prompt = f"""Voce eh um especialista em data engineering. Gere um table_config.json com APENAS campos necessarios.

TABELA: {table_id}
DOMINIO: {domain}
KEYWORDS: {', '.join(keywords[:8]) if keywords else 'N/A'}

CAMPOS:{fields_text}

Para CADA campo, retorne JSON com:
- name (string)
- type (string)
- description (string, max 70 chars em PORTUGUES)

SE field_type = STRING: SEMPRE adicione search_pattern (sql LIKE pattern)
SE field_type = TIMESTAMP/DATE: SEMPRE adicione conversion (sql CAST/PARSE)
SE field_type = FLOAT64/INT64: SEMPRE adicione aggregations (lista de operadores: SUM, AVG, MAX, MIN, COUNT)

NÃO inclua "examples" em fields - examples sao gerados SEPARADAMENTE em usage_examples!

FORMATO OBRIGATORIO:
{{
  "temporal_fields": [
    {{
      "name": "data_venda",
      "type": "DATE",
      "description": "Data em que a venda foi realizada",
      "conversion": "SAFE_CAST(data_venda AS DATE)"
    }}
  ],
  "dimension_fields": [
    {{
      "name": "modelo",
      "type": "STRING",
      "description": "Modelo do veiculo vendido",
      "search_pattern": "UPPER(modelo) LIKE UPPER('%{{valor}}%')"
    }}
  ],
  "metric_fields": [
    {{
      "name": "valor_venda",
      "type": "FLOAT64",
      "description": "Valor total da venda em reais",
      "aggregations": ["SUM", "AVG", "MAX", "MIN"]
    }}
  ],
  "filter_fields": []
}}

RETORNE APENAS JSON, SEM EXPLICACOES.
"""
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text
            
            import re
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                result = json.loads(json_match.group())
                print(f"    OK")
                return result
            return {}
        except Exception as e:
            print(f"    Erro: {e}")
            return {}
    
    def generate(self, table_id: str) -> None:
        """Gera arquivo de teste completo"""
        
        if table_id not in self.tables_config:
            print(f"Erro: Tabela '{table_id}' nao existe")
            return
        
        print(f"\nGerando: {table_id}")
        print(f"{'='*70}")
        
        original = self.tables_config[table_id]
        
        print(f"1. Consultando BigQuery...")
        summary = self._get_table_summary(table_id)
        
        print(f"2. Gerando campos com Gemini...")
        generated = self._generate_complete_config(table_id, original)
        
        if not generated:
            print(f"Erro: Nao foi possivel gerar config")
            return
        
        print(f"3. Gerando exemplos de uso...")
        usage_examples = self._generate_usage_examples(table_id, original)
        
        print(f"4. Salvando resultado...")
        
        final = {
            "metadata": original.get("metadata", {}),
            "business_rules": original.get("business_rules", {
                "critical_rules": [],
                "query_rules": []
            }),
            "fields": generated,
            "usage_examples": usage_examples,
            "generation": {
                "model": self.model_name,
                "source": "bigquery",
                "row_count": summary.get("row_count"),
                "timestamp": self._get_timestamp()
            }
        }
        
        output_file = f"test_output_{table_id}.json"
        output_path = os.path.join(os.path.dirname(__file__), output_file)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(final, f, indent=2, ensure_ascii=False)
        
        print(f"\nSUCESSO!")
        print(f"Arquivo: {output_file}")
        total_fields = sum(len(v) for v in generated.values())
        print(f"Campos: {total_fields}")
        print(f"Exemplos: {sum(len(v) if isinstance(v, list) else 0 for v in usage_examples.values())} perguntas")
    
    def _get_timestamp(self) -> str:
        from datetime import datetime
        return datetime.now().isoformat()


def main():
    parser = argparse.ArgumentParser(
        description="Gera table_config.json COMPLETO com Gemini 2.5 Pro"
    )
    parser.add_argument("--table", type=str, required=True, help="Tabela para processar")
    
    args = parser.parse_args()
    
    try:
        gen = CompleteTableConfigGenerator()
        gen.generate(args.table)
        
        print(f"\n{'='*70}")
        print(f"PRONTO! Revise o arquivo e integre ao seu workflow.")
        print(f"{'='*70}")
        
    except Exception as e:
        print(f"\nERRO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
