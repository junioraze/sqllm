#!/usr/bin/env python3
"""
SINCRONIZADOR DE ARQUIVOS COMPARTILHADOS
Sincroniza APENAS arquivos que DEVEM SER IDÊNTICOS entre projetos
Respeita: credenciais, configs específicas, dados locais
"""

import os
import sys
import shutil
from pathlib import Path
from typing import List, Dict

class SharedFileSyncer:
    """Sincroniza arquivos compartilhados entre projetos"""
    
    # Arquivos que DEVEM ser iguais em todos os projetos
    # Estrutura: "caminho/arquivo.py" -> "descrição"
    SHARED_FILES = {
        # Raiz
        "requirements.txt": "Dependências Python",
        "README.md": "Documentação principal",
        
        # Config
        "config/google_auth.py": "Autenticação Google",
        "config/settings.py": "Variáveis de projeto",
        
        # RAG System
        "rag_system/manager.py": "RAG Manager singleton",
        "rag_system/business_metadata_rag.py": "RAG v2",
        "rag_system/business_metadata_rag_v3.py": "RAG v3",
        
        # Utils
        "utils/logger.py": "Logger centralizado",
        "utils/prompt_rules.py": "Regras de prompts",
        
        # Generators
        "generators/test_generator.py": "Gerador de configs",
        
        # LLM Handlers
        "llm_handlers/gemini_handler.py": "Handler Gemini",
        
        # Tools
        "tools/sync_shared.py": "Ferramenta de sync",
        "tools/validate_migration.py": "Validador",
    }
    
    # Arquivos que NÃO devem ser sincronizados
    LOCAL_FILES = {
        "config/tables_config.json",  # Específico de cada projeto
        "config/client_config.json",  # UI config
        "config/credentials.json",    # Credenciais
        "gl.json",                    # Credenciais Google
        "cache.db",                   # Cache local
        "cache.ann",                  # Embeddings
        "cache.meta.json",            # Metadados cache
        "rate_limit_state.json",      # Estado local
    }
    
    def __init__(self, source: str, targets: List[str]):
        self.source = Path(source)
        self.targets = [Path(t) for t in targets]
        self.synced = []
        self.failed = []
        self.skipped = []
    
    def sync_all(self, dry_run: bool = False) -> Dict:
        """Sincronizar todos os arquivos compartilhados"""
        
        print(f"\n{'='*70}")
        print(f"SINCRONIZADOR DE ARQUIVOS COMPARTILHADOS")
        print(f"{'='*70}")
        print(f"Modo: {'DRY RUN (simulação)' if dry_run else 'EXECUÇÃO REAL'}")
        print(f"Origem: {self.source.name}")
        print(f"Destinos: {len(self.targets)} projetos\n")
        
        for target in self.targets:
            self._sync_to_target(target, dry_run)
        
        self._print_summary()
        
        return {
            "synced": len(self.synced),
            "failed": len(self.failed),
            "skipped": len(self.skipped),
            "details": {
                "synced": self.synced,
                "failed": self.failed,
                "skipped": self.skipped,
            }
        }
    
    def _sync_to_target(self, target: Path, dry_run: bool):
        """Sincronizar para um projeto alvo"""
        
        if not target.exists():
            print(f"⚠️  {target.name}: Pasta não existe")
            self.skipped.append(f"{target.name}: não encontrado")
            return
        
        print(f"Sincronizando: {self.source.name} → {target.name}")
        
        for file_path, description in self.SHARED_FILES.items():
            src = self.source / file_path
            dst = target / file_path
            
            if not src.exists():
                print(f"  ⚠️  {file_path} não existe na origem - pulando")
                self.skipped.append(f"{target.name}/{file_path}")
                continue
            
            try:
                # Criar pasta destino se não existir
                dst.parent.mkdir(parents=True, exist_ok=True)
                
                if dry_run:
                    print(f"  [DRY] {file_path:40} {description}")
                    self.skipped.append(f"[DRY] {target.name}/{file_path}")
                else:
                    shutil.copy2(src, dst)
                    print(f"  ✓ {file_path:40} {description}")
                    self.synced.append(f"{target.name}/{file_path}")
            
            except Exception as e:
                print(f"  ✗ {file_path:40} ERRO: {e}")
                self.failed.append(f"{target.name}/{file_path}: {e}")
        
        print()
    
    def _print_summary(self):
        """Imprimir resumo"""
        print(f"{'='*70}")
        print(f"RESUMO")
        print(f"{'='*70}\n")
        
        print(f"✓ Sincronizados: {len(self.synced)}")
        print(f"⚠️  Pulados: {len(self.skipped)}")
        print(f"✗ Erros: {len(self.failed)}\n")
        
        if self.failed:
            print("Erros encontrados:")
            for error in self.failed:
                print(f"  - {error}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Sincronizar arquivos compartilhados entre projetos"
    )
    parser.add_argument(
        "--source",
        default="/home/Junio/gl_sqllm",
        help="Projeto origem (default: gl_sqllm)"
    )
    parser.add_argument(
        "--targets",
        nargs="+",
        help="Projetos destino (default: todos exceto source)"
    )
    parser.add_argument(
        "--base",
        default="/home/Junio",
        help="Base para encontrar projetos"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simular sem fazer alterações"
    )
    parser.add_argument(
        "--list-files",
        action="store_true",
        help="Listar arquivos compartilhados"
    )
    
    args = parser.parse_args()
    
    # Listar arquivos?
    if args.list_files:
        print("\n📋 ARQUIVOS COMPARTILHADOS:\n")
        for file_path, description in SharedFileSyncer.SHARED_FILES.items():
            print(f"  {file_path:40} - {description}")
        print()
        return
    
    # Encontrar targets se não especificado
    if not args.targets:
        base = Path(args.base)
        all_projects = [str(p) for p in base.iterdir() 
                       if p.is_dir() and 'sqllm' in p.name.lower()]
        args.targets = [p for p in all_projects if p != args.source]
    
    # Sincronizar
    syncer = SharedFileSyncer(args.source, args.targets)
    result = syncer.sync_all(dry_run=args.dry_run)
    
    sys.exit(0 if len(result["failed"]) == 0 else 1)


if __name__ == "__main__":
    main()
