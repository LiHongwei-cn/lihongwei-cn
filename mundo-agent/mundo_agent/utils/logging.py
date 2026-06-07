"""蒙多日志系统 — 统一日志记录"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional


# 日志目录
LOG_DIR = Path.home() / ".hermes" / "mundo-agent" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


# 日志格式
CONSOLE_FORMAT = "%(message)s"
FILE_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class ColoredFormatter(logging.Formatter):
    """带颜色的控制台日志格式化器"""

    COLORS = {
        logging.DEBUG: "\033[2m",      # 暗色
        logging.INFO: "\033[0m",       # 默认
        logging.WARNING: "\033[33m",   # 黄色
        logging.ERROR: "\033[31m",     # 红色
        logging.CRITICAL: "\033[35m",  # 紫色
    }
    RESET = "\033[0m"

    def format(self, record):
        color = self.COLORS.get(record.levelno, self.RESET)
        message = super().format(record)
        return f"{color}{message}{self.RESET}"


class MundoLogger:
    """蒙多日志管理器"""

    _loggers = {}
    _initialized = False

    @classmethod
    def initialize(cls, level: str = "INFO", file_logging: bool = True):
        """初始化日志系统"""
        if cls._initialized:
            return

        # 根日志器
        root_logger = logging.getLogger("mundo")
        root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = ColoredFormatter(CONSOLE_FORMAT)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

        # 文件处理器
        if file_logging:
            log_file = LOG_DIR / f"mundo_{datetime.now().strftime('%Y%m%d')}.log"
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(FILE_FORMAT, DATE_FORMAT)
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)

        cls._initialized = True

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """获取日志器"""
        if not cls._initialized:
            cls.initialize()
        if name not in cls._loggers:
            cls._loggers[name] = logging.getLogger(f"mundo.{name}")
        return cls._loggers[name]


def get_logger(name: str) -> logging.Logger:
    """便捷函数：获取日志器"""
    return MundoLogger.get_logger(name)


# 常用日志器
def get_core_logger():
    return get_logger("core")


def get_tool_logger():
    return get_logger("tools")


def get_memory_logger():
    return get_logger("memory")


def get_llm_logger():
    return get_logger("llm")


def get_agent_logger():
    return get_logger("agents")


def get_cli_logger():
    return get_logger("cli")