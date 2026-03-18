#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Clase base abstracta para traductores.
"""

import re
import time
from abc import ABC, abstractmethod
from typing import Optional

PLACEHOLDER_PATTERN = re.compile(r'\{[^}]+\}')
# Token format: ⟪N⟫ using Unicode mathematical double angle brackets (U+27EA/U+27EB)
# Google Translate preserves these because they are not natural language characters
_PH_LEFT = '\u27ea'
_PH_RIGHT = '\u27eb'
_PH_TOKEN_PATTERN = re.compile(
    rf'{_PH_LEFT}\s*(\d+)\s*{_PH_RIGHT}'
)

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

    def traducir(self, texto: str) -> Optional[str]:
        """
        Traduce un texto con manejo de reintentos.
        Protege variables {placeholder} automaticamente.

        Args:
            texto: Texto a traducir

        Returns:
            Texto traducido o None si falla tras todos los reintentos
        """
        if not texto or not texto.strip():
            return texto

        texto_protegido, placeholders = self._proteger_placeholders(texto)

        for intento in range(self.reintentos):
            resultado = self._ejecutar_traduccion_con_reintentos(texto_protegido, intento)
            if resultado is not None:
                self._traducciones_realizadas += 1
                return self._restaurar_placeholders(resultado, placeholders)

        return None

    def _proteger_placeholders(self, texto: str) -> tuple:
        """Extrae {variables} y las reemplaza con tokens Unicode seguros."""
        placeholders = PLACEHOLDER_PATTERN.findall(texto)
        texto_protegido = texto
        for i, ph in enumerate(placeholders):
            texto_protegido = texto_protegido.replace(
                ph, f"{_PH_LEFT}{i}{_PH_RIGHT}", 1
            )
        return texto_protegido, placeholders

    def _restaurar_placeholders(self, texto: str, placeholders: list) -> str:
        """Restaura los tokens Unicode por las variables originales."""
        if not placeholders:
            return texto

        def reemplazar_token(match):
            idx = int(match.group(1))
            if idx < len(placeholders):
                return placeholders[idx]
            return match.group(0)

        resultado = _PH_TOKEN_PATTERN.sub(reemplazar_token, texto)

        # Fallback: si quedan tokens sin resolver, forzar por posicion
        for i, ph in enumerate(placeholders):
            token_exacto = f"{_PH_LEFT}{i}{_PH_RIGHT}"
            if token_exacto in resultado:
                resultado = resultado.replace(token_exacto, ph, 1)

        return resultado

    def _ejecutar_traduccion_con_reintentos(self, texto: str, intento: int) -> Optional[str]:
        """Ejecuta traduccion con logica de reintentos."""
        try:
            return self._traducir_interno(texto)

        except Exception as e:
            self._errores += 1
            if intento < self.reintentos - 1:
                delay = min(self.delay_base * (2 ** intento), 30.0)
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
