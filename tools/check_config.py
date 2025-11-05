#!/usr/bin/env python3
"""
VERIFICADOR DE ARQUIVOS DE CONFIGURAÇÃO
Mostra quais arquivos de configuração existem no seu projeto
"""

import sys
from pathlib import Path

def check_project(project_path: str):
    """Verificar e listar arquivos de configuração encontrados"""
    
    project = Path(project_path)
    
    if not project.exists():
        print(f"❌ Projeto não encontrado: {project_path}")
        return
    
    print(f"\n{'='*70}")
    print(f"ARQUIVOS DE CONFIGURAÇÃO EM: {project.name}")
    print(f"{'='*70}\n")
    
    # Arquivos que procurar
    files_to_check = [
        ("Credenciais Google", "gl.json"),
        ("Credenciais App", "credentials.json"),
        ("Tabelas", "tables_config.json"),
        ("Tabelas (config/)", "config/tables_config.json"),
        ("UI Config", "client_config.json"),
        ("UI Config (config/)", "config/client_config.json"),
        ("Payment Config", "payment_config.json"),
        ("Payment Config (config/)", "config/payment_config.json"),
        ("Env", ".env"),
        ("Env Local", ".env.local"),
    ]
    
    found = []
    not_found = []
    
    for label, file_path in files_to_check:
        full_path = project / file_path
        if full_path.exists():
            found.append((label, file_path))
            print(f"✓ {label:30} {file_path}")
        else:
            not_found.append((label, file_path))
    
    if not found:
        print("Nenhum arquivo de configuração encontrado")
    
    print(f"\n{'='*70}")
    print(f"RESUMO: {len(found)} arquivo(s) encontrado(s)")
    print(f"{'='*70}\n")
    
    if found:
        print("Quando você rodar 'git pull', esses arquivos serão preservados:")
        for label, file_path in found:
            print(f"  • {file_path}")
        print()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python check_config.py /caminho/do/projeto")
        print("Exemplo: python check_config.py /home/Junio/ap_sqllm")
        sys.exit(1)
    
    check_project(sys.argv[1])
