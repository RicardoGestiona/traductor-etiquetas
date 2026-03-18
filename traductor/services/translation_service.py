#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servicio principal de traduccion.

Coordina todos los componentes del sistema para realizar traducciones
completas o incrementales de archivos XLIFF.
"""

import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    tqdm = None
    TQDM_AVAILABLE = False

from traductor.config.idiomas import ConfigIdioma, obtener_config_idioma
from traductor.core.base_translator import crear_traductor, BaseTranslator, PLACEHOLDER_PATTERN
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
    pendientes: int
    duracion_segundos: float
    exitoso: bool


@dataclass
class ContextoFinalizacion:
    """Contexto agrupado para finalizar una traduccion."""
    parser: object
    resultado_deteccion: object
    config_idioma: object
    archivo_entrada: str
    archivo_salida: str
    traducciones_pendientes: List[Tuple[str, str]]
    nuevas_traducciones: List[Tuple[str, str]]
    inicio: float
    fin: float


class TranslationService:
    """Servicio principal de traduccion XLIFF."""

    def __init__(
        self,
        db_path: str = "traductor.db",
        base_dir_salida: str = "Idiomas",
        tipo_traductor: str = "google",
        pausa_cada_n: int = 50,
        delay_pausa: float = 1.0,
        guardar_cache_cada_n: int = 100
    ):
        """
        Inicializa el servicio de traduccion.

        Args:
            db_path: Ruta a la base de datos SQLite
            base_dir_salida: Directorio base para archivos traducidos
            tipo_traductor: Tipo de traductor a usar ('google', etc.)
            pausa_cada_n: Pausar cada N traducciones nuevas
            delay_pausa: Segundos de pausa
            guardar_cache_cada_n: Guardar cache incrementalmente cada N traducciones
        """
        self.db = DatabaseManager(db_path)
        self.file_naming = FileNaming(base_dir_salida)
        self.detector = IncrementalDetector(self.db)
        self.tipo_traductor = tipo_traductor
        self.pausa_cada_n = pausa_cada_n
        self.delay_pausa = delay_pausa
        self.guardar_cache_cada_n = guardar_cache_cada_n
        self.logger = get_logger()

        self._traductor: Optional[BaseTranslator] = None

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
        config_idioma = self._validar_y_obtener_config(idioma_destino)
        parser, archivo_salida = self._preparar_documento(archivo_entrada, archivo_salida, config_idioma)
        resultado_deteccion = self._analizar_traducciones_necesarias(
            parser, config_idioma, forzar_retraduccion
        )

        self._traductor = crear_traductor(
            tipo=self.tipo_traductor,
            config_destino=config_idioma
        )

        self._aplicar_cache(parser, resultado_deteccion)
        traducciones_pendientes, nuevas_traducciones = self._traducir_nuevas(
            parser, resultado_deteccion, config_idioma
        )

        contexto = ContextoFinalizacion(
            parser=parser,
            resultado_deteccion=resultado_deteccion,
            config_idioma=config_idioma,
            archivo_entrada=archivo_entrada,
            archivo_salida=archivo_salida,
            traducciones_pendientes=traducciones_pendientes,
            nuevas_traducciones=nuevas_traducciones,
            inicio=inicio,
            fin=time.time()
        )
        resultado = self._finalizar_traduccion(contexto)

        self._mostrar_resumen(resultado)
        return resultado

    def _validar_y_obtener_config(self, idioma_destino: str) -> ConfigIdioma:
        """Valida idioma y retorna configuracion."""
        config_idioma = obtener_config_idioma(idioma_destino)
        if config_idioma is None:
            raise ValueError(f"Idioma no soportado: {idioma_destino}")
        self.logger.info(f"Traduciendo a {config_idioma.nombre}...")
        return config_idioma

    def _preparar_documento(
        self,
        archivo_entrada: str,
        archivo_salida: Optional[str],
        config_idioma: ConfigIdioma
    ) -> tuple:
        """Carga, parsea y prepara documento XLIFF."""
        if archivo_salida is None:
            archivo_salida = self.file_naming.generar_nombre_salida(
                archivo_entrada, config_idioma
            )
        self.file_naming.asegurar_directorio(archivo_salida)

        self.logger.info(f"Cargando: {archivo_entrada}")
        parser = XLIFFParser()
        doc = parser.cargar(archivo_entrada)
        parser.actualizar_target_language(config_idioma.codigo)
        self.logger.info(f"Total de unidades: {doc.total_unidades}")
        return parser, archivo_salida

    def _analizar_traducciones_necesarias(
        self,
        parser: XLIFFParser,
        config_idioma: ConfigIdioma,
        forzar_retraduccion: bool
    ) -> ResultadoDeteccion:
        """Analiza que etiquetas necesitan traduccion."""
        if forzar_retraduccion:
            return ResultadoDeteccion(
                total_etiquetas=parser.doc.total_unidades,
                etiquetas_nuevas=list(parser.iterar_unidades()),
                etiquetas_en_cache=[],
                etiquetas_modificadas=[]
            )
        else:
            resultado = self.detector.analizar(parser, config_idioma.codigo)
            self.logger.info(self.detector.generar_resumen(resultado))
            return resultado

    def _aplicar_cache(
        self,
        parser: XLIFFParser,
        resultado_deteccion: ResultadoDeteccion
    ) -> None:
        """Aplica traducciones desde cache."""
        for unit, traduccion in resultado_deteccion.etiquetas_en_cache:
            parser.actualizar_traduccion(unit, traduccion)

    def _traducir_nuevas(
        self,
        parser: XLIFFParser,
        resultado_deteccion: ResultadoDeteccion,
        config_idioma: ConfigIdioma
    ) -> tuple:
        """Orquesta la traduccion de etiquetas nuevas."""
        traducciones_pendientes = []
        nuevas_traducciones = []
        buffer_cache = []

        total_nuevas = resultado_deteccion.total_nuevas
        if total_nuevas == 0:
            return traducciones_pendientes, nuevas_traducciones

        self.logger.info(f"Traduciendo {total_nuevas} etiquetas nuevas...")
        iterador = self._crear_iterador_progreso(resultado_deteccion.etiquetas_nuevas, total_nuevas)

        for idx, unit in enumerate(iterador, 1):
            texto_original = unit.target
            if not texto_original or not texto_original.strip():
                self.logger.debug(f"Ignorando etiqueta vacia: {unit.id}")
                continue

            self._traducir_unidad(
                unit, texto_original, parser, config_idioma,
                traducciones_pendientes, nuevas_traducciones, buffer_cache
            )
            self._aplicar_pausa_rate_limit(idx, total_nuevas)

        self._guardar_cache_incremental(buffer_cache, config_idioma, es_final=True)
        return traducciones_pendientes, nuevas_traducciones

    def _crear_iterador_progreso(self, etiquetas: list, total: int):
        """Encapsula la creacion del iterador con barra de progreso."""
        if TQDM_AVAILABLE:
            return tqdm(etiquetas, desc="Traduciendo", unit=" etiquetas")
        return etiquetas

    def _traducir_unidad(
        self, unit, texto_original: str, parser: XLIFFParser,
        config_idioma: ConfigIdioma, pendientes: list,
        nuevas: list, buffer_cache: list
    ) -> None:
        """Traduce una unidad individual, valida resultado y gestiona buffer."""
        try:
            traduccion = self._traductor.traducir(texto_original)

            if traduccion is None or traduccion.strip() == "":
                pendientes.append((texto_original, "API devolvio respuesta vacia"))
                self.logger.warning(f"API vacia para: {texto_original[:50]}...")
                return

            if traduccion == texto_original:
                pendientes.append((texto_original, "API retorno texto identico"))
                self.logger.warning(f"Traduccion identica al original: {texto_original[:50]}...")
                return

            placeholders_origen = set(PLACEHOLDER_PATTERN.findall(texto_original))
            if placeholders_origen:
                placeholders_traduccion = set(PLACEHOLDER_PATTERN.findall(traduccion))
                perdidos = placeholders_origen - placeholders_traduccion
                if perdidos:
                    # Reintento con tokens alfanumericos [[PH0]], [[PH1]]...
                    self.logger.warning(
                        f"Placeholders perdidos, reintentando con tokens alternativos: {texto_original[:50]}..."
                    )
                    traduccion = self._reintentar_con_tokens_alt(texto_original)
                    if traduccion is None:
                        pendientes.append((texto_original, f"Placeholders perdidos en traduccion: {perdidos}"))
                        return

            parser.actualizar_traduccion(unit, traduccion)
            nuevas.append((texto_original, traduccion))
            buffer_cache.append((texto_original, traduccion))

            if len(buffer_cache) >= self.guardar_cache_cada_n:
                self._guardar_cache_incremental(buffer_cache, config_idioma, es_final=False)
                buffer_cache.clear()

        except Exception as e:
            pendientes.append((texto_original, str(e)))
            self.logger.error(f"Error en unidad {unit.id}: {e}")

    def _reintentar_con_tokens_alt(self, texto: str) -> Optional[str]:
        """
        Reintenta traduccion usando tokens alfanumericos [[PH0]] en lugar
        de Unicode. Fallback cuando Google Translate corrompe los tokens.

        Args:
            texto: Texto original con {placeholders}

        Returns:
            Texto traducido con placeholders restaurados, o None si falla
        """
        placeholders = PLACEHOLDER_PATTERN.findall(texto)
        if not placeholders:
            return None

        # Proteger con tokens alfanumericos
        texto_protegido = texto
        for i, ph in enumerate(placeholders):
            texto_protegido = texto_protegido.replace(ph, f"[[PH{i}]]", 1)

        # Traducir
        resultado = self._traductor._traducir_interno(texto_protegido)
        if resultado is None:
            return None

        # Restaurar placeholders
        for i, ph in enumerate(placeholders):
            variantes = [f"[[PH{i}]]", f"[[ PH{i} ]]", f"[[PH {i}]]", f"[[ PH{i}]]"]
            for variante in variantes:
                if variante in resultado:
                    resultado = resultado.replace(variante, ph, 1)
                    break

        # Validar que todos los placeholders fueron restaurados
        placeholders_resultado = set(PLACEHOLDER_PATTERN.findall(resultado))
        if set(placeholders) - placeholders_resultado:
            self.logger.error(
                f"Tokens alternativos tambien fallaron: {texto[:50]}..."
            )
            return None

        self.logger.info("Reintento con tokens alternativos exitoso")
        return resultado

    def _guardar_cache_incremental(
        self, buffer: list, config_idioma: ConfigIdioma, es_final: bool
    ) -> None:
        """Guarda buffer de cache parcial o final."""
        if not buffer:
            return
        self.db.guardar_lote_cache(config_idioma.codigo, buffer)
        tipo = "final" if es_final else "parcial"
        self.logger.info(f"Cache {tipo} guardado: {len(buffer)} traducciones")

    def _aplicar_pausa_rate_limit(self, idx: int, total: int) -> None:
        """Aplica pausa cada N traducciones y muestra progreso sin tqdm."""
        if idx % self.pausa_cada_n == 0:
            time.sleep(self.delay_pausa)
        if not TQDM_AVAILABLE and idx % 100 == 0:
            self.logger.progress(idx, total)

    def _finalizar_traduccion(self, contexto: ContextoFinalizacion) -> ResultadoTraduccion:
        """Guarda archivo y registra sesion en BD."""
        if contexto.traducciones_pendientes:
            self.db.guardar_lote_pendientes(
                contexto.config_idioma.codigo,
                contexto.traducciones_pendientes,
                contexto.archivo_entrada
            )
            self.logger.warning(
                f"Registradas {len(contexto.traducciones_pendientes)} traducciones pendientes para reintentar"
            )

        # Aplicar cabecera custom si el idioma la define
        if contexto.config_idioma.cabecera_custom:
            contexto.parser.reemplazar_cabecera(contexto.config_idioma.cabecera_custom)

        self.logger.info(f"Guardando: {contexto.archivo_salida}")
        contexto.parser.guardar(contexto.archivo_salida)

        duracion = contexto.fin - contexto.inicio
        errores = len(contexto.traducciones_pendientes)

        self.db.registrar_traduccion(
            idioma_origen="en",
            idioma_destino=contexto.config_idioma.codigo,
            fichero_original=contexto.archivo_entrada,
            fichero_destino=contexto.archivo_salida,
            total_etiquetas=contexto.resultado_deteccion.total_etiquetas,
            total_traducidas=contexto.resultado_deteccion.total_etiquetas - errores,
            total_nuevas=len(contexto.nuevas_traducciones),
            total_reutilizadas=contexto.resultado_deteccion.total_en_cache,
            duracion_segundos=duracion,
            estado="completado" if errores == 0 else "con_errores"
        )

        return ResultadoTraduccion(
            archivo_origen=contexto.archivo_entrada,
            archivo_destino=contexto.archivo_salida,
            idioma_destino=contexto.config_idioma.nombre,
            total_etiquetas=contexto.resultado_deteccion.total_etiquetas,
            traducidas=contexto.resultado_deteccion.total_etiquetas - errores,
            nuevas=len(contexto.nuevas_traducciones),
            reutilizadas=contexto.resultado_deteccion.total_en_cache,
            errores=errores,
            pendientes=len(contexto.traducciones_pendientes),
            duracion_segundos=duracion,
            exitoso=errores == 0
        )

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
            resultado = self._procesar_idioma_individual(
                archivo_entrada, idioma, forzar_retraduccion
            )
            if resultado:
                resultados.append(resultado)
        return resultados

    def _procesar_idioma_individual(
        self,
        archivo_entrada: str,
        idioma: str,
        forzar_retraduccion: bool
    ) -> Optional[ResultadoTraduccion]:
        """Procesa traduccion de un idioma individual."""
        self.logger.info(f"\n{'='*50}")
        self.logger.info(f"Procesando: {idioma}")
        self.logger.info(f"{'='*50}")

        try:
            return self.traducir(
                archivo_entrada,
                idioma,
                forzar_retraduccion=forzar_retraduccion
            )
        except Exception as e:
            self.logger.error(f"Error al traducir a {idioma}: {e}")
            return None

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
        if resultado.pendientes > 0:
            self.logger.info(f"  Pendientes (reintentar): {resultado.pendientes}")
        self.logger.info(f"  Duracion: {resultado.duracion_segundos:.1f}s")

    def obtener_estadisticas(self) -> dict:
        """Obtiene estadisticas globales del sistema."""
        return {
            "por_idioma": self.db.obtener_estadisticas_globales(),
            "cache": self.db.obtener_conteo_cache(),
            "historial_reciente": self.db.obtener_historial(5)
        }
