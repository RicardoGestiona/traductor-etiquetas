#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Traductor XLIFF - Sistema unificado de traduccion de etiquetas Docebo

Este paquete proporciona:
- Traduccion incremental (solo etiquetas nuevas)
- Base de datos SQLite para control de traducciones
- Nomenclatura estandarizada de archivos (YYYYMMDD-nombre-idioma.xliff)
- Escalabilidad para nuevos idiomas sin duplicar codigo
"""

__version__ = "2.0.0"
__author__ = "ES Publico"

from traductor.services.translation_service import TranslationService
from traductor.database.db_manager import DatabaseManager
from traductor.config.idiomas import IDIOMAS_SOPORTADOS

__all__ = [
    "TranslationService",
    "DatabaseManager",
    "IDIOMAS_SOPORTADOS",
]
