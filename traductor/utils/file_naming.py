#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de nomenclatura estandarizada para archivos de traduccion.

Formato: YYYYMMDD-nombre-idioma.xliff
Ejemplo: 20260123-xliff-english-ca.xliff
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from traductor.config.idiomas import ConfigIdioma


class FileNaming:
    """Gestiona la nomenclatura de archivos de traduccion."""

    def __init__(self, base_dir: str = "Idiomas"):
        """
        Inicializa el gestor de nomenclatura.

        Args:
            base_dir: Directorio base para archivos traducidos
        """
        self.base_dir = Path(base_dir)

    def generar_nombre_salida(
        self,
        archivo_origen: str,
        config_idioma: ConfigIdioma,
        fecha: Optional[datetime] = None
    ) -> str:
        """
        Genera el nombre de archivo de salida con formato estandarizado.

        Args:
            archivo_origen: Ruta del archivo original
            config_idioma: Configuracion del idioma destino
            fecha: Fecha para el nombre (default: hoy)

        Returns:
            Ruta completa del archivo de salida
        """
        if fecha is None:
            fecha = datetime.now()

        # Extraer nombre base sin extension
        nombre_base = Path(archivo_origen).stem

        # Formato: YYYYMMDD-nombre-idioma.xliff
        fecha_str = fecha.strftime("%Y%m%d")
        nombre_archivo = f"{fecha_str}-{nombre_base}-{config_idioma.codigo_archivo}.xliff"

        # Ruta completa: Idiomas/carpeta_idioma/archivo.xliff
        ruta_completa = self.base_dir / config_idioma.carpeta / nombre_archivo

        return str(ruta_completa)

    def asegurar_directorio(self, ruta_archivo: str) -> None:
        """
        Crea el directorio para el archivo si no existe.

        Args:
            ruta_archivo: Ruta completa del archivo
        """
        directorio = Path(ruta_archivo).parent
        directorio.mkdir(parents=True, exist_ok=True)

    def obtener_ultimo_archivo(
        self,
        config_idioma: ConfigIdioma,
        nombre_base: Optional[str] = None
    ) -> Optional[str]:
        """
        Obtiene el archivo mas reciente para un idioma.

        Args:
            config_idioma: Configuracion del idioma
            nombre_base: Filtrar por nombre base (opcional)

        Returns:
            Ruta del archivo mas reciente o None
        """
        carpeta = self.base_dir / config_idioma.carpeta

        if not carpeta.exists():
            return None

        patron = f"*-{config_idioma.codigo_archivo}.xliff"
        if nombre_base:
            patron = f"*-{nombre_base}-{config_idioma.codigo_archivo}.xliff"

        archivos = list(carpeta.glob(patron))

        if not archivos:
            return None

        # Ordenar por fecha en nombre (formato YYYYMMDD al inicio)
        archivos_ordenados = sorted(archivos, reverse=True)

        return str(archivos_ordenados[0])

    def listar_traducciones(self, config_idioma: ConfigIdioma) -> list:
        """
        Lista todas las traducciones existentes para un idioma.

        Args:
            config_idioma: Configuracion del idioma

        Returns:
            Lista de rutas de archivos
        """
        carpeta = self.base_dir / config_idioma.carpeta

        if not carpeta.exists():
            return []

        patron = f"*-{config_idioma.codigo_archivo}.xliff"
        return [str(f) for f in carpeta.glob(patron)]
