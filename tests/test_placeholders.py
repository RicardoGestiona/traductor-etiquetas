#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests para proteccion de variables {placeholder} en traducciones.
"""

import re
import unittest
from unittest.mock import patch
from typing import Optional

from traductor.core.base_translator import (
    BaseTranslator,
    PLACEHOLDER_PATTERN,
    _PH_LEFT,
    _PH_RIGHT,
)
from traductor.config.idiomas import ConfigIdioma


def _token(n: int) -> str:
    """Helper: genera token placeholder con formato Unicode."""
    return f"{_PH_LEFT}{n}{_PH_RIGHT}"


class FakeTranslator(BaseTranslator):
    """Traductor fake que simula Google Translate."""

    def __init__(self, traducciones: Optional[dict] = None):
        config = ConfigIdioma(
            codigo="ca", codigo_archivo="ca",
            nombre="catalan", carpeta="catalan"
        )
        super().__init__(idioma_origen="en", config_destino=config)
        self._traducciones = traducciones or {}

    def _traducir_interno(self, texto: str) -> str:
        if texto in self._traducciones:
            return self._traducciones[texto]
        return f"[traducido]{texto}[/traducido]"


class TestPlaceholderPattern(unittest.TestCase):
    """Tests para el patron regex de placeholders."""

    def test_detecta_placeholder_simple(self):
        matches = PLACEHOLDER_PATTERN.findall("Hello {name}")
        self.assertEqual(matches, ["{name}"])

    def test_detecta_multiples_placeholders(self):
        matches = PLACEHOLDER_PATTERN.findall("{current} of {total}")
        self.assertEqual(matches, ["{current}", "{total}"])

    def test_sin_placeholders(self):
        matches = PLACEHOLDER_PATTERN.findall("Hello world")
        self.assertEqual(matches, [])

    def test_placeholder_con_underscore(self):
        matches = PLACEHOLDER_PATTERN.findall("Value: {max_value}")
        self.assertEqual(matches, ["{max_value}"])

    def test_placeholder_con_numeros(self):
        matches = PLACEHOLDER_PATTERN.findall("Item {item1} and {item2}")
        self.assertEqual(matches, ["{item1}", "{item2}"])


class TestProtegerPlaceholders(unittest.TestCase):
    """Tests para _proteger_placeholders."""

    def setUp(self):
        self.translator = FakeTranslator()

    def test_sin_placeholders(self):
        texto, placeholders = self.translator._proteger_placeholders("Hello world")
        self.assertEqual(texto, "Hello world")
        self.assertEqual(placeholders, [])

    def test_un_placeholder(self):
        texto, placeholders = self.translator._proteger_placeholders("Hello {name}")
        self.assertEqual(texto, f"Hello {_token(0)}")
        self.assertEqual(placeholders, ["{name}"])

    def test_multiples_placeholders(self):
        texto, placeholders = self.translator._proteger_placeholders(
            "{current} of {total} items"
        )
        self.assertEqual(texto, f"{_token(0)} of {_token(1)} items")
        self.assertEqual(placeholders, ["{current}", "{total}"])

    def test_placeholders_duplicados(self):
        texto, placeholders = self.translator._proteger_placeholders(
            "{name} and {name}"
        )
        self.assertEqual(texto, f"{_token(0)} and {_token(1)}")
        self.assertEqual(placeholders, ["{name}", "{name}"])


class TestRestaurarPlaceholders(unittest.TestCase):
    """Tests para _restaurar_placeholders."""

    def setUp(self):
        self.translator = FakeTranslator()

    def test_sin_placeholders(self):
        resultado = self.translator._restaurar_placeholders("Hola mundo", [])
        self.assertEqual(resultado, "Hola mundo")

    def test_un_placeholder(self):
        resultado = self.translator._restaurar_placeholders(
            f"Hola {_token(0)}", ["{name}"]
        )
        self.assertEqual(resultado, "Hola {name}")

    def test_multiples_placeholders(self):
        resultado = self.translator._restaurar_placeholders(
            f"{_token(0)} de {_token(1)} elements",
            ["{current}", "{total}"]
        )
        self.assertEqual(resultado, "{current} de {total} elements")

    def test_restaurar_con_espacios_mangling(self):
        """Google Translate a veces anade espacios alrededor del numero."""
        resultado = self.translator._restaurar_placeholders(
            f"{_PH_LEFT} 0 {_PH_RIGHT} de {_PH_LEFT} 1{_PH_RIGHT} elements",
            ["{current}", "{total}"]
        )
        self.assertEqual(resultado, "{current} de {total} elements")


class TestTraducirConPlaceholders(unittest.TestCase):
    """Tests de integracion: traducir() preserva placeholders."""

    def test_texto_sin_placeholders(self):
        translator = FakeTranslator({
            "Hello world": "Hola mon"
        })
        resultado = translator.traducir("Hello world")
        self.assertEqual(resultado, "Hola mon")

    def test_texto_con_placeholder(self):
        translator = FakeTranslator({
            f"Page {_token(0)} of {_token(1)}": f"Pagina {_token(0)} de {_token(1)}"
        })
        resultado = translator.traducir("Page {current} of {total}")
        self.assertEqual(resultado, "Pagina {current} de {total}")

    def test_solo_placeholder(self):
        translator = FakeTranslator({
            f"{_token(0)}": f"{_token(0)}"
        })
        resultado = translator.traducir("{max}")
        self.assertEqual(resultado, "{max}")

    def test_placeholder_duplicado_preservado(self):
        translator = FakeTranslator({
            f"{_token(0)} i {_token(1)}": f"{_token(0)} i {_token(1)}"
        })
        resultado = translator.traducir("{name} i {name}")
        self.assertEqual(resultado, "{name} i {name}")

    def test_texto_vacio_no_se_traduce(self):
        translator = FakeTranslator()
        self.assertEqual(translator.traducir(""), "")
        self.assertIsNone(translator.traducir(None))

    def test_traduccion_none_devuelve_none(self):
        """Si _traducir_interno falla, traducir() devuelve None."""
        translator = FakeTranslator()
        with patch.object(translator, '_traducir_interno', side_effect=Exception("API error")):
            resultado = translator.traducir("Hello {name}")
        self.assertIsNone(resultado)


class TestValidacionPlaceholdersEnServicio(unittest.TestCase):
    """Tests para la validacion de placeholders en translation_service."""

    def test_detecta_placeholders_perdidos(self):
        texto_original = "Page {current} of {total}"
        traduccion_mala = "Pagina de total"

        placeholders_origen = set(PLACEHOLDER_PATTERN.findall(texto_original))
        placeholders_traduccion = set(PLACEHOLDER_PATTERN.findall(traduccion_mala))
        perdidos = placeholders_origen - placeholders_traduccion

        self.assertEqual(perdidos, {"{current}", "{total}"})

    def test_placeholders_correctos_no_genera_perdidos(self):
        texto_original = "Page {current} of {total}"
        traduccion_buena = "Pagina {current} de {total}"

        placeholders_origen = set(PLACEHOLDER_PATTERN.findall(texto_original))
        placeholders_traduccion = set(PLACEHOLDER_PATTERN.findall(traduccion_buena))
        perdidos = placeholders_origen - placeholders_traduccion

        self.assertEqual(perdidos, set())


if __name__ == "__main__":
    unittest.main()
