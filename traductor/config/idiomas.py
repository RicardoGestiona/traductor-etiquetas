#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuracion de idiomas soportados para el sistema de traduccion.

Cada idioma tiene:
- codigo: Codigo ISO 639-1 para la API de traduccion
- codigo_archivo: Sufijo para nombres de archivo
- nombre: Nombre del idioma en espanol
- carpeta: Nombre de carpeta en Idiomas/
"""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class ConfigIdioma:
    """Configuracion de un idioma soportado."""
    codigo: str           # Codigo para deep_translator (ej: 'ca', 'eu', 'gl')
    codigo_archivo: str   # Sufijo para archivos (ej: 'ca', 'eu', 'gl')
    nombre: str           # Nombre descriptivo
    carpeta: str          # Carpeta en Idiomas/


# Diccionario de idiomas soportados
IDIOMAS_SOPORTADOS: Dict[str, ConfigIdioma] = {
    "catalan": ConfigIdioma(
        codigo="ca",
        codigo_archivo="ca",
        nombre="Catalan",
        carpeta="catalan"
    ),
    "euskera": ConfigIdioma(
        codigo="eu",
        codigo_archivo="eu",
        nombre="Euskera",
        carpeta="euskera"
    ),
    "gallego": ConfigIdioma(
        codigo="gl",
        codigo_archivo="gl",
        nombre="Gallego",
        carpeta="gallego"
    ),
    "valenciano": ConfigIdioma(
        codigo="ca",  # Mismo codigo que catalan en Google Translate
        codigo_archivo="va",
        nombre="Valenciano",
        carpeta="valenciano"
    ),
    "espanol": ConfigIdioma(
        codigo="es",
        codigo_archivo="es",
        nombre="Espanol",
        carpeta="espanol"
    ),
    "frances": ConfigIdioma(
        codigo="fr",
        codigo_archivo="fr",
        nombre="Frances",
        carpeta="frances"
    ),
    "portugues": ConfigIdioma(
        codigo="pt",
        codigo_archivo="pt",
        nombre="Portugues",
        carpeta="portugues"
    ),
    "italiano": ConfigIdioma(
        codigo="it",
        codigo_archivo="it",
        nombre="Italiano",
        carpeta="italiano"
    ),
    "aleman": ConfigIdioma(
        codigo="de",
        codigo_archivo="de",
        nombre="Aleman",
        carpeta="aleman"
    ),
}

# Idioma de origen por defecto
IDIOMA_ORIGEN_DEFAULT = "en"


def obtener_config_idioma(nombre_idioma: str) -> Optional[ConfigIdioma]:
    """
    Obtiene la configuracion de un idioma por nombre.

    Args:
        nombre_idioma: Nombre del idioma (ej: 'catalan', 'euskera')

    Returns:
        ConfigIdioma si existe, None si no
    """
    nombre_normalizado = nombre_idioma.lower().strip()
    return IDIOMAS_SOPORTADOS.get(nombre_normalizado)


def listar_idiomas() -> list:
    """Retorna lista de nombres de idiomas soportados."""
    return list(IDIOMAS_SOPORTADOS.keys())
