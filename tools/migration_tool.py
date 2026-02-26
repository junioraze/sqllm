#!/usr/bin/env python3
"""
FERRAMENTA DE SINCRONIZAÇÃO SIMPLES
Sincroniza APENAS arquivos que devem ser iguais entre projetos
Preserva: credenciais, configs específicas de projeto, dados locais
"""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class SyncReport:
    """Relatório de sincronização"""
    source: str
    target: str
    files_synced: List[str]
    status: str  # "success", "error"
    errors: List[str]
    timestamp: str

class ProjectSyncer:
    """Migra um projeto para a nova estrutura"""
    
    # Novo padrão de pastas
    NEW_STRUCTURE = {
        'config': ['settings.py', 'google_auth.py', '__init__.py'],
        'database': ['__init__.py'],
        'llm_handlers': ['__init__.py'],
        'rag_system': ['__init__.py', 'manager.py'],
        'ui': ['__init__.py'],
        'utils': ['__init__.py'],
        'tests': ['__init__.py'],
        'generators': ['__init__.py'],
        'docs': [],
        'etc': []
    }
    
    # Mapeamento de arquivos por categoria
    FILE_CATEGORIES = {
        'config': ['config.py', 'settings.py', 'config_menu.py', 'payment_config.json', 'client_config.json'],
        'database': ['database.py', 'cache_db.py', 'user_database.py', 'subscription_system_db.py', 'payment_ui_db.py', 'query_cache.py'],
        'llm_handlers': ['gemini_handler.py', 'deepseek_theme.py'],
        'rag_system': ['business_metadata_rag.py', 'business_metadata_rag_v3.py', 'sql_pattern_rag.py', 'manager.py'],
        'utils': ['utils.py', 'logger.py', 'image_utils.py', 'auth_system.py', 'message_handler.py', 'rate_limit.py', 'ai_metrics.py', 'prompt_rules.py'],
        'generators': ['table_config_generator.py', 'test_generator.py'],
        'tests': ['test_rag_local.py', 'test_backend_flow.py'],
    }
    
    def __init__(self, project_path: str, dry_run: bool = True):
        self.project_path = Path(project_path)
        self.dry_run = dry_run
        self.report = MigrationReport(
            project_name=self.project_path.name,
            source_path=str(self.project_path),
            status="pending",
            actions=[],
            imports_updated=0,
            files_moved=0,
            files_created=0,
            errors=[],
            timestamp=datetime.now().isoformat()
        )
    
    def run(self) -> MigrationReport:
        """Executar migração completa"""
        try:
            print(f"\n{'='*70}")
            print(f"MIGRANDO: {self.project_path.name}")
            print(f"{'='*70}")
            print(f"Modo: {'DRY RUN' if self.dry_run else 'EXECUÇÃO REAL'}\n")
            
            # 1. Validar projeto
            if not self._validate_project():
                self.report.status = "skipped"
                return self.report
            
            # 2. Detectar estrutura atual
            current_structure = self._detect_current_structure()
            self.report.actions.append(f"Estrutura atual detectada: {current_structure}")
            
            # 3. Criar nova estrutura de pastas
            self._create_folder_structure()
            
            # 4. Mover arquivos
            self._move_files()
            
            # 5. Atualizar imports
            self._update_imports()
            
            # 6. Criar arquivos faltantes
            self._create_missing_files()
            
            self.report.status = "completed"
            print(f"\n✅ {self.project_path.name} migrado com sucesso!")
            
        except Exception as e:
            self.report.status = "failed"
            self.report.errors.append(str(e))
            print(f"\n❌ Erro: {e}")
        
        return self.report
    
    def _validate_project(self) -> bool:
        """Validar se é um projeto válido"""
        if not self.project_path.exists():
            self.report.errors.append(f"Pasta não existe: {self.project_path}")
            return False
        
        # Verificar se tem arquivo principal
        main_files = list(self.project_path.glob("main.py")) + \
                     list(self.project_path.glob("app.py")) + \
                     list(self.project_path.glob("run.py"))
        
        if not main_files:
            self.report.errors.append("Arquivo main.py/app.py/run.py não encontrado")
            return False
        
        return True
    
    def _detect_current_structure(self) -> str:
        """Detectar estrutura atual do projeto"""
        py_files = list(self.project_path.glob("*.py"))
        folders = [f.name for f in self.project_path.iterdir() if f.is_dir() and not f.name.startswith('.')]
        
        return f"{len(py_files)} arquivos .py, {len(folders)} pastas"
    
    def _create_folder_structure(self):
        """Criar nova estrutura de pastas"""
        for folder in self.NEW_STRUCTURE.keys():
            folder_path = self.project_path / folder
            
            if not folder_path.exists():
                if self.dry_run:
                    self.report.actions.append(f"[DRY] Criaria pasta: {folder}")
                else:
                    folder_path.mkdir(parents=True, exist_ok=True)
                    self.report.files_created += 1
                    self.report.actions.append(f"Pasta criada: {folder}")
            
            # Criar __init__.py se não existir
            init_file = folder_path / "__init__.py"
            if not init_file.exists():
                if self.dry_run:
                    self.report.actions.append(f"[DRY] Criaria: {folder}/__init__.py")
                else:
                    init_file.write_text("# Auto-generated package\n")
                    self.report.files_created += 1
    
    def _move_files(self):
        """Mover arquivos para as pastas corretas"""
        for category, files in self.FILE_CATEGORIES.items():
            category_path = self.project_path / category
            
            for filename in files:
                src = self.project_path / filename
                dst = category_path / filename
                
                if src.exists() and not dst.exists():
                    if self.dry_run:
                        self.report.actions.append(f"[DRY] Moveria: {filename} → {category}/")
                    else:
                        shutil.move(str(src), str(dst))
                        self.report.files_moved += 1
                        self.report.actions.append(f"Arquivo movido: {filename} → {category}/")
    
    def _update_imports(self):
        """Atualizar imports em todos os arquivos Python"""
        # Mapeamento de imports antigos → novos
        import_map = {
            r'from\s+config\s+import': 'from config.settings import',
            r'from\s+database\s+import': 'from database import',
            r'from\s+gemini_handler\s+import': 'from llm_handlers.gemini_handler import',
            r'from\s+business_metadata_rag\s+import': 'from rag_system.business_metadata_rag import',
            r'from\s+business_metadata_rag_v3\s+import': 'from rag_system.business_metadata_rag_v3 import',
            r'from\s+logger\s+import': 'from utils.logger import',
            r'from\s+utils\s+import': 'from utils import',
            r'import\s+logger': 'from utils from utils import logger',
            r'import\s+gemini_handler': 'from llm_handlers from llm_handlers import gemini_handler',
        }
        
        py_files = list(self.project_path.rglob("*.py"))
        
        for py_file in py_files:
            try:
                content = py_file.read_text(encoding='utf-8')
                original_content = content
                
                for old_pattern, new_import in import_map.items():
                    content = re.sub(old_pattern, new_import, content)
                
                if content != original_content:
                    if self.dry_run:
                        self.report.actions.append(f"[DRY] Atualizaria imports: {py_file.name}")
                    else:
                        py_file.write_text(content, encoding='utf-8')
                        self.report.imports_updated += 1
                        self.report.actions.append(f"Imports atualizados: {py_file.name}")
            
            except Exception as e:
                self.report.errors.append(f"Erro ao atualizar {py_file.name}: {e}")
    
    def _create_missing_files(self):
        """Criar arquivos faltantes como __init__.py"""
        for folder in self.NEW_STRUCTURE.keys():
            folder_path = self.project_path / folder
            init_file = folder_path / "__init__.py"
            
            if not init_file.exists():
                if not self.dry_run:
                    init_file.write_text("# Package\n")
                    self.report.files_created += 1


class MultiProjectMigrator:
    """Migra múltiplos projetos"""
    
    def __init__(self, base_path: str = "/home/Junio", dry_run: bool = True):
        self.base_path = Path(base_path)
        self.dry_run = dry_run
        self.projects = self._find_projects()
        self.reports: List[MigrationReport] = []
    
    def _find_projects(self) -> List[Path]:
        """Encontrar todos os projetos SQLLM"""
        projects = []
        
        for item in self.base_path.iterdir():
            if item.is_dir() and 'sqllm' in item.name.lower():
                projects.append(item)
        
        return sorted(projects)
    
    def run_all(self) -> List[MigrationReport]:
        """Migrar todos os projetos"""
        print(f"\n{'='*70}")
        print(f"FERRAMENTA DE MIGRAÇÃO EM LOTE")
        print(f"{'='*70}")
        print(f"Base: {self.base_path}")
        print(f"Projetos encontrados: {len(self.projects)}")
        print(f"Modo: {'DRY RUN' if self.dry_run else 'EXECUÇÃO REAL'}\n")
        
        for project_path in self.projects:
            migrator = ProjectMigrator(project_path, dry_run=self.dry_run)
            report = migrator.run()
            self.reports.append(report)
        
        self._print_summary()
        return self.reports
    
    def _print_summary(self):
        """Imprimir resumo final"""
        print(f"\n{'='*70}")
        print(f"RESUMO DA MIGRAÇÃO")
        print(f"{'='*70}\n")
        
        for report in self.reports:
            status_icon = "✅" if report.status == "completed" else "⚠️" if report.status == "skipped" else "❌"
            print(f"{status_icon} {report.project_name:20} {report.status:12}")
            print(f"   Arquivos: {report.files_moved} movidos, {report.files_created} criados")
            print(f"   Imports:  {report.imports_updated} atualizados")
            if report.errors:
                print(f"   Erros:    {len(report.errors)}")
            print()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Ferramenta de Migração de Projetos SQLLM")
    parser.add_argument(
        "--project",
        type=str,
        help="Projeto específico para migrar (ex: /home/Junio/fa_sqllm)"
    )
    parser.add_argument(
        "--base",
        type=str,
        default="/home/Junio",
        help="Diretório base para buscar projetos (padrão: /home/Junio)"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Executar migração real (sem --execute, apenas simula)"
    )
    parser.add_argument(
        "--save-report",
        type=str,
        help="Salvar relatório em JSON"
    )
    
    args = parser.parse_args()
    
    if args.project:
        # Migrar projeto específico
        migrator = ProjectMigrator(args.project, dry_run=not args.execute)
        report = migrator.run()
        
        if args.save_report:
            with open(args.save_report, 'w') as f:
                json.dump(asdict(report), f, indent=2)
    else:
        # Migrar todos os projetos
        multi = MultiProjectMigrator(base_path=args.base, dry_run=not args.execute)
        reports = multi.run_all()
        
        if args.save_report:
            with open(args.save_report, 'w') as f:
                json.dump([asdict(r) for r in reports], f, indent=2)


if __name__ == "__main__":
    main()
