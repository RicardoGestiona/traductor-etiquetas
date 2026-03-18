#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de logging para el traductor XLIFF.
"""

import json
import logging
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional


class JsonFormatter(logging.Formatter):
    """Formatter que emite logs en JSON estructurado para file handlers."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = traceback.format_exception(*record.exc_info)
        return json.dumps(log_entry, ensure_ascii=False)


class Logger:
    """Configuracion centralizada de logging."""

    _instance: Optional['Logger'] = None
    _logger: Optional[logging.Logger] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._logger is not None:
            return

        self._logger = logging.getLogger("traductor")
        self._logger.setLevel(logging.DEBUG)

        # Formato para consola
        console_formatter = logging.Formatter(
            "%(message)s"
        )

        # Formato para archivo
        file_formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Handler de consola
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)
        self._logger.addHandler(console_handler)

        # Handler de archivo (opcional, se activa con setup_file_logging)
        self._file_handler: Optional[logging.FileHandler] = None

    def setup_file_logging(self, log_dir: str = "logs") -> None:
        """
        Configura logging a archivo.

        Args:
            log_dir: Directorio para archivos de log
        """
        log_path = Path(log_dir)
        log_path.mkdir(exist_ok=True)

        fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_path / f"traductor_{fecha}.log"

        self._file_handler = logging.FileHandler(log_file, encoding="utf-8")
        self._file_handler.setLevel(logging.DEBUG)
        self._file_handler.setFormatter(JsonFormatter())
        self._logger.addHandler(self._file_handler)

    def set_level(self, level: int) -> None:
        """Cambia el nivel de logging."""
        self._logger.setLevel(level)
        for handler in self._logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                handler.setLevel(level)

    @property
    def logger(self) -> logging.Logger:
        """Retorna el logger configurado."""
        return self._logger

    def info(self, msg: str) -> None:
        self._logger.info(msg)

    def debug(self, msg: str) -> None:
        self._logger.debug(msg)

    def warning(self, msg: str) -> None:
        self._logger.warning(msg)

    def error(self, msg: str) -> None:
        self._logger.error(msg)

    def progress(self, current: int, total: int, prefix: str = "") -> None:
        """Muestra progreso sin barra (compatible con tqdm)."""
        porcentaje = (current / total) * 100 if total > 0 else 0
        self._logger.info(f"{prefix}Progreso: {current}/{total} ({porcentaje:.1f}%)")


def get_logger() -> Logger:
    """Obtiene la instancia singleton del logger."""
    return Logger()
