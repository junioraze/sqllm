"""
Generators Package - Geração automática de configurações

Módulos:
- table_config_generator: Orquestrador principal
- schema_extractor: Extração de DDL do BigQuery
- config_builder: Construção de table_config.json
"""

from .table_config_generator import TableConfigGenerator

__all__ = ["TableConfigGenerator"]
