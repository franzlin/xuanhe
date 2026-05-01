"""引擎包初始化"""
from .db import init_db
from .game_engine import char_create, process_action, month_settle, format_status_line
from .ai_narrator import generate_narrative_ai, get_ai_status, load_config, save_config
