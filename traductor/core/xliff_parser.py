#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parser XLIFF centralizado con soporte completo para CDATA.

Preserva el formato exacto del archivo original incluyendo:
- Estructura XML completa
- Secciones CDATA
- Espaciado y formato
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Tuple


@dataclass
class TransUnit:
    """Representa una unidad de traduccion."""
    id: str
    source: str
    target: str
    linea_idx: int  # Indice de linea en el archivo
    linea_original: str  # Linea original completa


@dataclass
class XLIFFDocument:
    """Representa un documento XLIFF completo."""
    lineas: List[str] = field(default_factory=list)
    trans_units: List[TransUnit] = field(default_factory=list)
    total_unidades: int = 0


class XLIFFParser:
    """Parser XLIFF que preserva el formato exacto del archivo."""

    # Patron para extraer ID de trans-unit
    PATTERN_TRANS_UNIT_ID = re.compile(r'<trans-unit\s+id="([^"]*)"')

    # Patron para extraer contenido de target con CDATA
    PATTERN_TARGET_CDATA = re.compile(
        r'(<target>)<!\[CDATA\[(.*?)\]\]>(</target>)',
        re.DOTALL
    )

    # Patron para contar trans-units
    PATTERN_TRANS_UNIT = re.compile(r'<trans-unit')

    def __init__(self):
        """Inicializa el parser."""
        self._documento: Optional[XLIFFDocument] = None
        self._ruta_archivo: Optional[str] = None

    def cargar(self, ruta_archivo: str) -> XLIFFDocument:
        """
        Carga y parsea un archivo XLIFF.

        Args:
            ruta_archivo: Ruta al archivo XLIFF

        Returns:
            XLIFFDocument con el contenido parseado
        """
        self._ruta_archivo = ruta_archivo

        with open(ruta_archivo, 'r', encoding='utf-8') as f:
            contenido = f.read()

        lineas = contenido.split('\n')
        trans_units = self._extraer_trans_units(lineas)
        total = len(re.findall(self.PATTERN_TRANS_UNIT, contenido))

        self._documento = XLIFFDocument(
            lineas=lineas,
            trans_units=trans_units,
            total_unidades=total
        )

        return self._documento

    def _extraer_trans_units(self, lineas: List[str]) -> List[TransUnit]:
        """
        Extrae todas las unidades de traduccion.

        Soporta etiquetas target que abarcan multiples lineas.

        Args:
            lineas: Lista de lineas del archivo

        Returns:
            Lista de TransUnit
        """
        contenido_completo = '\n'.join(lineas)
        trans_unit_positions = self._encontrar_trans_unit_positions(contenido_completo)
        pattern_target = re.compile(r'<target><!\[CDATA\[(.*?)\]\]></target>', re.DOTALL)

        trans_units = []
        for match in pattern_target.finditer(contenido_completo):
            unit = self._asociar_target_con_unit(
                match, contenido_completo, trans_unit_positions
            )
            trans_units.append(unit)

        return trans_units

    def _encontrar_trans_unit_positions(self, contenido: str) -> List[Tuple[int, str]]:
        """Encuentra todas las posiciones de trans-unit IDs."""
        positions = []
        for match in self.PATTERN_TRANS_UNIT_ID.finditer(contenido):
            positions.append((match.start(), match.group(1)))
        return positions

    def _asociar_target_con_unit(
        self,
        target_match,
        contenido_completo: str,
        trans_unit_positions: List[Tuple[int, str]]
    ) -> TransUnit:
        """Asocia un target con su trans-unit ID."""
        texto_target = target_match.group(1)
        target_pos = target_match.start()

        # Encontrar trans-unit ID mas cercano anterior
        trans_unit_id = None
        for pos, unit_id in reversed(trans_unit_positions):
            if pos < target_pos:
                trans_unit_id = unit_id
                break

        linea_idx = contenido_completo[:target_pos].count('\n')

        return TransUnit(
            id=trans_unit_id or f'pos_{target_pos}',
            source=texto_target,
            target=texto_target,
            linea_idx=linea_idx,
            linea_original=f'<target><![CDATA[{texto_target}]]></target>'
        )

    def actualizar_traduccion(self, trans_unit: TransUnit, nueva_traduccion: str) -> None:
        """
        Actualiza la traduccion de una unidad en el documento.

        Soporta etiquetas target que abarcan multiples lineas.

        Args:
            trans_unit: Unidad a actualizar
            nueva_traduccion: Nueva traduccion
        """
        if self._documento is None:
            raise ValueError("No hay documento cargado")

        # Reconstruir contenido completo
        contenido = '\n'.join(self._documento.lineas)

        # Reemplazar el target original por el nuevo
        target_original = f'<target><![CDATA[{trans_unit.target}]]></target>'
        target_nuevo = f'<target><![CDATA[{nueva_traduccion}]]></target>'

        contenido = contenido.replace(target_original, target_nuevo, 1)

        # Actualizar las lineas
        self._documento.lineas = contenido.split('\n')
        trans_unit.target = nueva_traduccion

    def guardar(self, ruta_salida: str) -> None:
        """
        Guarda el documento en un archivo.

        Args:
            ruta_salida: Ruta del archivo de salida
        """
        if self._documento is None:
            raise ValueError("No hay documento cargado")

        # Asegurar que existe el directorio
        Path(ruta_salida).parent.mkdir(parents=True, exist_ok=True)

        contenido = '\n'.join(self._documento.lineas)
        with open(ruta_salida, 'w', encoding='utf-8') as f:
            f.write(contenido)

    def iterar_unidades(self) -> Iterator[TransUnit]:
        """
        Itera sobre todas las unidades de traduccion.

        Yields:
            TransUnit
        """
        if self._documento is None:
            raise ValueError("No hay documento cargado")

        yield from self._documento.trans_units

    def obtener_textos_para_traducir(self) -> Dict[str, str]:
        """
        Obtiene diccionario de textos a traducir.

        Returns:
            Diccionario {id: texto}
        """
        if self._documento is None:
            raise ValueError("No hay documento cargado")

        return {unit.id: unit.target for unit in self._documento.trans_units}

    @property
    def total_unidades(self) -> int:
        """Retorna el total de unidades."""
        return self._documento.total_unidades if self._documento else 0

    @property
    def documento(self) -> Optional[XLIFFDocument]:
        """Retorna el documento actual."""
        return self._documento


def extraer_estadisticas_xliff(ruta: str) -> Dict[str, int]:
    """
    Extrae estadisticas basicas de un archivo XLIFF.

    Args:
        ruta: Ruta al archivo

    Returns:
        Diccionario con estadisticas
    """
    parser = XLIFFParser()
    doc = parser.cargar(ruta)

    return {
        "total_lineas": len(doc.lineas),
        "total_trans_units": doc.total_unidades,
        "unidades_parseadas": len(doc.trans_units),
    }
