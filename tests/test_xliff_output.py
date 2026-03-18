#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests de validacion del fichero XLIFF generado.

Verifica que el archivo de salida cumple las reglas de procesamiento:
- target-language actualizado al codigo ISO destino
- source-language preservado como 'en'
- Etiquetas <source> nunca modificadas
- Etiquetas <target> traducidas correctamente
- Etiquetas vacias permanecen vacias
- Estructura CDATA preservada
- Cabecera XML intacta
"""

import os
import re
import shutil
import tempfile
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

from traductor.core.xliff_parser import XLIFFParser
from traductor.services.batch_processor import BatchProcessor


# --- Fixtures ---

XLIFF_TEMPLATE = """\
<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE xliff PUBLIC "-//XLIFF//DTD XLIFF//EN" "http://www.oasis-open.org/committees/xliff/documents/xliff.dtd">
<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2">
<file datatype="html" source-language="en" target-language="en" date="2026-01-24" original="xliff-english.xliff">
<body>
<trans-unit id="greeting" extradata="TestApp">
      <source><![CDATA[Hello]]></source>
      <target><![CDATA[Hello]]></target>
</trans-unit>
<trans-unit id="farewell" extradata="TestApp">
      <source><![CDATA[Goodbye]]></source>
      <target><![CDATA[Goodbye]]></target>
</trans-unit>
<trans-unit id="empty_label" extradata="TestApp">
      <source><![CDATA[]]></source>
      <target><![CDATA[]]></target>
</trans-unit>
<trans-unit id="special_chars" extradata="TestApp">
      <source><![CDATA[Price: 10€ & 20% off]]></source>
      <target><![CDATA[Price: 10€ & 20% off]]></target>
</trans-unit>
</body>
</file>
</xliff>"""


@pytest.fixture
def xliff_tmp(tmp_path):
    """Crea un archivo XLIFF temporal con contenido de prueba."""
    ruta = tmp_path / "test-input.xliff"
    ruta.write_text(XLIFF_TEMPLATE, encoding="utf-8")
    return str(ruta)


@pytest.fixture
def parser_cargado(xliff_tmp):
    """Retorna un parser con el documento XLIFF de prueba cargado."""
    parser = XLIFFParser()
    parser.cargar(xliff_tmp)
    return parser


@pytest.fixture
def salida_traducida(tmp_path, parser_cargado):
    """Genera un fichero XLIFF con traducciones aplicadas y target-language actualizado."""
    parser = parser_cargado
    parser.actualizar_target_language("ca")

    for unit in parser.iterar_unidades():
        if unit.target and unit.target.strip():
            parser.actualizar_traduccion(unit, f"[CA] {unit.target}")

    ruta_salida = str(tmp_path / "test-output-ca.xliff")
    parser.guardar(ruta_salida)
    return ruta_salida


# --- Tests de cabecera ---

class TestCabeceraXLIFF:
    """Verifica integridad de la cabecera del fichero generado."""

    def test_target_language_actualizado(self, salida_traducida):
        """target-language debe reflejar el codigo ISO destino."""
        with open(salida_traducida, encoding="utf-8") as f:
            contenido = f.read()
        assert 'target-language="ca"' in contenido

    def test_source_language_preservado(self, salida_traducida):
        """source-language debe mantenerse como 'en'."""
        with open(salida_traducida, encoding="utf-8") as f:
            contenido = f.read()
        assert 'source-language="en"' in contenido

    def test_xml_declaration_preservada(self, salida_traducida):
        """La declaracion XML debe ser la primera linea."""
        with open(salida_traducida, encoding="utf-8") as f:
            primera_linea = f.readline()
        assert primera_linea.startswith('<?xml version="1.0" encoding="utf-8"?>')

    def test_doctype_preservado(self, salida_traducida):
        """El DOCTYPE XLIFF debe preservarse."""
        with open(salida_traducida, encoding="utf-8") as f:
            contenido = f.read()
        assert '<!DOCTYPE xliff' in contenido

    def test_target_language_multiples_idiomas(self, xliff_tmp):
        """target-language se actualiza correctamente para distintos codigos ISO."""
        codigos = ["ca", "eu", "gl", "fr", "de", "pt", "it", "es"]
        for codigo in codigos:
            parser = XLIFFParser()
            parser.cargar(xliff_tmp)
            parser.actualizar_target_language(codigo)

            ruta = xliff_tmp.replace(".xliff", f"-{codigo}.xliff")
            parser.guardar(ruta)

            with open(ruta, encoding="utf-8") as f:
                contenido = f.read()
            assert f'target-language="{codigo}"' in contenido, (
                f"target-language no actualizado para {codigo}"
            )


# --- Tests de etiquetas source ---

class TestSourceIntacto:
    """Verifica que las etiquetas <source> nunca se modifican."""

    def test_source_no_modificado(self, salida_traducida):
        """Los textos source deben ser identicos al original."""
        with open(salida_traducida, encoding="utf-8") as f:
            contenido = f.read()

        sources_esperados = [
            "Hello",
            "Goodbye",
            "",
            "Price: 10€ & 20% off",
        ]
        pattern = re.compile(r'<source><!\[CDATA\[(.*?)\]\]></source>', re.DOTALL)
        sources_encontrados = pattern.findall(contenido)

        assert sources_encontrados == sources_esperados


# --- Tests de etiquetas target ---

class TestTargetTraducido:
    """Verifica que las etiquetas <target> se traducen correctamente."""

    def test_targets_traducidos(self, salida_traducida):
        """Los targets no vacios deben contener la traduccion."""
        with open(salida_traducida, encoding="utf-8") as f:
            contenido = f.read()

        pattern = re.compile(r'<target><!\[CDATA\[(.*?)\]\]></target>', re.DOTALL)
        targets = pattern.findall(contenido)

        # Verificar traducciones aplicadas
        assert targets[0] == "[CA] Hello"
        assert targets[1] == "[CA] Goodbye"
        assert targets[3] == "[CA] Price: 10€ & 20% off"

    def test_etiqueta_vacia_permanece_vacia(self, salida_traducida):
        """Una etiqueta con target vacio no debe traducirse."""
        with open(salida_traducida, encoding="utf-8") as f:
            contenido = f.read()

        pattern = re.compile(r'<target><!\[CDATA\[(.*?)\]\]></target>', re.DOTALL)
        targets = pattern.findall(contenido)

        # El tercer target (empty_label) debe seguir vacio
        assert targets[2] == ""

    def test_target_no_es_identico_a_source(self, salida_traducida):
        """Los targets traducidos no deben ser identicos al source (excepto vacios)."""
        with open(salida_traducida, encoding="utf-8") as f:
            contenido = f.read()

        source_pattern = re.compile(r'<source><!\[CDATA\[(.*?)\]\]></source>', re.DOTALL)
        target_pattern = re.compile(r'<target><!\[CDATA\[(.*?)\]\]></target>', re.DOTALL)

        sources = source_pattern.findall(contenido)
        targets = target_pattern.findall(contenido)

        for src, tgt in zip(sources, targets):
            if src.strip():
                assert src != tgt, f"Target identico a source: '{src}'"


# --- Tests de estructura CDATA ---

class TestEstructuraCDATA:
    """Verifica que la estructura CDATA se preserva."""

    def test_todos_los_targets_tienen_cdata(self, salida_traducida):
        """Todos los <target> deben estar envueltos en CDATA."""
        with open(salida_traducida, encoding="utf-8") as f:
            contenido = f.read()

        targets_sin_cdata = re.findall(
            r'<target>(?!<!\[CDATA\[)', contenido
        )
        assert len(targets_sin_cdata) == 0, (
            f"Targets sin CDATA encontrados: {targets_sin_cdata}"
        )

    def test_cdata_correctamente_cerrado(self, salida_traducida):
        """Cada CDATA abierto debe estar correctamente cerrado."""
        with open(salida_traducida, encoding="utf-8") as f:
            contenido = f.read()

        abiertos = len(re.findall(r'<!\[CDATA\[', contenido))
        cerrados = len(re.findall(r'\]\]>', contenido))
        assert abiertos == cerrados

    def test_cdata_escape_secuencia_peligrosa(self, xliff_tmp):
        """Texto que contiene ']]>' debe ser escapado para no romper CDATA."""
        parser = XLIFFParser()
        parser.cargar(xliff_tmp)

        units = list(parser.iterar_unidades())
        # Inyectar texto con secuencia peligrosa
        parser.actualizar_traduccion(units[0], "text]]>injection")

        ruta_salida = xliff_tmp.replace(".xliff", "-escape.xliff")
        parser.guardar(ruta_salida)

        with open(ruta_salida, encoding="utf-8") as f:
            contenido = f.read()

        # No debe haber un cierre CDATA prematuro dentro del target
        # El parser escapa ]]> como ]]]]><![CDATA[>
        target_match = re.search(
            r'<target><!\[CDATA\[(.*?)\]\]></target>',
            contenido,
            re.DOTALL
        )
        # Si el escape funciona, el fichero sigue siendo parseable
        parser2 = XLIFFParser()
        parser2.cargar(ruta_salida)
        assert parser2.total_unidades > 0


# --- Tests de integridad del fichero completo ---

class TestIntegridadFichero:
    """Verifica la integridad general del fichero XLIFF generado."""

    def test_mismo_numero_trans_units(self, xliff_tmp, salida_traducida):
        """El fichero generado debe tener el mismo numero de trans-units."""
        parser_orig = XLIFFParser()
        parser_orig.cargar(xliff_tmp)

        parser_salida = XLIFFParser()
        parser_salida.cargar(salida_traducida)

        assert parser_orig.total_unidades == parser_salida.total_unidades

    def test_mismos_ids_trans_units(self, xliff_tmp, salida_traducida):
        """Los IDs de trans-unit deben preservarse."""
        parser_orig = XLIFFParser()
        parser_orig.cargar(xliff_tmp)
        ids_orig = {u.id for u in parser_orig.iterar_unidades()}

        parser_salida = XLIFFParser()
        parser_salida.cargar(salida_traducida)
        ids_salida = {u.id for u in parser_salida.iterar_unidades()}

        assert ids_orig == ids_salida

    def test_fichero_es_reparseable(self, salida_traducida):
        """El fichero generado debe poder ser cargado de nuevo sin error."""
        parser = XLIFFParser()
        doc = parser.cargar(salida_traducida)
        assert doc.total_unidades > 0
        assert len(doc.trans_units) > 0

    def test_encoding_utf8(self, salida_traducida):
        """El fichero debe ser legible como UTF-8."""
        with open(salida_traducida, encoding="utf-8") as f:
            contenido = f.read()
        assert len(contenido) > 0


# --- Tests del metodo actualizar_target_language ---

class TestActualizarTargetLanguage:
    """Tests unitarios del metodo actualizar_target_language."""

    def test_sin_documento_cargado_lanza_error(self):
        """Debe lanzar ValueError si no hay documento cargado."""
        parser = XLIFFParser()
        with pytest.raises(ValueError, match="No hay documento cargado"):
            parser.actualizar_target_language("ca")

    def test_no_modifica_otras_lineas(self, xliff_tmp):
        """Solo debe modificar la linea que contiene target-language."""
        parser = XLIFFParser()
        parser.cargar(xliff_tmp)
        lineas_antes = list(parser.documento.lineas)

        parser.actualizar_target_language("eu")

        lineas_despues = parser.documento.lineas
        cambios = 0
        for antes, despues in zip(lineas_antes, lineas_despues):
            if antes != despues:
                cambios += 1
                assert 'target-language=' in antes
        assert cambios == 1

    def test_actualizacion_idempotente(self, xliff_tmp):
        """Llamar dos veces con el mismo codigo produce el mismo resultado."""
        parser = XLIFFParser()
        parser.cargar(xliff_tmp)

        parser.actualizar_target_language("gl")
        lineas_primera = list(parser.documento.lineas)

        parser.actualizar_target_language("gl")
        lineas_segunda = parser.documento.lineas

        assert lineas_primera == lineas_segunda

    def test_actualizacion_secuencial(self, xliff_tmp):
        """Actualizar de un codigo a otro debe reflejar el ultimo valor."""
        parser = XLIFFParser()
        parser.cargar(xliff_tmp)

        parser.actualizar_target_language("ca")
        parser.actualizar_target_language("eu")

        contenido = '\n'.join(parser.documento.lineas)
        assert 'target-language="eu"' in contenido
        assert 'target-language="ca"' not in contenido


# --- Tests de archivado del original en inglés ---

class TestArchivoOriginalEnIngles:
    """Verifica que se genera copia del original en xliffs-english-archivo/."""

    @pytest.fixture
    def entorno_batch(self, tmp_path):
        """Crea un entorno temporal para BatchProcessor."""
        carpeta_entrada = tmp_path / "traduccion-pendiente"
        carpeta_salida = tmp_path / "traducidos"
        carpeta_archivo = tmp_path / "xliffs-english-archivo"
        carpeta_entrada.mkdir()
        carpeta_salida.mkdir()

        # Crear archivo XLIFF de prueba
        archivo = carpeta_entrada / "xliff-english.xliff"
        archivo.write_text(XLIFF_TEMPLATE, encoding="utf-8")

        # Patchear la carpeta de archivo dentro del procesador
        with patch.object(
            BatchProcessor,
            "__init__",
            lambda self_bp, **kw: None
        ):
            bp = BatchProcessor()
            bp.carpeta_entrada = carpeta_entrada
            bp.carpeta_salida = carpeta_salida
            bp.carpeta_archivo = carpeta_archivo
            bp.carpeta_archivo.mkdir(parents=True, exist_ok=True)
            bp.carpeta_procesados = carpeta_entrada / "_procesados"
            bp.mover_procesados = False
            bp.db_path = str(tmp_path / "test.db")
            from traductor.utils.logger import get_logger
            bp.logger = get_logger()
            bp.IDIOMAS_DESTINO = []

        return bp, archivo, carpeta_archivo

    def test_genera_copia_en_carpeta_archivo(self, entorno_batch):
        """Se genera la copia en xliffs-english-archivo/."""
        bp, archivo, carpeta_archivo = entorno_batch
        bp._archivar_original(archivo)

        archivos_generados = list(carpeta_archivo.glob("*.xliff"))
        assert len(archivos_generados) == 1

    def test_nombre_sigue_patron_fecha(self, entorno_batch):
        """El nombre sigue el patron YYYYMMDD-xliff-english.xliff."""
        bp, archivo, carpeta_archivo = entorno_batch
        bp._archivar_original(archivo)

        fecha_hoy = date.today().strftime("%Y%m%d")
        esperado = carpeta_archivo / f"{fecha_hoy}-xliff-english.xliff"
        assert esperado.exists()

    def test_contenido_identico_al_original(self, entorno_batch):
        """El contenido de la copia debe ser identico al original."""
        bp, archivo, carpeta_archivo = entorno_batch
        contenido_original = archivo.read_text(encoding="utf-8")

        bp._archivar_original(archivo)

        copia = list(carpeta_archivo.glob("*.xliff"))[0]
        contenido_copia = copia.read_text(encoding="utf-8")
        assert contenido_copia == contenido_original

    def test_sufijo_incremental_mismo_dia(self, entorno_batch):
        """Segunda ejecucion el mismo dia genera sufijo -2."""
        bp, archivo, carpeta_archivo = entorno_batch

        bp._archivar_original(archivo)
        bp._archivar_original(archivo)

        fecha_hoy = date.today().strftime("%Y%m%d")
        primero = carpeta_archivo / f"{fecha_hoy}-xliff-english.xliff"
        segundo = carpeta_archivo / f"{fecha_hoy}-xliff-english-2.xliff"

        assert primero.exists()
        assert segundo.exists()

    def test_tercer_archivo_mismo_dia(self, entorno_batch):
        """Tercera ejecucion el mismo dia genera sufijo -3."""
        bp, archivo, carpeta_archivo = entorno_batch

        bp._archivar_original(archivo)
        bp._archivar_original(archivo)
        bp._archivar_original(archivo)

        fecha_hoy = date.today().strftime("%Y%m%d")
        tercero = carpeta_archivo / f"{fecha_hoy}-xliff-english-3.xliff"
        assert tercero.exists()
