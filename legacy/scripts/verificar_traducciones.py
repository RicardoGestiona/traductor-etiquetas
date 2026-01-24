#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar las traducciones completadas
Analiza cuántas etiquetas fueron traducidas y cuáles quedaron sin traducir
"""

import re
import sys
from pathlib import Path

def analizar_archivo_xliff(archivo_path):
    """Analiza un archivo XLIFF y cuenta las traducciones"""

    print(f"\n📊 Analizando: {archivo_path}")
    print("=" * 80)

    with open(archivo_path, 'r', encoding='utf-8') as f:
        contenido = f.read()

    # Contar total de trans-units
    total_units = len(re.findall(r'<trans-unit', contenido))

    # Encontrar todas las etiquetas target con CDATA
    pattern_target = re.compile(
        r'<trans-unit[^>]*id="([^"]*)"[^>]*>.*?<source><!\[CDATA\[(.*?)\]\]></source>.*?<target><!\[CDATA\[(.*?)\]\]></target>',
        re.DOTALL
    )

    matches = pattern_target.findall(contenido)

    traducidas = 0
    sin_traducir = []
    identicas = []

    for unit_id, source, target in matches:
        source = source.strip()
        target = target.strip()

        if not target or target == '':
            # Target vacío
            sin_traducir.append({
                'id': unit_id,
                'source': source[:100],  # Primeros 100 caracteres
                'motivo': 'Target vacío'
            })
        elif source == target:
            # Source y target son idénticos (posible no traducción)
            identicas.append({
                'id': unit_id,
                'source': source[:100],
                'motivo': 'Idéntico al source'
            })
            traducidas += 1  # Se cuenta como traducida aunque sea idéntica
        else:
            # Traducida
            traducidas += 1

    # Resumen
    print(f"\n📈 RESULTADOS:")
    print(f"   Total de trans-units encontradas: {total_units}")
    print(f"   Unidades con target procesadas: {len(matches)}")
    print(f"   ✅ Traducidas: {traducidas}")
    print(f"   ⚠️  Sin traducir (vacías): {len(sin_traducir)}")
    print(f"   🔄 Idénticas al source: {len(identicas)}")

    # Mostrar algunas sin traducir
    if sin_traducir:
        print(f"\n❌ ETIQUETAS SIN TRADUCIR (vacías):")
        for i, item in enumerate(sin_traducir[:10], 1):
            print(f"   {i}. ID: {item['id']}")
            print(f"      Source: {item['source']}")
            print(f"      Motivo: {item['motivo']}\n")

        if len(sin_traducir) > 10:
            print(f"   ... y {len(sin_traducir) - 10} más")

    # Mostrar algunas idénticas
    if identicas:
        print(f"\n⚠️  ETIQUETAS IDÉNTICAS AL SOURCE (primeras 5):")
        for i, item in enumerate(identicas[:5], 1):
            print(f"   {i}. ID: {item['id']}")
            print(f"      Texto: {item['source']}\n")

        if len(identicas) > 5:
            print(f"   ... y {len(identicas) - 5} más")

    return {
        'total': total_units,
        'procesadas': len(matches),
        'traducidas': traducidas,
        'sin_traducir': len(sin_traducir),
        'identicas': len(identicas)
    }

def main():
    """Función principal"""

    # Archivos a verificar
    archivos = [
        'Idiomas/euskera/xliff-arabic.xliff',
        'Idiomas/gallego/xliff-bosnian.xliff'
    ]

    resultados = {}

    for archivo in archivos:
        archivo_path = Path(archivo)
        if archivo_path.exists():
            resultados[archivo] = analizar_archivo_xliff(archivo_path)
        else:
            print(f"\n❌ Archivo no encontrado: {archivo}")

    # Resumen final
    print("\n" + "=" * 80)
    print("📋 RESUMEN GENERAL")
    print("=" * 80)

    for archivo, res in resultados.items():
        idioma = "EUSKERA" if "euskera" in archivo else "GALLEGO"
        print(f"\n{idioma}:")
        print(f"  Total unidades: {res['total']}")
        print(f"  Procesadas: {res['procesadas']}")
        print(f"  Traducidas: {res['traducidas']} ({res['traducidas']/res['total']*100:.2f}%)")
        print(f"  Sin traducir: {res['sin_traducir']}")
        print(f"  Idénticas: {res['identicas']}")

if __name__ == "__main__":
    main()
