#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Clase base abstracta para traductores.
"""

import time
from abc import ABC, abstractmethod
from typing import Optional

from traductor.config.idiomas import ConfigIdioma, IDIOMA_ORIGEN_DEFAULT
from traductor.utils.logger import get_logger


class BaseTranslator(ABC):
    """Clase base para implementaciones de traductores."""

    def __init__(
        self,
        idioma_origen: str = IDIOMA_ORIGEN_DEFAULT,
        config_destino: Optional[ConfigIdioma] = None,
        reintentos: int = 3,
        delay_entre_reintentos: float = 1.0
    ):
        """
        Inicializa el traductor base.

        Args:
            idioma_origen: Codigo del idioma de origen
            config_destino: Configuracion del idioma destino
            reintentos: Numero de reintentos en caso de error
            delay_entre_reintentos: Delay base entre reintentos (exponencial)
        """
        self.idioma_origen = idioma_origen
        self.config_destino = config_destino
        self.reintentos = reintentos
        self.delay_base = delay_entre_reintentos
        self.logger = get_logger()

        self._traducciones_realizadas = 0
        self._errores = 0

    @abstractmethod
    def _traducir_interno(self, texto: str) -> str:
        """
        Implementacion interna de traduccion.

        Args:
            texto: Texto a traducir

        Returns:
            Texto traducido

        Raises:
            Exception: Si falla la traduccion
        """
        pass

    def traducir(self, texto: str) -> str:
        """
        Traduce un texto con manejo de reintentos.

        Args:
            texto: Texto a traducir

        Returns:
            Texto traducido (o original si falla)
        """
        if not texto or not texto.strip():
            return texto

        for intento in range(self.reintentos):
            resultado = self._ejecutar_traduccion_con_reintentos(texto, intento)
            if resultado is not None:
                self._traducciones_realizadas += 1
                return resultado

        return texto

    def _ejecutar_traduccion_con_reintentos(self, texto: str, intento: int) -> Optional[str]:
        """Ejecuta traduccion con logica de reintentos."""
        try:
            return self._traducir_interno(texto)

        except Exception as e:
            self._errores += 1
            if intento < self.reintentos - 1:
                delay = self.delay_base * (2 ** intento)
                self.logger.warning(
                    f"Error en intento {intento + 1}, reintentando en {delay}s..."
                )
                time.sleep(delay)
            else:
                self.logger.error(
                    f"Error al traducir despues de {self.reintentos} intentos: {texto[:50]}..."
                )
            return None

    @property
    def estadisticas(self) -> dict:
        """Retorna estadisticas del traductor."""
        return {
            "traducciones_realizadas": self._traducciones_realizadas,
            "errores": self._errores,
            "idioma_origen": self.idioma_origen,
            "idioma_destino": self.config_destino.codigo if self.config_destino else None,
        }

    def reiniciar_estadisticas(self) -> None:
        """Reinicia contadores de estadisticas."""
        self._traducciones_realizadas = 0
        self._errores = 0


class GoogleTranslatorWrapper(BaseTranslator):
    """Implementacion usando deep_translator con Google Translate."""

    def __init__(
        self,
        idioma_origen: str = IDIOMA_ORIGEN_DEFAULT,
        config_destino: Optional[ConfigIdioma] = None,
        **kwargs
    ):
        super().__init__(idioma_origen, config_destino, **kwargs)

        try:
            from deep_translator import GoogleTranslator
        except ImportError:
            raise ImportError(
                "deep-translator no esta instalado. "
                "Instala con: pip install deep-translator"
            )

        idioma_destino = config_destino.codigo if config_destino else "es"
        self._translator = GoogleTranslator(
            source=idioma_origen,
            target=idioma_destino
        )

    def _traducir_interno(self, texto: str) -> str:
        """Traduce usando Google Translate."""
        return self._translator.translate(texto)

    def cambiar_idioma_destino(self, config_destino: ConfigIdioma) -> None:
        """
        Cambia el idioma de destino.

        Args:
            config_destino: Nueva configuracion de idioma
        """
        from deep_translator import GoogleTranslator

        self.config_destino = config_destino
        self._translator = GoogleTranslator(
            source=self.idioma_origen,
            target=config_destino.codigo
        )


def crear_traductor(
    tipo: str = "google",
    idioma_origen: str = IDIOMA_ORIGEN_DEFAULT,
    config_destino: Optional[ConfigIdioma] = None,
    **kwargs
) -> BaseTranslator:
    """
    Factory para crear traductores.

    Args:
        tipo: Tipo de traductor ('google', 'deepl', etc.)
        idioma_origen: Codigo del idioma origen
        config_destino: Configuracion del idioma destino
        **kwargs: Argumentos adicionales para el traductor

    Returns:
        Instancia de traductor
    """
    traductores = {
        "google": GoogleTranslatorWrapper,
    }

    if tipo not in traductores:
        raise ValueError(
            f"Tipo de traductor '{tipo}' no soportado. "
            f"Opciones: {list(traductores.keys())}"
        )

    return traductores[tipo](
        idioma_origen=idioma_origen,
        config_destino=config_destino,
        **kwargs
    )
