"""Config module for application settings."""

# ⚠️ IMPORTAR GOOGLE AUTH PRIMEIRO (antes de qualquer uso de google.cloud)
from . import google_auth

from .settings import (
    MAX_RATE_LIMIT,
    DATASET_ID,
    PROJECT_ID,
    TABLES_CONFIG,
    CLIENT_CONFIG,
    STANDARD_ERROR_MESSAGE,
    is_empresarial_mode,
    load_tables_config,
    load_client_config
)

__all__ = [
    'MAX_RATE_LIMIT',
    'DATASET_ID',
    'PROJECT_ID',
    'TABLES_CONFIG',
    'CLIENT_CONFIG',
    'STANDARD_ERROR_MESSAGE',
    'is_empresarial_mode',
    'load_tables_config',
    'load_client_config',
]
