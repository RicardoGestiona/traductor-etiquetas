#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migracion de checkpoints JSON legacy a base de datos SQLite.
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple

from traductor.database.db_manager import DatabaseManager
from traductor.utils.logger import get_logger

# Mapeo de archivos checkpoint a idiomas
CHECKPOINT_MAPPING = {
    "checkpoint_simple.json": "ca",      # Catalan
    "checkpoint_euskera.json": "eu",     # Euskera
    "checkpoint_gallego.json": "gl",     # Gallego
}


class CheckpointMigrator:
    """Migra checkpoints JSON a SQLite."""

    def __init__(self, db_manager: DatabaseManager, base_dir: str = "."):
        """
        Inicializa el migrador.

        Args:
            db_manager: Instancia del gestor de BD
            base_dir: Directorio donde buscar checkpoints
        """
        self.db = db_manager
        self.base_dir = Path(base_dir)
        self.logger = get_logger()

    def detectar_checkpoints(self) -> List[Tuple[str, str]]:
        """
        Detecta archivos checkpoint existentes.

        Returns:
            Lista de tuplas (ruta_archivo, codigo_idioma)
        """
        encontrados = []

        for archivo, idioma in CHECKPOINT_MAPPING.items():
            ruta = self.base_dir / archivo
            if ruta.exists():
                encontrados.append((str(ruta), idioma))

        return encontrados

    def cargar_checkpoint(self, ruta: str) -> Dict[str, str]:
        """
        Carga un archivo checkpoint JSON.

        Args:
            ruta: Ruta al archivo JSON

        Returns:
            Diccionario con traducciones
        """
        try:
            with open(ruta, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error al cargar {ruta}: {e}")
            return {}

    def migrar_checkpoint(self, ruta: str, idioma_destino: str) -> int:
        """
        Migra un checkpoint a la base de datos.

        Args:
            ruta: Ruta al archivo checkpoint
            idioma_destino: Codigo del idioma destino

        Returns:
            Numero de traducciones migradas
        """
        self.logger.info(f"Migrando {ruta} -> idioma '{idioma_destino}'")

        datos = self.cargar_checkpoint(ruta)
        if not datos:
            return 0

        # Preparar traducciones para insercion masiva
        traducciones = []
        for texto_origen, texto_traducido in datos.items():
            if texto_origen and texto_traducido:
                traducciones.append((texto_origen, texto_traducido))

        # Guardar en cache
        total = self.db.guardar_lote_cache(idioma_destino, traducciones)

        self.logger.info(f"  Migradas {total} traducciones")
        return total

    def migrar_todos(self, archivar: bool = True) -> Dict[str, int]:
        """
        Migra todos los checkpoints detectados.

        Args:
            archivar: Si True, mueve los JSON a carpeta 'legacy/'

        Returns:
            Diccionario {idioma: total_migradas}
        """
        checkpoints = self.detectar_checkpoints()

        if not checkpoints:
            self.logger.info("No se encontraron checkpoints para migrar")
            return {}

        self.logger.info(f"Encontrados {len(checkpoints)} checkpoints")

        resultados = {}
        archivos_migrados = []

        for ruta, idioma in checkpoints:
            total = self.migrar_checkpoint(ruta, idioma)
            resultados[idioma] = total
            if total > 0:
                archivos_migrados.append(ruta)

        # Archivar checkpoints migrados
        if archivar and archivos_migrados:
            self._archivar_checkpoints(archivos_migrados)

        return resultados

    def _archivar_checkpoints(self, archivos: List[str]) -> None:
        """
        Mueve checkpoints migrados a carpeta legacy.

        Args:
            archivos: Lista de rutas a archivar
        """
        legacy_dir = self.base_dir / "legacy"
        legacy_dir.mkdir(exist_ok=True)

        for archivo in archivos:
            origen = Path(archivo)
            destino = legacy_dir / origen.name

            try:
                origen.rename(destino)
                self.logger.info(f"  Archivado: {origen.name} -> legacy/")
            except Exception as e:
                self.logger.warning(f"  No se pudo archivar {origen.name}: {e}")

    def verificar_migracion(self) -> Dict[str, Dict]:
        """
        Verifica el estado de la migracion.

        Returns:
            Estadisticas de la migracion
        """
        stats = {
            "checkpoints_pendientes": [],
            "cache_por_idioma": self.db.obtener_conteo_cache(),
        }

        for archivo, idioma in CHECKPOINT_MAPPING.items():
            ruta = self.base_dir / archivo
            if ruta.exists():
                stats["checkpoints_pendientes"].append(archivo)

        return stats


def migrar_checkpoints(
    db_path: str = "traductor.db",
    base_dir: str = ".",
    archivar: bool = True
) -> Dict[str, int]:
    """
    Funcion de conveniencia para migrar checkpoints.

    Args:
        db_path: Ruta a la base de datos
        base_dir: Directorio con checkpoints
        archivar: Si mover checkpoints a legacy/

    Returns:
        Resultados de la migracion
    """
    db = DatabaseManager(db_path)
    migrador = CheckpointMigrator(db, base_dir)
    return migrador.migrar_todos(archivar)
