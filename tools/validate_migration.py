#!/usr/bin/env python3
"""
VERIFICADOR DE MIGRAÇÃO
Valida que cada projeto foi migrado corretamente
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple

class MigrationValidator:
    """Valida a estrutura de um projeto após migração"""
    
    REQUIRED_FOLDERS = {
        'config', 'database', 'llm_handlers', 'rag_system', 
        'ui', 'utils', 'tests', 'generators'
    }
    
    REQUIRED_FILES = {
        'config': ['settings.py', '__init__.py'],
        'database': ['__init__.py'],
        'llm_handlers': ['__init__.py'],
        'rag_system': ['__init__.py'],
        'utils': ['__init__.py'],
        'tests': ['__init__.py'],
        'generators': ['__init__.py'],
    }
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.project_name = self.project_path.name
        self.issues: List[str] = []
        self.warnings: List[str] = []
        self.checks_passed = 0
        self.checks_failed = 0
    
    def validate(self) -> bool:
        """Validar projeto"""
        print(f"\n{'='*70}")
        print(f"VALIDANDO: {self.project_name}")
        print(f"{'='*70}\n")
        
        # 1. Validar pastas
        self._check_folders()
        
        # 2. Validar arquivos
        self._check_files()
        
        # 3. Validar imports
        self._check_imports()
        
        # 4. Validar arquivos raiz antigos
        self._check_legacy_files()
        
        # Imprimir resultado
        self._print_report()
        
        return len(self.issues) == 0
    
    def _check_folders(self):
        """Verificar se as pastas existem"""
        print("Verificando pastas...")
        
        for folder in self.REQUIRED_FOLDERS:
            folder_path = self.project_path / folder
            
            if folder_path.exists():
                print(f"  ✅ {folder}/")
                self.checks_passed += 1
            else:
                print(f"  ❌ {folder}/ - NÃO ENCONTRADA")
                self.issues.append(f"Pasta faltante: {folder}")
                self.checks_failed += 1
    
    def _check_files(self):
        """Verificar se os arquivos necessários existem"""
        print("\nVerificando arquivos...")
        
        for folder, files in self.REQUIRED_FILES.items():
            folder_path = self.project_path / folder
            
            for filename in files:
                file_path = folder_path / filename
                
                if file_path.exists():
                    print(f"  ✅ {folder}/{filename}")
                    self.checks_passed += 1
                else:
                    print(f"  ⚠️  {folder}/{filename} - faltando")
                    self.warnings.append(f"Arquivo faltante: {folder}/{filename}")
                    self.checks_failed += 1
    
    def _check_imports(self):
        """Verificar se os imports foram atualizados"""
        print("\nVerificando imports em 5 arquivos principais...")
        
        py_files = list(self.project_path.rglob("*.py"))[:5]
        bad_imports = 0
        
        for py_file in py_files:
            try:
                content = py_file.read_text(encoding='utf-8', errors='ignore')
                
                # Detectar imports antigos
                old_patterns = [
                    r'from\s+config\s+import',
                    r'from\s+gemini_handler',
                    r'from\s+business_metadata_rag\s+import',
                ]
                
                import re
                has_old = False
                for pattern in old_patterns:
                    if re.search(pattern, content):
                        has_old = True
                        break
                
                if has_old:
                    print(f"  ⚠️  {py_file.name} - ainda tem imports antigos")
                    bad_imports += 1
                else:
                    print(f"  ✅ {py_file.name}")
                    self.checks_passed += 1
            
            except Exception as e:
                print(f"  ❌ {py_file.name} - erro ao ler")
        
        if bad_imports > 0:
            self.checks_failed += bad_imports
            self.warnings.append(f"{bad_imports} arquivo(s) com imports antigos")
    
    def _check_legacy_files(self):
        """Verificar se ainda há arquivos legados no raiz"""
        print("\nVerificando arquivos legados no raiz...")
        
        legacy_files = [
            'gemini_handler.py', 'business_metadata_rag.py', 
            'utils.py', 'logger.py', 'database.py', 'config.py'
        ]
        
        found_legacy = []
        for filename in legacy_files:
            file_path = self.project_path / filename
            if file_path.exists():
                found_legacy.append(filename)
        
        if found_legacy:
            print(f"  ⚠️  {len(found_legacy)} arquivo(s) legado(s) ainda no raiz:")
            for f in found_legacy:
                print(f"      - {f}")
            self.warnings.append(f"Arquivos legados no raiz: {', '.join(found_legacy)}")
        else:
            print(f"  ✅ Nenhum arquivo legado no raiz")
            self.checks_passed += 1
    
    def _print_report(self):
        """Imprimir relatório"""
        print(f"\n{'='*70}")
        print(f"RELATÓRIO")
        print(f"{'='*70}\n")
        
        print(f"Verificações: {self.checks_passed} OK, {self.checks_failed} com problemas")
        
        if self.issues:
            print(f"\n❌ PROBLEMAS CRÍTICOS ({len(self.issues)}):")
            for issue in self.issues:
                print(f"   • {issue}")
        
        if self.warnings:
            print(f"\n⚠️  AVISOS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   • {warning}")
        
        if not self.issues and not self.warnings:
            print(f"\n✅ TUDO OK! Projeto migrado com sucesso!\n")
        else:
            print()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Validar migração de projetos")
    parser.add_argument(
        "--project",
        type=str,
        help="Projeto para validar"
    )
    parser.add_argument(
        "--base",
        type=str,
        default="/home/Junio",
        help="Base para buscar todos os projetos"
    )
    
    args = parser.parse_args()
    
    if args.project:
        validator = MigrationValidator(args.project)
        validator.validate()
    else:
        # Validar todos
        base = Path(args.base)
        projects = sorted([p for p in base.iterdir() if 'sqllm' in p.name.lower()])
        
        print(f"\n{'='*70}")
        print(f"VALIDANDO {len(projects)} PROJETOS")
        print(f"{'='*70}")
        
        results = {}
        for project_path in projects:
            validator = MigrationValidator(project_path)
            success = validator.validate()
            results[project_path.name] = success
        
        # Resumo final
        print(f"\n{'='*70}")
        print(f"RESUMO FINAL")
        print(f"{'='*70}\n")
        
        ok = sum(1 for v in results.values() if v)
        fail = len(results) - ok
        
        for name, success in sorted(results.items()):
            icon = "✅" if success else "⚠️"
            print(f"{icon} {name}")
        
        print(f"\nTotal: {ok} OK, {fail} com avisos")


if __name__ == "__main__":
    main()
