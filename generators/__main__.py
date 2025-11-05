#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║     TABLE CONFIG GENERATOR - CLI Helper                                   ║
║                                                                           ║
║  Uso:                                                                     ║
║  $ python -m generators drvy_VeiculosVendas                              ║
║  $ python -m generators --list                                            ║
║  $ python -m generators --validate table_config_xyz.json                 ║
║  $ python -m generators --merge tables_config.json                       ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
"""

import sys
import json
from pathlib import Path
from typing import List

# 🔐 Configurar Google Auth PRIMEIRO (antes de google.cloud)
from config import google_auth

from google.cloud import bigquery
from config.settings import PROJECT_ID, DATASET_ID
from .table_config_generator import TableConfigGenerator


def list_available_tables() -> List[str]:
    """Lista todas as tabelas disponíveis no dataset"""
    print(f"📋 Listando tabelas em {PROJECT_ID}.{DATASET_ID}...\n")
    
    client = bigquery.Client(project=PROJECT_ID)
    
    query = f"""
    SELECT table_name
    FROM `{PROJECT_ID}.{DATASET_ID}.INFORMATION_SCHEMA.TABLES`
    WHERE table_schema = '{DATASET_ID}'
    ORDER BY table_name
    """
    
    try:
        result = client.query(query).result()
        tables = [row.table_name for row in result]
        
        print(f"✅ Encontradas {len(tables)} tabelas:\n")
        for i, table in enumerate(tables, 1):
            print(f"  {i:2d}. {table}")
        
        return tables
    except Exception as e:
        print(f"❌ Erro ao listar tabelas: {e}")
        return []


def validate_config(config_path: str) -> bool:
    """Valida estrutura de um table_config.json"""
    print(f"🔍 Validando {config_path}...\n")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Validações básicas
        required_keys = ['metadata', 'business_rules', 'fields', 'usage_examples']
        missing_keys = [k for k in required_keys if k not in config]
        
        if missing_keys:
            print(f"❌ Chaves faltantes: {missing_keys}")
            return False
        
        # Validar metadata
        metadata_required = ['table_id', 'bigquery_table', 'description', 'domain', 'keywords']
        metadata_missing = [k for k in metadata_required if k not in config['metadata']]
        
        if metadata_missing:
            print(f"⚠️  Metadata incompleta. Faltam: {metadata_missing}")
        else:
            print(f"✅ Metadata: OK")
        
        # Validar fields
        fields_required = ['temporal_fields', 'dimension_fields', 'metric_fields', 'filter_fields']
        fields_missing = [k for k in fields_required if k not in config['fields']]
        
        if fields_missing:
            print(f"⚠️  Fields incompleto. Faltam: {fields_missing}")
        else:
            print(f"✅ Fields: OK ({sum(len(config['fields'][k]) for k in fields_required)} campos)")
        
        # Validar business_rules
        if config.get('business_rules'):
            rules_count = len(config['business_rules'].get('critical_rules', []))
            print(f"✅ Business Rules: OK ({rules_count} regras críticas)")
        
        print(f"\n✅ Config válido!")
        return True
    
    except json.JSONDecodeError as e:
        print(f"❌ JSON inválido: {e}")
        return False
    except FileNotFoundError:
        print(f"❌ Arquivo não encontrado: {config_path}")
        return False
    except Exception as e:
        print(f"❌ Erro ao validar: {e}")
        return False


def merge_configs(output_file: str = "tables_config.json", input_dir: str = ".") -> bool:
    """Mescla múltiplos table_config_*.json em um único tables_config.json"""
    print(f"🔗 Mesclando configs de {input_dir}...\n")
    
    config_files = list(Path(input_dir).glob("table_config_*.json"))
    
    if not config_files:
        print(f"❌ Nenhum arquivo table_config_*.json encontrado em {input_dir}")
        return False
    
    merged = {}
    
    for config_file in config_files:
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            table_id = config.get('metadata', {}).get('table_id')
            if not table_id:
                print(f"⚠️  Pulando {config_file.name} - sem table_id")
                continue
            
            merged[table_id] = config
            print(f"✅ {table_id} mesclado")
        
        except Exception as e:
            print(f"❌ Erro ao processar {config_file.name}: {e}")
    
    # Salvar arquivo mesclado
    output_path = Path(input_dir) / output_file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Config mesclado salvo em: {output_path}")
    print(f"   Total de tabelas: {len(merged)}")
    
    return True


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="CLI Helper para Table Config Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  # Gerar config para uma tabela
  python -m generators drvy_VeiculosVendas
  
  # Gerar para múltiplas tabelas
  python -m generators dvry_ihs_cotas_ativas dvry_ihs_qualidade_vendas_historico
  
  # Listar tabelas disponíveis
  python -m generators --list
  
  # Validar config gerado
  python -m generators --validate table_config_drvy_VeiculosVendas.json
  
  # Mesclar configs individuais em um único arquivo
  python -m generators --merge tables_config.json
        """
    )
    
    parser.add_argument(
        "table_ids",
        nargs="*",
        help="IDs das tabelas para gerar config"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Listar todas as tabelas disponíveis"
    )
    parser.add_argument(
        "--validate",
        metavar="FILE",
        help="Validar um arquivo table_config.json"
    )
    parser.add_argument(
        "--merge",
        metavar="OUTPUT_FILE",
        nargs="?",
        const="tables_config.json",
        help="Mesclar configs individuais (padrão: tables_config.json)"
    )
    parser.add_argument(
        "--no-refine",
        action="store_true",
        help="Não usar Gemini para refinar (mais rápido)"
    )
    parser.add_argument(
        "--output-dir",
        default=".",
        help="Diretório para salvar configs"
    )
    
    args = parser.parse_args()
    
    # --list
    if args.list:
        list_available_tables()
        return
    
    # --validate
    if args.validate:
        validate_config(args.validate)
        return
    
    # --merge
    if args.merge:
        merge_configs(args.merge, args.output_dir)
        return
    
    # Gerar configs
    if not args.table_ids:
        print("❌ Nenhuma tabela especificada!")
        print("\nUse:")
        print("  python -m generators <table_id> [<table_id2> ...]")
        print("  python -m generators --list")
        sys.exit(1)
    
    print(f"\n{'='*80}")
    print(f"🚀 TABLE CONFIG GENERATOR")
    print(f"{'='*80}\n")
    
    generator = TableConfigGenerator()
    
    for table_id in args.table_ids:
        try:
            print(f"\n{'─'*80}")
            config = generator.generate_for_table(table_id, refine=not args.no_refine)
            generator.save_config(table_id, config, args.output_dir)
            print(f"✅ {table_id}: OK")
        
        except Exception as e:
            print(f"❌ {table_id}: ERRO")
            print(f"   {e}")
    
    print(f"\n{'='*80}")
    print(f"💡 Próximas etapas:")
    print(f"  1. Revisar os arquivos table_config_*.json gerados")
    print(f"  2. Validar com: python -m generators --validate table_config_*.json")
    print(f"  3. Mesclar com: python -m generators --merge")
    print(f"  4. Substituir tables_config.json original pelo novo")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
