"""
GL_SQLLM - SQL LLM Query Generation System

Retrieval-Augmented Generation (RAG) + Google Gemini para geração de SQL
"""

import os
import sys

# Adicionar raiz do projeto ao Python path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

__version__ = "3.0.0"
__author__ = "Junio"
__license__ = "MIT"

# Exports principais
try:
    from config import *
    from database import *
    from llm_handlers import *
    from rag_system import *
    from utils import *
except ImportError as e:
    print(f"⚠️ Aviso ao importar módulos: {e}")

__all__ = [
    'config',
    'database',
    'llm_handlers',
    'rag_system',
    'utils',
]
