#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servicio principal de traduccion.

Coordina todos los componentes del sistema para realizar traducciones
completas o incrementales de archivos XLIFF.
"""

import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    tqdm = None
    TQDM_AVAILABLE = False

from traductor.config.idiomas import ConfigIdioma, obtener_config_idioma
from traductor.core.base_translator import crear_traductor, BaseTranslator
from traductor.core.xliff_parser import XLIFFParser
from traductor.database.db_manager import DatabaseManager
from traductor.services.incremental_detector import IncrementalDetector, ResultadoDeteccion
from traductor.utils.file_naming import FileNaming
from traductor.utils.logger import get_logger


@dataclass
class ResultadoTraduccion:
    """Resultado de una sesion de traduccion."""
    archivo_origen: str
    archivo_destino: str
    idioma_destino: str
    total_etiquetas: int
    traducidas: int
    nuevas: int
    reutilizadas: int
    errores: int
    duracion_segundos: float
    exitoso: bool


class TranslationService:
    """Servicio principal de traduccion XLIFF."""

    def __init__(
        self,
        db_path: str = "traductor.db",
        base_dir_salida: str = "Idiomas",
        tipo_traductor: str = "google",
        pausa_cada_n: int = 50,
        delay_pausa: float = 1.0
    ):
        """
        Inicializa el servicio de traduccion.

        Args:
            db_path: Ruta a la base de datos SQLite
            base_dir_salida: Directorio base para archivos traducidos
            tipo_traductor: Tipo de traductor a usar ('google', etc.)
            pausa_cada_n: Pausar cada N traducciones nuevas
            delay_pausa: Segundos de pausa
        """
        self.db = DatabaseManager(db_path)
        self.file_naming = FileNaming(base_dir_salida)
        self.detector = IncrementalDetector(self.db)
        self.tipo_traductor = tipo_traductor
        self.pausa_cada_n = pausa_cada_n
        self.delay_pausa = delay_pausa
        self.logger = get_logger()

        self._traductor: Optional[BaseTranslator] = None
        self._progreso_callback: Optional[Callable[[int, int], None]] = None

    def traducir(
        self,
        archivo_entrada: str,
        idioma_destino: str,
        archivo_salida: Optional[str] = None,
        forzar_retraduccion: bool = False
    ) -> ResultadoTraduccion:
        """
        Traduce un archivo XLIFF a un idioma destino.

        Args:
            archivo_entrada: Ruta al archivo XLIFF de entrada
            idioma_destino: Nombre del idioma destino (ej: 'catalan', 'euskera')
            archivo_salida: Ruta de salida (opcional, se genera automaticamente)
            forzar_retraduccion: Si True, traduce todo ignorando cache

        Returns:
            ResultadoTraduccion con estadisticas
        """
        inicio = time.time()

        # Obtener configuracion del idioma
        config_idioma = obtener_config_idioma(idioma_destino)
        if config_idioma is None:
            raise ValueError(f"Idioma no soportado: {idioma_destino}")

        self.logger.info(f"Traduciendo a {config_idioma.nombre}...")

        # Determinar archivo de salida
        if archivo_salida is None:
            archivo_salida = self.file_naming.generar_nombre_salida(
                archivo_entrada, config_idioma
            )

        # Asegurar directorio de salida
        self.file_naming.asegurar_directorio(archivo_salida)

        # Cargar y parsear archivo
        self.logger.info(f"Cargando: {archivo_entrada}")
        parser = XLIFFParser()
        doc = parser.cargar(archivo_entrada)
        self.logger.info(f"Total de unidades: {doc.total_unidades}")

        # Analizar que necesita traduccion
        if forzar_retraduccion:
            # Traducir todo
            resultado_deteccion = ResultadoDeteccion(
                total_etiquetas=doc.total_unidades,
                etiquetas_nuevas=list(parser.iterar_unidades()),
                etiquetas_en_cache=[],
                etiquetas_modificadas=[]
            )
        else:
            resultado_deteccion = self.detector.analizar(parser, config_idioma.codigo)
            self.logger.info(self.detector.generar_resumen(resultado_deteccion))

        # Inicializar traductor
        self._traductor = crear_traductor(
            tipo=self.tipo_traductor,
            config_destino=config_idioma
        )

        # Procesar traducciones
        errores = 0
        nuevas_traducciones = []

        # Aplicar traducciones desde cache
        for unit, traduccion in resultado_deteccion.etiquetas_en_cache:
            parser.actualizar_traduccion(unit, traduccion)

        # Traducir etiquetas nuevas
        total_nuevas = resultado_deteccion.total_nuevas
        if total_nuevas > 0:
            self.logger.info(f"Traduciendo {total_nuevas} etiquetas nuevas...")

            if TQDM_AVAILABLE:
                iterador = tqdm(
                    resultado_deteccion.etiquetas_nuevas,
                    desc="Traduciendo",
                    unit=" etiquetas"
                )
            else:
                iterador = resultado_deteccion.etiquetas_nuevas

            for idx, unit in enumerate(iterador, 1):
                try:
                    traduccion = self._traductor.traducir(unit.target)
                    parser.actualizar_traduccion(unit, traduccion)
                    nuevas_traducciones.append((unit.target, traduccion))

                    # Pausa periodica
                    if idx % self.pausa_cada_n == 0:
                        time.sleep(self.delay_pausa)

                except Exception as e:
                    errores += 1
                    self.logger.error(f"Error en unidad {unit.id}: {e}")

                # Progreso sin tqdm
                if not TQDM_AVAILABLE and idx % 100 == 0:
                    self.logger.progress(idx, total_nuevas)

        # Guardar nuevas traducciones en cache
        if nuevas_traducciones:
            self.db.guardar_lote_cache(config_idioma.codigo, nuevas_traducciones)
            self.logger.info(f"Cache actualizado: {len(nuevas_traducciones)} traducciones")

        # Guardar archivo traducido
        self.logger.info(f"Guardando: {archivo_salida}")
        parser.guardar(archivo_salida)

        duracion = time.time() - inicio

        # Registrar sesion en BD
        self.db.registrar_traduccion(
            idioma_origen="en",
            idioma_destino=config_idioma.codigo,
            fichero_original=archivo_entrada,
            fichero_destino=archivo_salida,
            total_etiquetas=resultado_deteccion.total_etiquetas,
            total_traducidas=resultado_deteccion.total_etiquetas - errores,
            total_nuevas=len(nuevas_traducciones),
            total_reutilizadas=resultado_deteccion.total_en_cache,
            duracion_segundos=duracion,
            estado="completado" if errores == 0 else "con_errores"
        )

        resultado = ResultadoTraduccion(
            archivo_origen=archivo_entrada,
            archivo_destino=archivo_salida,
            idioma_destino=config_idioma.nombre,
            total_etiquetas=resultado_deteccion.total_etiquetas,
            traducidas=resultado_deteccion.total_etiquetas - errores,
            nuevas=len(nuevas_traducciones),
            reutilizadas=resultado_deteccion.total_en_cache,
            errores=errores,
            duracion_segundos=duracion,
            exitoso=errores == 0
        )

        self._mostrar_resumen(resultado)
        return resultado

    def traducir_multiples_idiomas(
        self,
        archivo_entrada: str,
        idiomas: List[str],
        forzar_retraduccion: bool = False
    ) -> List[ResultadoTraduccion]:
        """
        Traduce un archivo a multiples idiomas.

        Args:
            archivo_entrada: Ruta al archivo XLIFF
            idiomas: Lista de nombres de idiomas
            forzar_retraduccion: Si True, ignora cache

        Returns:
            Lista de ResultadoTraduccion
        """
        resultados = []

        for idioma in idiomas:
            self.logger.info(f"\n{'='*50}")
            self.logger.info(f"Procesando: {idioma}")
            self.logger.info(f"{'='*50}")

            try:
                resultado = self.traducir(
                    archivo_entrada,
                    idioma,
                    forzar_retraduccion=forzar_retraduccion
                )
                resultados.append(resultado)
            except Exception as e:
                self.logger.error(f"Error al traducir a {idioma}: {e}")

        return resultados

    def _mostrar_resumen(self, resultado: ResultadoTraduccion) -> None:
        """Muestra resumen de la traduccion."""
        self.logger.info("")
        self.logger.info("Traduccion completada!")
        self.logger.info(f"  Archivo: {resultado.archivo_destino}")
        self.logger.info(f"  Idioma: {resultado.idioma_destino}")
        self.logger.info(f"  Total etiquetas: {resultado.total_etiquetas}")
        self.logger.info(f"  Nuevas traducciones: {resultado.nuevas}")
        self.logger.info(f"  Reutilizadas (cache): {resultado.reutilizadas}")
        if resultado.errores > 0:
            self.logger.info(f"  Errores: {resultado.errores}")
        self.logger.info(f"  Duracion: {resultado.duracion_segundos:.1f}s")

    def obtener_estadisticas(self) -> dict:
        """Obtiene estadisticas globales del sistema."""
        return {
            "por_idioma": self.db.obtener_estadisticas_globales(),
            "cache": self.db.obtener_conteo_cache(),
            "historial_reciente": self.db.obtener_historial(5)
        }
