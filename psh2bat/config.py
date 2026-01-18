"""配置管理"""

import os
import logging
from pathlib import Path

LOGGER_NAME = os.getenv("PSH2BAT_LOGGER_NAME", "Psh2Bat")
"""日志器名字"""

LOGGER_LEVEL = int(os.getenv("PSH2BAT_LOGGER_LEVEL", str(logging.INFO)))
"""日志等级"""

LOGGER_COLOR = os.getenv("PSH2BAT_LOGGER_COLOR") not in ["0", "False", "false", "None", "none", "null"]
"""日志颜色"""

ROOT_PATH = Path(__file__).parent
"""Psh2Bat 根目录"""
