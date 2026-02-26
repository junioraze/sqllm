"""
RAG Manager - Gerenciador centralizado de instâncias RAG
Garante inicialização correta e recarregamento em desenvolvimento
"""

import os
import json
import time
from typing import Optional, Dict, Any
from functools import lru_cache
from datetime import datetime

_rag_instance: Optional['RAGManager'] = None
_config_last_modified: Optional[float] = None


class RAGManager:
    """Gerenciador singleton para RAG System"""
    
    def __init__(self):
        self.config_path = self._find_config()
        self.config_mtime = self._get_config_mtime()
        self.rag_v3 = None
        self.initialized_at = None
        self.initialization_errors = []
        
        # Inicializar
        self._initialize()
    
    def _find_config(self) -> str:
        """Procura tables_config.json em múltiplas localizações"""
        possible_paths = [
            os.path.join(os.path.dirname(__file__), "..", "config", "tables_config.json"),
            os.path.join(os.path.dirname(__file__), "..", "tables_config.json"),
            "tables_config.json",
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                print(f"[RAG Manager] Config encontrado: {path}")
                return path
        
        raise FileNotFoundError("tables_config.json não encontrado em nenhuma localização")
    
    def _get_config_mtime(self) -> float:
        """Obter tempo de modificação do config"""
        try:
            return os.path.getmtime(self.config_path)
        except:
            return 0
    
    def _initialize(self):
        """Inicializar RAG v3"""
        try:
            print(f"\n{'='*70}")
            print("[RAG Manager] 🚀 Inicializando RAG System...")
            print(f"{'='*70}")
            
            from rag_system.business_metadata_rag_v3 import BusinessMetadataRAGv3
            
            # Carregar RAG v3
            self.rag_v3 = BusinessMetadataRAGv3(config_path=self.config_path)
            
            # Validar que foi inicializado
            if not hasattr(self.rag_v3, 'table_metadata') or not self.rag_v3.table_metadata:
                raise RuntimeError("RAG v3 não carregou metadados das tabelas")
            
            if hasattr(self.rag_v3, 'embedder') and self.rag_v3.embedder:
                if not hasattr(self.rag_v3, 'embeddings') or not self.rag_v3.embeddings:
                    raise RuntimeError("RAG v3 não pré-computou embeddings")
            
            self.initialized_at = datetime.now()
            self.initialization_errors = []
            
            print(f"[RAG Manager] ✅ RAG System inicializado com sucesso!")
            print(f"[RAG Manager] ✅ Tabelas carregadas: {len(self.rag_v3.table_metadata)}")
            print(f"[RAG Manager] ✅ Embeddings pré-computados: {len(self.rag_v3.embeddings) if hasattr(self.rag_v3, 'embeddings') else 'N/A'}")
            print(f"{'='*70}\n")
            
        except Exception as e:
            error_msg = str(e)
            self.initialization_errors.append(error_msg)
            print(f"[RAG Manager] ❌ ERRO na inicialização: {error_msg}")
            raise
    
    def check_reload_needed(self) -> bool:
        """Verificar se config foi modificado (para desenvolvimento)"""
        current_mtime = self._get_config_mtime()
        if current_mtime > self.config_mtime:
            print(f"[RAG Manager] 🔄 Config modificado detectado, recarregando...")
            self.config_mtime = current_mtime
            self._initialize()
            return True
        return False
    
    def get_rag(self):
        """Obter instância do RAG v3"""
        if self.rag_v3 is None:
            raise RuntimeError("RAG não foi inicializado corretamente")
        
        # Verificar se precisa recarregar (apenas em desenvolvimento)
        if os.getenv("ENVIRONMENT", "prod") == "dev":
            self.check_reload_needed()
        
        return self.rag_v3
    
    def get_status(self) -> Dict[str, Any]:
        """Retornar status da inicialização"""
        return {
            "initialized": self.rag_v3 is not None,
            "initialized_at": self.initialized_at.isoformat() if self.initialized_at else None,
            "tables_count": len(self.rag_v3.table_metadata) if self.rag_v3 else 0,
            "embeddings_count": len(self.rag_v3.embeddings) if self.rag_v3 and hasattr(self.rag_v3, 'embeddings') else 0,
            "errors": self.initialization_errors,
            "config_path": self.config_path
        }


def get_rag_manager() -> RAGManager:
    """Obter ou criar o gerenciador singleton de RAG"""
    global _rag_instance
    
    if _rag_instance is None:
        _rag_instance = RAGManager()
    
    return _rag_instance


def get_rag():
    """Forma simples de obter instância do RAG"""
    return get_rag_manager().get_rag()


def get_rag_status() -> Dict[str, Any]:
    """Obter status do RAG Manager"""
    try:
        return get_rag_manager().get_status()
    except Exception as e:
        return {
            "initialized": False,
            "error": str(e)
        }


# Inicializar na primeira importação (desenvolvimento)
if os.getenv("ENVIRONMENT", "prod") == "dev":
    try:
        get_rag_manager()
        print("[RAG Manager] ✅ Pré-carregado em modo desenvolvimento")
    except Exception as e:
        print(f"[RAG Manager] ⚠️  Erro ao pré-carregar: {e}")
