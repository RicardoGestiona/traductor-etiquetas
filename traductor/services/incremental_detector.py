#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Detector de traducciones incrementales.

Compara archivos XLIFF para identificar etiquetas nuevas o modificadas.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple

from traductor.core.xliff_parser import XLIFFParser, TransUnit
from traductor.database.db_manager import DatabaseManager
from traductor.utils.logger import get_logger


@dataclass
class ResultadoDeteccion:
    """Resultado del analisis incremental."""
    total_etiquetas: int
    etiquetas_nuevas: List[TransUnit]
    etiquetas_en_cache: List[Tuple[TransUnit, str]]  # (unit, traduccion_cache)
    etiquetas_modificadas: List[TransUnit]

    @property
    def total_nuevas(self) -> int:
        return len(self.etiquetas_nuevas)

    @property
    def total_en_cache(self) -> int:
        return len(self.etiquetas_en_cache)

    @property
    def total_modificadas(self) -> int:
        return len(self.etiquetas_modificadas)

    @property
    def requiere_traduccion(self) -> int:
        """Total de etiquetas que requieren traduccion."""
        return self.total_nuevas + self.total_modificadas


class IncrementalDetector:
    """Detecta etiquetas que necesitan traduccion."""

    def __init__(self, db_manager: DatabaseManager):
        """
        Inicializa el detector.

        Args:
            db_manager: Gestor de base de datos
        """
        self.db = db_manager
        self.logger = get_logger()

    def analizar(
        self,
        parser: XLIFFParser,
        idioma_destino: str
    ) -> ResultadoDeteccion:
        """
        Analiza un documento XLIFF para detectar que traducir.

        Args:
            parser: Parser con documento cargado
            idioma_destino: Codigo del idioma destino

        Returns:
            ResultadoDeteccion con el analisis
        """
        if parser.documento is None:
            raise ValueError("El parser no tiene documento cargado")

        cache = self.db.obtener_todo_cache(idioma_destino)
        etiquetas_nuevas, etiquetas_en_cache = self._clasificar_etiquetas(parser, cache)

        return ResultadoDeteccion(
            total_etiquetas=parser.total_unidades,
            etiquetas_nuevas=etiquetas_nuevas,
            etiquetas_en_cache=etiquetas_en_cache,
            etiquetas_modificadas=[]
        )

    def _clasificar_etiquetas(
        self,
        parser: XLIFFParser,
        cache: dict
    ) -> Tuple[List[TransUnit], List[Tuple[TransUnit, str]]]:
        """Clasifica etiquetas en nuevas o en cache."""
        etiquetas_nuevas = []
        etiquetas_en_cache = []

        for unit in parser.iterar_unidades():
            # Ignorar etiquetas con texto vacío o solo espacios
            if not unit.target or not unit.target.strip():
                continue

            hash_texto = self.db.calcular_hash(unit.target)

            if hash_texto in cache:
                traduccion_cacheada = cache[hash_texto]
                etiquetas_en_cache.append((unit, traduccion_cacheada))
            else:
                etiquetas_nuevas.append(unit)

        return etiquetas_nuevas, etiquetas_en_cache

    def generar_resumen(self, resultado: ResultadoDeteccion) -> str:
        """
        Genera un resumen legible del analisis.

        Args:
            resultado: Resultado del analisis

        Returns:
            Texto con resumen
        """
        lineas = [
            f"Total de etiquetas: {resultado.total_etiquetas}",
            f"  - En cache (reutilizables): {resultado.total_en_cache}",
            f"  - Nuevas (requieren traduccion): {resultado.total_nuevas}",
            f"  - Modificadas: {resultado.total_modificadas}",
            "",
            f"Etiquetas a traducir: {resultado.requiere_traduccion}",
        ]

        if resultado.total_en_cache > 0:
            ahorro = (resultado.total_en_cache / resultado.total_etiquetas) * 100
            lineas.append(f"Ahorro por cache: {ahorro:.1f}%")

        return "\n".join(lineas)
