#!/usr/bin/env python3
"""
GERENCIADOR DE ATUALIZAÇÃO COM GIT
1. Salva arquivos locais (não sincronizáveis)
2. Faz git pull
3. Restaura arquivos locais
"""

import os
import sys
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime

class GitPullManager:
    """Gerencia git pull preservando arquivos locais"""
    
    # Locais alternativos onde o arquivo pode estar em projetos antigos
    ALTERNATIVE_LOCATIONS = {
        "tables_config.json": ["tables_config.json", "config/tables_config.json"],
        "client_config.json": ["client_config.json", "config/client_config.json"],
        "payment_config.json": ["payment_config.json", "config/payment_config.json"],
        "gl.json": ["gl.json", "config/gl.json"],
        "credentials.json": ["credentials.json", "config/credentials.json"],
    }
    
    # Arquivos de configuração que o usuário coloca e devem ser preservados
    # NUNCA são gerados automaticamente - são configurações do projeto
    LOCAL_ONLY_FILES = {
        # Credenciais - mover para config/
        "gl.json": "config/gl.json",                      # Google Cloud credentials
        "credentials.json": "config/credentials.json",    # App credentials
        
        # Configs específicas de projeto - buscar em ambos os locais
        "tables_config.json": "config/tables_config.json",      # Tabelas do projeto (pode estar na raiz)
        "config/tables_config.json": "config/tables_config.json",    # Tabelas do projeto
        "client_config.json": "config/client_config.json",      # UI customizada (pode estar na raiz)
        "config/client_config.json": "config/client_config.json",    # UI customizada
        "payment_config.json": "config/payment_config.json",    # Payment config (pode estar na raiz)
        "config/payment_config.json": "config/payment_config.json",  # Payment config
        
        # Variáveis de ambiente
        ".env": ".env",                         # Variáveis de ambiente
        ".env.local": ".env.local",             # Env local
    }
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.project_name = self.project_path.name
        self.temp_dir = None
        self.saved_files: Dict[str, str] = {}  # {file: backup_path}
        self.errors: List[str] = []
    
    def run(self, dry_run: bool = False) -> Dict:
        """Executar fluxo completo"""
        
        print(f"\n{'='*70}")
        print(f"GERENCIADOR DE GIT PULL")
        print(f"{'='*70}")
        print(f"Projeto: {self.project_name}")
        print(f"Caminho: {self.project_path}")
        print(f"Modo: {'DRY RUN (simulação)' if dry_run else 'EXECUÇÃO REAL'}\n")
        
        try:
            # 1. Validar projeto
            if not self._validate_project():
                return {"status": "error", "message": "Projeto inválido"}
            
            # 2. Detectar arquivos locais
            print("1️⃣ Detectando arquivos locais...")
            local_files = self._find_local_files()
            
            if not local_files:
                print("   ℹ️  Nenhum arquivo local encontrado\n")
            else:
                print(f"   Encontrados: {len(local_files)} arquivo(s)")
                for src, dst in local_files:
                    if src == dst:
                        print(f"      • {src}")
                    else:
                        print(f"      • {src} → {dst}")
                print()
            
            # 3. Salvar arquivos locais
            if local_files:
                print("2️⃣ Salvando arquivos locais...")
                if not dry_run:
                    self._backup_files(local_files)
                    print(f"   ✓ {len(self.saved_files)} arquivo(s) salvos\n")
                else:
                    print(f"   [DRY] Salvaria {len(local_files)} arquivo(s)\n")
            else:
                print("2️⃣ (Pulando - nenhum arquivo para salvar)\n")
            
            # 4. Git reset (descartar mudanças locais)
            print("3️⃣ Descartando mudanças locais...")
            if not dry_run:
                result = self._git_reset()
                if not result["success"]:
                    self.errors.append(f"Git reset falhou: {result['error']}")
                    print(f"   ✗ Erro: {result['error']}\n")
                    return {"status": "error", "message": result['error'], "errors": self.errors}
                else:
                    print(f"   ✓ Mudanças locais descartadas\n")
            else:
                print("   [DRY] Descartaria mudanças locais\n")
            
            # 5. Git pull
            print("4️⃣ Executando git pull...")
            if not dry_run:
                result = self._git_pull()
                if not result["success"]:
                    self.errors.append(f"Git pull falhou: {result['error']}")
                    print(f"   ✗ Erro: {result['error']}\n")
                    return {"status": "error", "message": result['error'], "errors": self.errors}
                else:
                    print(f"   ✓ Git pull concluído\n")
            else:
                print("   [DRY] Executaria git pull\n")
            
            # 5. Restaurar arquivos locais
            if self.saved_files and not dry_run:
                print("5️⃣ Restaurando arquivos locais...")
                self._restore_files()
                print(f"   ✓ {len(self.saved_files)} arquivo(s) restaurados\n")
            elif dry_run and local_files:
                print("5️⃣ [DRY] Restauraria arquivos locais\n")
            else:
                print("5️⃣ (Pulando - nada para restaurar)\n")
            
            print(f"{'='*70}")
            print(f"✅ CONCLUÍDO COM SUCESSO!")
            print(f"{'='*70}\n")
            
            return {
                "status": "success",
                "project": self.project_name,
                "local_files": len(local_files),
                "saved_files": len(self.saved_files),
                "errors": self.errors,
                "dry_run": dry_run,
            }
        
        except Exception as e:
            self.errors.append(str(e))
            print(f"\n❌ ERRO: {e}\n")
            return {
                "status": "error",
                "message": str(e),
                "errors": self.errors,
            }
        
        finally:
            # Limpar temp dir
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
    
    def _validate_project(self) -> bool:
        """Validar se é um projeto git válido"""
        if not self.project_path.exists():
            self.errors.append(f"Pasta não existe: {self.project_path}")
            return False
        
        git_dir = self.project_path / ".git"
        if not git_dir.exists():
            self.errors.append(f"Não é um repositório git: {self.project_path}")
            return False
        
        return True
    
    def _find_local_files(self) -> List[Tuple[str, str]]:
        """Encontrar arquivos locais que não devem ser sincronizados
        
        Retorna lista de (arquivo_atual, arquivo_destino_correto)
        Detecta se arquivo está em local errado e move para o correto
        Evita duplicatas - cada arquivo destino aparece apenas uma vez
        """
        found_dict = {}  # {dst_path: src_path} para evitar duplicatas
        
        for src_pattern, dst_path in self.LOCAL_ONLY_FILES.items():
            # Se já encontramos um arquivo para este destino, pula
            if dst_path in found_dict:
                continue
            
            # Se tem mapeamento de locais alternativos
            if src_pattern in self.ALTERNATIVE_LOCATIONS:
                alt_locs = self.ALTERNATIVE_LOCATIONS[src_pattern]
                
                for alt_loc in alt_locs:
                    file_path = self.project_path / alt_loc
                    if file_path.exists() and file_path.is_file():
                        # Arquivo encontrado neste local
                        found_dict[dst_path] = alt_loc
                        break
                
                # Se encontrou em algum local alternativo, segue para próximo
                if dst_path in found_dict:
                    continue
            
            # Suporta wildcards
            if "*" in src_pattern:
                for file_path in self.project_path.glob(src_pattern):
                    if file_path.is_file():
                        rel_src = str(file_path.relative_to(self.project_path))
                        rel_dst = dst_path.replace("*", file_path.stem)
                        found_dict[rel_dst] = rel_src
            else:
                file_path = self.project_path / src_pattern
                if file_path.exists() and file_path.is_file():
                    found_dict[dst_path] = src_pattern
        
        # Converter de volta para lista de tuplas
        return sorted([(src, dst) for dst, src in found_dict.items()])
    
    def _backup_files(self, files: List[Tuple[str, str]]):
        """Fazer backup dos arquivos locais com novo destino
        
        Args:
            files: Lista de (arquivo_atual, arquivo_destino)
        """
        # Criar temp dir para backups
        self.temp_dir = tempfile.mkdtemp()
        
        for src_rel, dst_rel in files:
            src = self.project_path / src_rel
            
            if not src.exists():
                continue
            
            # Salvar no temp com estrutura de DESTINO
            dst_backup = Path(self.temp_dir) / dst_rel
            dst_backup.parent.mkdir(parents=True, exist_ok=True)
            
            # Copiar arquivo
            shutil.copy2(src, dst_backup)
            self.saved_files[dst_rel] = str(dst_backup)
    
    def _git_reset(self) -> Dict:
        """Executar git reset --hard e git clean para descartar mudanças locais"""
        try:
            # 1. Reset hard
            result = subprocess.run(
                ["git", "reset", "--hard", "HEAD"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                return {"success": False, "error": result.stderr}
            
            # 2. Clean arquivos não rastreados (exceto os que vamos preservar)
            result = subprocess.run(
                ["git", "clean", "-fd"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                return {"success": True, "output": result.stdout}
            else:
                return {"success": False, "error": result.stderr}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _git_pull(self) -> Dict:
        """Executar git pull"""
        try:
            result = subprocess.run(
                ["git", "pull"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                return {"success": True, "output": result.stdout}
            else:
                return {"success": False, "error": result.stderr}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _restore_files(self):
        """Restaurar arquivos locais após git pull (nos locais corretos)"""
        for dst_rel_path, backup_path in self.saved_files.items():
            dst = self.project_path / dst_rel_path
            
            # Criar pasta se não existir
            dst.parent.mkdir(parents=True, exist_ok=True)
            
            # Restaurar arquivo no local CORRETO
            shutil.copy2(backup_path, dst)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Fazer git pull preservando arquivos locais"
    )
    parser.add_argument(
        "project",
        nargs="?",
        help="Caminho do projeto (default: /home/Junio/gl_sqllm)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simular sem fazer alterações"
    )
    parser.add_argument(
        "--list-files",
        action="store_true",
        help="Listar arquivos que serão preservados"
    )
    
    args = parser.parse_args()
    
    # Projeto padrão
    project = args.project or "/home/Junio/gl_sqllm"
    
    # Listar arquivos?
    if args.list_files:
        print("\n📋 ARQUIVOS QUE PODEM SER PRESERVADOS:\n")
        print("Esses arquivos serão preservados SE encontrados no seu projeto:\n")
        for src, dst in sorted(GitPullManager.LOCAL_ONLY_FILES.items()):
            if src == dst:
                print(f"  • {src}")
            else:
                print(f"  • {src:30} → {dst}")
        print("\n💡 Para VER quais arquivos REALMENTE existem no seu projeto:")
        print("   python git_pull_safe.py /seu/projeto --dry-run\n")
        return
    
    # Executar
    manager = GitPullManager(project)
    result = manager.run(dry_run=args.dry_run)
    
    sys.exit(0 if result["status"] == "success" else 1)


if __name__ == "__main__":
    main()
