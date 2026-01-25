#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestor de base de datos SQLite para el sistema de traduccion.
"""

import hashlib
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple

from traductor.database.models import QUERIES, SCHEMA_SQL


class DatabaseManager:
    """Gestor de operaciones de base de datos."""

    def __init__(self, db_path: str = "traductor.db"):
        """
        Inicializa el gestor de base de datos.

        Args:
            db_path: Ruta al archivo SQLite
        """
        self.db_path = Path(db_path)
        self._inicializar_db()

    def _inicializar_db(self) -> None:
        """Crea las tablas si no existen."""
        with self._conexion() as conn:
            conn.executescript(SCHEMA_SQL)

    @contextmanager
    def _conexion(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager para conexiones a la BD."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @staticmethod
    def calcular_hash(texto: str) -> str:
        """
        Calcula hash MD5 de un texto para cache.

        Args:
            texto: Texto a hashear

        Returns:
            Hash MD5 hexadecimal
        """
        return hashlib.md5(texto.encode('utf-8')).hexdigest()

    # ==================== CACHE DE TRADUCCIONES ====================

    def buscar_en_cache(self, idioma_destino: str, texto_origen: str) -> Optional[str]:
        """
        Busca una traduccion en cache.

        Args:
            idioma_destino: Codigo del idioma destino
            texto_origen: Texto original a buscar

        Returns:
            Traduccion cacheada o None
        """
        hash_origen = self.calcular_hash(texto_origen)

        with self._conexion() as conn:
            cursor = conn.execute(
                QUERIES["buscar_cache"],
                (idioma_destino, hash_origen)
            )
            resultado = cursor.fetchone()

            if resultado:
                # Actualizar contador de uso
                conn.execute(
                    QUERIES["actualizar_uso_cache"],
                    (idioma_destino, hash_origen)
                )
                return resultado["texto_traducido"]

        return None

    def guardar_en_cache(
        self,
        idioma_destino: str,
        texto_origen: str,
        texto_traducido: str
    ) -> None:
        """
        Guarda una traduccion en cache.

        Args:
            idioma_destino: Codigo del idioma destino
            texto_origen: Texto original
            texto_traducido: Texto traducido
        """
        hash_origen = self.calcular_hash(texto_origen)

        with self._conexion() as conn:
            conn.execute(
                QUERIES["insertar_cache"],
                (idioma_destino, hash_origen, texto_origen, texto_traducido,
                 idioma_destino, hash_origen)
            )

    def guardar_lote_cache(
        self,
        idioma_destino: str,
        traducciones: List[Tuple[str, str]]
    ) -> int:
        """
        Guarda multiples traducciones en cache.

        Args:
            idioma_destino: Codigo del idioma destino
            traducciones: Lista de tuplas (texto_origen, texto_traducido)

        Returns:
            Numero de traducciones guardadas
        """
        with self._conexion() as conn:
            for texto_origen, texto_traducido in traducciones:
                hash_origen = self.calcular_hash(texto_origen)
                conn.execute(
                    QUERIES["insertar_cache"],
                    (idioma_destino, hash_origen, texto_origen, texto_traducido,
                     idioma_destino, hash_origen)
                )
        return len(traducciones)

    def obtener_todo_cache(self, idioma_destino: str) -> Dict[str, str]:
        """
        Obtiene todo el cache para un idioma.

        Args:
            idioma_destino: Codigo del idioma

        Returns:
            Diccionario {hash: traduccion}
        """
        with self._conexion() as conn:
            cursor = conn.execute(
                "SELECT hash_origen, texto_traducido FROM cache_traducciones WHERE idioma_destino = ?",
                (idioma_destino,)
            )
            return {row["hash_origen"]: row["texto_traducido"] for row in cursor}

    # ==================== SESIONES DE TRADUCCION ====================

    def registrar_traduccion(
        self,
        idioma_origen: str,
        idioma_destino: str,
        fichero_original: str,
        fichero_destino: str,
        total_etiquetas: int,
        total_traducidas: int,
        total_nuevas: int,
        total_reutilizadas: int,
        duracion_segundos: float = 0,
        estado: str = "completado"
    ) -> int:
        """
        Registra una sesion de traduccion.

        Returns:
            ID de la sesion creada
        """
        with self._conexion() as conn:
            cursor = conn.execute(
                QUERIES["insertar_traduccion"],
                (idioma_origen, idioma_destino, fichero_original, fichero_destino,
                 total_etiquetas, total_traducidas, total_nuevas, total_reutilizadas,
                 duracion_segundos, estado)
            )
            return cursor.lastrowid

    # ==================== ESTADISTICAS ====================

    def obtener_estadisticas_idioma(self, idioma_destino: str) -> Dict[str, Any]:
        """Obtiene estadisticas para un idioma especifico."""
        with self._conexion() as conn:
            cursor = conn.execute(
                QUERIES["obtener_estadisticas_idioma"],
                (idioma_destino,)
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
            return {}

    def obtener_estadisticas_globales(self) -> List[Dict[str, Any]]:
        """Obtiene estadisticas globales por idioma."""
        with self._conexion() as conn:
            cursor = conn.execute(QUERIES["obtener_estadisticas_globales"])
            return [dict(row) for row in cursor]

    def obtener_conteo_cache(self) -> Dict[str, int]:
        """Obtiene conteo de traducciones en cache por idioma."""
        with self._conexion() as conn:
            cursor = conn.execute(QUERIES["contar_cache_por_idioma"])
            return {row["idioma_destino"]: row["total"] for row in cursor}

    def obtener_historial(self, limite: int = 10) -> List[Dict[str, Any]]:
        """Obtiene historial de traducciones."""
        with self._conexion() as conn:
            cursor = conn.execute(QUERIES["obtener_historial"], (limite,))
            return [dict(row) for row in cursor]

    # ==================== UTILIDADES ====================

    def limpiar_cache(self, idioma_destino: Optional[str] = None) -> int:
        """
        Limpia el cache de traducciones.

        Args:
            idioma_destino: Si se especifica, solo limpia ese idioma

        Returns:
            Numero de registros eliminados
        """
        with self._conexion() as conn:
            if idioma_destino:
                cursor = conn.execute(
                    "DELETE FROM cache_traducciones WHERE idioma_destino = ?",
                    (idioma_destino,)
                )
            else:
                cursor = conn.execute("DELETE FROM cache_traducciones")
            return cursor.rowcount

    def exportar_cache_json(self, idioma_destino: str) -> Dict[str, str]:
        """
        Exporta cache a formato compatible con checkpoints legacy.

        Args:
            idioma_destino: Codigo del idioma

        Returns:
            Diccionario {texto_origen: texto_traducido}
        """
        with self._conexion() as conn:
            cursor = conn.execute(
                "SELECT texto_origen, texto_traducido FROM cache_traducciones WHERE idioma_destino = ?",
                (idioma_destino,)
            )
            return {row["texto_origen"]: row["texto_traducido"] for row in cursor}

    # ==================== TRADUCCIONES PENDIENTES ====================

    def guardar_pendiente(
        self,
        idioma_destino: str,
        texto_origen: str,
        motivo_fallo: str,
        archivo_origen: Optional[str] = None
    ) -> None:
        """
        Guarda una traduccion que fallo para reintentar despues.

        Args:
            idioma_destino: Codigo del idioma destino
            texto_origen: Texto original que no se pudo traducir
            motivo_fallo: Descripcion del error
            archivo_origen: Archivo XLIFF de donde proviene
        """
        hash_origen = self.calcular_hash(texto_origen)

        with self._conexion() as conn:
            conn.execute(
                QUERIES["insertar_pendiente"],
                (idioma_destino, hash_origen, texto_origen, motivo_fallo,
                 archivo_origen, idioma_destino, hash_origen)
            )

    def guardar_lote_pendientes(
        self,
        idioma_destino: str,
        pendientes: List[Tuple[str, str]],
        archivo_origen: Optional[str] = None
    ) -> int:
        """
        Guarda multiples traducciones pendientes.

        Args:
            idioma_destino: Codigo del idioma destino
            pendientes: Lista de tuplas (texto_origen, motivo_fallo)
            archivo_origen: Archivo XLIFF de donde provienen

        Returns:
            Numero de pendientes guardados
        """
        with self._conexion() as conn:
            for texto_origen, motivo_fallo in pendientes:
                hash_origen = self.calcular_hash(texto_origen)
                conn.execute(
                    QUERIES["insertar_pendiente"],
                    (idioma_destino, hash_origen, texto_origen, motivo_fallo,
                     archivo_origen, idioma_destino, hash_origen)
                )
        return len(pendientes)

    def obtener_pendientes(self, idioma_destino: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Obtiene traducciones pendientes.

        Args:
            idioma_destino: Si se especifica, filtra por idioma

        Returns:
            Lista de traducciones pendientes
        """
        with self._conexion() as conn:
            if idioma_destino:
                cursor = conn.execute(QUERIES["obtener_pendientes"], (idioma_destino,))
            else:
                cursor = conn.execute(QUERIES["obtener_todas_pendientes"])
            return [dict(row) for row in cursor]

    def eliminar_pendiente(self, idioma_destino: str, texto_origen: str) -> bool:
        """
        Elimina una traduccion de la lista de pendientes.

        Args:
            idioma_destino: Codigo del idioma
            texto_origen: Texto original

        Returns:
            True si se elimino, False si no existia
        """
        hash_origen = self.calcular_hash(texto_origen)

        with self._conexion() as conn:
            cursor = conn.execute(
                QUERIES["eliminar_pendiente"],
                (idioma_destino, hash_origen)
            )
            return cursor.rowcount > 0

    def contar_pendientes(self) -> Dict[str, int]:
        """
        Cuenta traducciones pendientes por idioma.

        Returns:
            Diccionario {idioma: cantidad}
        """
        with self._conexion() as conn:
            cursor = conn.execute(QUERIES["contar_pendientes_por_idioma"])
            return {row["idioma_destino"]: row["total"] for row in cursor}

    def limpiar_pendientes(self, idioma_destino: Optional[str] = None) -> int:
        """
        Limpia traducciones pendientes.

        Args:
            idioma_destino: Si se especifica, solo limpia ese idioma

        Returns:
            Numero de registros eliminados
        """
        with self._conexion() as conn:
            if idioma_destino:
                cursor = conn.execute(
                    "DELETE FROM traducciones_pendientes WHERE idioma_destino = ?",
                    (idioma_destino,)
                )
            else:
                cursor = conn.execute("DELETE FROM traducciones_pendientes")
            return cursor.rowcount
