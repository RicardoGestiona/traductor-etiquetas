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

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class ConfigIdioma:
    """Configuracion de un idioma soportado."""
    codigo: str           # Codigo para deep_translator (ej: 'ca', 'eu', 'gl')
    codigo_archivo: str   # Sufijo para archivos (ej: 'uk', 'eu', 'gl')
    nombre: str           # Nombre descriptivo
    carpeta: str          # Carpeta en Idiomas/
    separador_archivo: str = "-"  # Separador antes del codigo en nombre de archivo
    nombre_base_override: Optional[str] = None  # Si se define, reemplaza el nombre base del archivo origen
    cabecera_custom: Optional[str] = None  # Cabecera XLIFF fija (usa {date} como placeholder)


# Diccionario de idiomas soportados
IDIOMAS_SOPORTADOS: Dict[str, ConfigIdioma] = {
    "catalan": ConfigIdioma(
        codigo="ca",
        codigo_archivo="uk",
        nombre="Catalan",
        carpeta="catalan",
        separador_archivo="_",
        cabecera_custom=(
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<!DOCTYPE xliff PUBLIC "-//XLIFF//DTD XLIFF//EN" '
            '"http://www.oasis-open.org/committees/xliff/documents/xliff.dtd">\n'
            '<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
            'xsi:schemaLocation="urn:oasis:names:tc:xliff:document:1.2 '
            'xliff-core-1.2-strict.xsd">\n'
            '<file datatype="html" source-language="en" target-language="ca" '
            'date="{date}" original="xliff-english.xliff">\n'
            '<body>'
        )
    ),
    "euskera": ConfigIdioma(
        codigo="eu",
        codigo_archivo="spanish_latam",
        nombre="Euskera",
        carpeta="euskera",
        separador_archivo="-",
        nombre_base_override="xliff",
        cabecera_custom=(
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<!DOCTYPE xliff PUBLIC "-//XLIFF//DTD XLIFF//EN" '
            '"http://www.oasis-open.org/committees/xliff/documents/xliff.dtd">\n'
            '<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
            'xsi:schemaLocation="urn:oasis:names:tc:xliff:document:1.2 '
            'xliff-core-1.2-strict.xsd">\n'
            '<file datatype="html" source-language="en" target-language="eu" '
            'date="{date}" original="xliff-english.xliff">\n'
            '<body>'
        )
    ),
    "gallego": ConfigIdioma(
        codigo="gl",
        codigo_archivo="portuguese-br",
        nombre="Gallego",
        carpeta="gallego",
        nombre_base_override="xliff",
        cabecera_custom=(
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<!DOCTYPE xliff PUBLIC "-//XLIFF//DTD XLIFF//EN" '
            '"http://www.oasis-open.org/committees/xliff/documents/xliff.dtd">\n'
            '<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
            'xsi:schemaLocation="urn:oasis:names:tc:xliff:document:1.2 '
            'xliff-core-1.2-strict.xsd">\n'
            '<file datatype="html" source-language="en" target-language="gl" '
            'date="{date}" original="xliff-english.xliff">\n'
            '<body>'
        )
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


def obtener_config_por_codigo(codigo: str) -> Optional[ConfigIdioma]:
    """
    Obtiene configuracion de un idioma por su codigo ISO.

    Args:
        codigo: Codigo del idioma (ej: 'ca', 'eu', 'gl')

    Returns:
        ConfigIdioma si existe, None si no
    """
    # Primero buscar por nombre (compatibilidad con obtener_config_idioma)
    config = obtener_config_idioma(codigo)
    if config:
        return config

    for cfg in IDIOMAS_SOPORTADOS.values():
        if cfg.codigo == codigo:
            return cfg
    return None


def obtener_nombre_por_codigo(codigo: str) -> str:
    """
    Obtiene el nombre de un idioma desde su codigo ISO.

    Args:
        codigo: Codigo del idioma (ej: 'ca', 'eu', 'gl')

    Returns:
        Nombre del idioma o el codigo si no se encuentra
    """
    for cfg in IDIOMAS_SOPORTADOS.values():
        if cfg.codigo == codigo:
            return cfg.nombre
    return codigo
