"""
🔐 Google Authentication Helper

Configura GOOGLE_APPLICATION_CREDENTIALS para apontar para gl.json
Suporta multi-path lookup para gl.json:
  1. config/gl.json (recomendado)
  2. raiz/gl.json (fallback)

Deve ser importado ANTES de qualquer uso de google.cloud
"""

import os
import json
from pathlib import Path


def _find_gl_json():
    """Procura gl.json em várias localizações"""
    possible_paths = [
        # Primeiro: relativo à pasta config
        os.path.join(os.path.dirname(__file__), "gl.json"),
        # Segundo: na raiz do projeto (fallback para compatibilidade)
        os.path.join(os.path.dirname(__file__), "..", "gl.json"),
        # Terceiro: diretório atual
        "gl.json",
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            abs_path = os.path.abspath(path)
            print(f"[Google Auth] ✅ gl.json encontrado em: {abs_path}")
            return abs_path
    
    # Nenhum encontrado
    print(f"[Google Auth] ⚠️ gl.json NÃO encontrado nas localizações:")
    for path in possible_paths:
        print(f"              - {os.path.abspath(path)}")
    
    return None


def configure_google_auth():
    """
    Configura autenticação Google para BigQuery.
    
    Esta função:
    1. Procura gl.json em múltiplas localizações
    2. Define GOOGLE_APPLICATION_CREDENTIALS com o caminho correto
    3. Permite que google.cloud.bigquery.Client() funcione sem erros
    
    Levanta:
        FileNotFoundError: Se gl.json não for encontrado
    """
    gl_json_path = _find_gl_json()
    
    if not gl_json_path:
        raise FileNotFoundError(
            "❌ Arquivo gl.json não encontrado!\n"
            "   Procurado em:\n"
            f"   - {os.path.abspath('config/gl.json')}\n"
            f"   - {os.path.abspath('gl.json')}\n"
            "\n   Solução: Copie suas credenciais do Google para config/gl.json"
        )
    
    # Validar se é um arquivo JSON válido
    try:
        with open(gl_json_path, 'r', encoding='utf-8') as f:
            json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"❌ Arquivo gl.json inválido (JSON malformado):\n"
            f"   Caminho: {gl_json_path}\n"
            f"   Erro: {e}"
        )
    except Exception as e:
        raise ValueError(
            f"❌ Erro ao ler gl.json:\n"
            f"   Caminho: {gl_json_path}\n"
            f"   Erro: {e}"
        )
    
    # Definir variável de ambiente
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = gl_json_path
    
    print(f"[Google Auth] ✅ GOOGLE_APPLICATION_CREDENTIALS configurado:")
    print(f"              {os.environ['GOOGLE_APPLICATION_CREDENTIALS']}")
    
    return gl_json_path


# Configurar automaticamente ao importar este módulo
try:
    _gl_json_configured_path = configure_google_auth()
except FileNotFoundError as e:
    print(f"[Google Auth] ⚠️ AVISO: {e}")
    _gl_json_configured_path = None
except ValueError as e:
    print(f"[Google Auth] ❌ ERRO: {e}")
    _gl_json_configured_path = None
except Exception as e:
    print(f"[Google Auth] ❌ ERRO INESPERADO: {e}")
    _gl_json_configured_path = None


def get_gl_json_path():
    """Retorna o caminho do gl.json configurado (ou None se não encontrado)"""
    return _gl_json_configured_path


def is_configured():
    """Verifica se autenticação foi configurada com sucesso"""
    return _gl_json_configured_path is not None
