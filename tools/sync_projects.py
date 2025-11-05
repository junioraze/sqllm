#!/usr/bin/env python3
"""
SINCRONIZADOR DE PROJETOS
Sincroniza alterações entre o projeto master (gl_sqllm) e todos os outros
"""

import os
import sys
import shutil
import json
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass

@dataclass
class SyncReport:
    """Relatório de sincronização"""
    source_project: str
    target_projects: List[str]
    files_synced: int
    folders_synced: int
    errors: List[str]
    timestamp: str

class ProjectSynchronizer:
    """Sincroniza arquivos entre projetos"""
    
    # Arquivos que devem estar sincronizados
    SYNC_PATTERNS = {
        'config/': ['settings.py', '__init__.py', 'google_auth.py'],
        'rag_system/': ['manager.py', '__init__.py'],
        'utils/': ['logger.py', '__init__.py'],
        'generators/': ['test_generator.py', '__init__.py'],
        'tools/': ['migration_tool.py', 'validate_migration.py', 'sync_projects.py'],
        'root': ['.gitignore', 'requirements.txt', 'README.md'],
    }
    
    def __init__(self, source_project: str, target_projects: List[str]):
        self.source_project = Path(source_project)
        self.target_projects = [Path(p) for p in target_projects]
    
    def sync_all(self, dry_run: bool = True) -> SyncReport:
        """Sincronizar todos os projetos"""
        
        print(f"\n{'='*70}")
        print(f"SINCRONIZADOR DE PROJETOS")
        print(f"{'='*70}")
        print(f"Modo: {'DRY RUN' if dry_run else 'EXECUÇÃO REAL'}\n")
        
        files_synced = 0
        folders_synced = 0
        errors = []
        
        for target in self.target_projects:
            print(f"\nSincronizando: {self.source_project.name} → {target.name}")
            print(f"{'-'*70}")
            
            for pattern, files in self.SYNC_PATTERNS.items():
                if pattern == 'root':
                    for filename in files:
                        src = self.source_project / filename
                        dst = target / filename
                        
                        if src.exists():
                            if self._sync_file(src, dst, dry_run):
                                files_synced += 1
                                print(f"  ✓ {filename}")
                else:
                    folder_path = pattern.rstrip('/')
                    src_folder = self.source_project / folder_path
                    dst_folder = target / folder_path
                    
                    if src_folder.exists():
                        for filename in files:
                            src = src_folder / filename
                            dst = dst_folder / filename
                            
                            if src.exists():
                                if self._sync_file(src, dst, dry_run):
                                    files_synced += 1
                                    print(f"  ✓ {pattern}{filename}")
        
        from datetime import datetime
        return SyncReport(
            source_project=self.source_project.name,
            target_projects=[p.name for p in self.target_projects],
            files_synced=files_synced,
            folders_synced=0,
            errors=errors,
            timestamp=datetime.now().isoformat()
        )
    
    def _sync_file(self, src: Path, dst: Path, dry_run: bool) -> bool:
        """Sincronizar um arquivo"""
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            
            if not dry_run:
                shutil.copy2(src, dst)
            
            return True
        except Exception as e:
            print(f"    Erro ao sincronizar {src.name}: {e}")
            return False


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Sincronizar projetos")
    parser.add_argument(
        "--source",
        type=str,
        default="/home/Junio/gl_sqllm",
        help="Projeto source (master)"
    )
    parser.add_argument(
        "--targets",
        nargs="+",
        help="Projetos alvo para sincronizar"
    )
    parser.add_argument(
        "--base",
        type=str,
        default="/home/Junio",
        help="Base para encontrar todos os projetos"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Executar sincronização real"
    )
    
    args = parser.parse_args()
    
    # Encontrar targets se não especificado
    if not args.targets:
        base = Path(args.base)
        all_projects = sorted([str(p) for p in base.iterdir() if 'sqllm' in p.name.lower()])
        args.targets = [p for p in all_projects if p != args.source]
    
    sync = ProjectSynchronizer(args.source, args.targets)
    report = sync.sync_all(dry_run=not args.execute)
    
    print(f"\n{'='*70}")
    print(f"RELATÓRIO")
    print(f"{'='*70}")
    print(f"Arquivos sincronizados: {report.files_synced}")


if __name__ == "__main__":
    main()
