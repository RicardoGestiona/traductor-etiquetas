#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Procesador por lotes para traducciones automáticas.

Monitorea la carpeta traduccion-pendiente/ y traduce automáticamente
a catalán, gallego y euskera.
"""

import os
import time
import shutil
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass

from traductor.services.translation_service import TranslationService
from traductor.utils.logger import get_logger


@dataclass
class ResultadoProcesamiento:
    """Resultado del procesamiento de un archivo."""
    archivo_origen: str
    idiomas_procesados: List[str]
    exitoso: bool
    errores: List[str]


class BatchProcessor:
    """Procesador por lotes de archivos XLIFF."""

    IDIOMAS_DESTINO = ["catalan", "gallego", "euskera"]

    def __init__(
        self,
        carpeta_entrada: str = "traduccion-pendiente",
        carpeta_salida: str = "traducidos",
        db_path: str = "traductor.db",
        mover_procesados: bool = True
    ):
        """
        Inicializa el procesador por lotes.

        Args:
            carpeta_entrada: Carpeta donde se depositan archivos a traducir
            carpeta_salida: Carpeta base para archivos traducidos
            db_path: Ruta a la base de datos SQLite
            mover_procesados: Si True, mueve archivos procesados a carpeta de respaldo
        """
        self.carpeta_entrada = Path(carpeta_entrada)
        self.carpeta_salida = Path(carpeta_salida)
        self.db_path = db_path
        self.mover_procesados = mover_procesados
        self.logger = get_logger()

        # Crear carpetas si no existen
        self.carpeta_entrada.mkdir(parents=True, exist_ok=True)
        for idioma in self.IDIOMAS_DESTINO:
            (self.carpeta_salida / idioma).mkdir(parents=True, exist_ok=True)

        # Carpeta para archivos procesados
        self.carpeta_procesados = self.carpeta_entrada / "_procesados"

    def detectar_archivos_pendientes(self) -> List[Path]:
        """
        Detecta archivos XLIFF pendientes de traducir.

        Returns:
            Lista de rutas a archivos XLIFF
        """
        archivos = []
        for archivo in self.carpeta_entrada.glob("*.xliff"):
            if archivo.is_file():
                archivos.append(archivo)
        return sorted(archivos)

    def procesar_archivo(self, archivo: Path) -> ResultadoProcesamiento:
        """
        Procesa un archivo traduciéndolo a todos los idiomas.

        Args:
            archivo: Ruta al archivo XLIFF

        Returns:
            ResultadoProcesamiento con el resultado
        """
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"Procesando: {archivo.name}")
        self.logger.info(f"{'='*60}")

        service = TranslationService(
            db_path=self.db_path,
            base_dir_salida=str(self.carpeta_salida)
        )

        idiomas_ok, errores = self._traducir_a_todos_idiomas(archivo, service)

        if self.mover_procesados and len(idiomas_ok) == len(self.IDIOMAS_DESTINO):
            self._mover_a_procesados(archivo)

        return ResultadoProcesamiento(
            archivo_origen=str(archivo),
            idiomas_procesados=idiomas_ok,
            exitoso=len(errores) == 0,
            errores=errores
        )

    def _traducir_a_todos_idiomas(
        self,
        archivo: Path,
        service: TranslationService
    ) -> tuple:
        """Traduce archivo a todos los idiomas destino."""
        idiomas_ok = []
        errores = []

        for idioma in self.IDIOMAS_DESTINO:
            try:
                self.logger.info(f"\n>>> Traduciendo a {idioma}...")
                resultado = service.traducir(str(archivo), idioma)

                if resultado.exitoso:
                    idiomas_ok.append(idioma)
                else:
                    errores.append(f"{idioma}: traducción con errores")
            except Exception as e:
                errores.append(f"{idioma}: {str(e)}")
                self.logger.error(f"Error traduciendo a {idioma}: {e}")

        return idiomas_ok, errores

    def _mover_a_procesados(self, archivo: Path) -> None:
        """Mueve un archivo a la carpeta de procesados."""
        self.carpeta_procesados.mkdir(exist_ok=True)
        destino = self.carpeta_procesados / archivo.name

        # Si ya existe, añadir timestamp
        if destino.exists():
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            destino = self.carpeta_procesados / f"{archivo.stem}_{timestamp}{archivo.suffix}"

        shutil.move(str(archivo), str(destino))
        self.logger.info(f"Archivo movido a: {destino}")

    def procesar_todos(self) -> List[ResultadoProcesamiento]:
        """
        Procesa todos los archivos pendientes.

        Returns:
            Lista de resultados de procesamiento
        """
        archivos = self.detectar_archivos_pendientes()

        if not archivos:
            self.logger.info("No hay archivos pendientes de traducir.")
            return []

        self.logger.info(f"Archivos encontrados: {len(archivos)}")
        resultados = []

        for archivo in archivos:
            resultado = self.procesar_archivo(archivo)
            resultados.append(resultado)

        # Resumen final
        self._mostrar_resumen(resultados)
        return resultados

    def _mostrar_resumen(self, resultados: List[ResultadoProcesamiento]) -> None:
        """Muestra resumen del procesamiento."""
        self.logger.info(f"\n{'='*60}")
        self.logger.info("RESUMEN DE PROCESAMIENTO")
        self.logger.info(f"{'='*60}")

        exitosos = sum(1 for r in resultados if r.exitoso)
        self.logger.info(f"Archivos procesados: {len(resultados)}")
        self.logger.info(f"Exitosos: {exitosos}")
        self.logger.info(f"Con errores: {len(resultados) - exitosos}")

        for r in resultados:
            estado = "✓" if r.exitoso else "✗"
            self.logger.info(f"  {estado} {Path(r.archivo_origen).name}: {', '.join(r.idiomas_procesados)}")
            for error in r.errores:
                self.logger.info(f"      Error: {error}")

    def watch(self, intervalo: int = 10) -> None:
        """
        Vigila la carpeta de entrada y procesa archivos automáticamente.

        Args:
            intervalo: Segundos entre cada verificación
        """
        self.logger.info(f"Iniciando watcher en: {self.carpeta_entrada}")
        self.logger.info(f"Intervalo de verificación: {intervalo}s")
        self.logger.info("Presiona Ctrl+C para detener.\n")

        try:
            while True:
                archivos = self.detectar_archivos_pendientes()

                if archivos:
                    self.logger.info(f"[{time.strftime('%H:%M:%S')}] Detectados {len(archivos)} archivo(s)")
                    self.procesar_todos()
                else:
                    self.logger.info(f"[{time.strftime('%H:%M:%S')}] Sin archivos pendientes...")

                time.sleep(intervalo)

        except KeyboardInterrupt:
            self.logger.info("\nWatcher detenido por el usuario.")
