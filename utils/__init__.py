"""Utils module for utilities and helpers."""

from .helpers import (
    display_message_with_spoiler,
    slugfy_response,
    safe_serialize_gemini_params,
    safe_serialize_data,
    safe_serialize_tech_details,
    format_text_with_ia_highlighting
)
from .cache import save_interaction, log_error, get_user_history, get_interaction_full_data
from .logger import log_interaction
from .rate_limit import RateLimiter
from .auth_system import render_auth_system, get_current_user
from .image_utils import get_background_style, get_login_background_style

__all__ = [
    'display_message_with_spoiler',
    'slugfy_response',
    'safe_serialize_gemini_params',
    'safe_serialize_data',
    'safe_serialize_tech_details',
    'format_text_with_ia_highlighting',
    'save_interaction',
    'log_error',
    'get_user_history',
    'get_interaction_full_data',
    'log_interaction',
    'RateLimiter',
    'render_auth_system',
    'get_current_user',
    'get_background_style',
    'get_login_background_style',
]
