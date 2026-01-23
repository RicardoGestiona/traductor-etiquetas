#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analizador de unidades no traducidas en archivos XLIFF
"""

import xml.etree.ElementTree as ET
import json
from datetime import datetime
import sys

def analizar_unidades_no_traducidas(archivo_original, archivo_traducido):
    """
    Analiza las unidades que no se tradujeron correctamente
    """
    print("🔍 Analizando unidades no traducidas...")
    
    # Parsear archivo original
    print("📂 Cargando archivo original...")
    tree_original = ET.parse(archivo_original)
    root_original = tree_original.getroot()
    
    # Parsear archivo traducido
    print("📂 Cargando archivo traducido...")
    tree_traducido = ET.parse(archivo_traducido)
    root_traducido = tree_traducido.getroot()
    
    # Encontrar namespaces
    namespaces = {
        'ns0': 'urn:oasis:names:tc:xliff:document:1.2',
        'ns1': 'urn:oasis:names:tc:xliff:document:1.2'
    }
    
    # Obtener todas las unidades del archivo original
    unidades_originales = root_original.findall('.//trans-unit')
    print(f"📊 Total de unidades en archivo original: {len(unidades_originales)}")
    
    # Obtener todas las unidades del archivo traducido
    unidades_traducidas = root_traducido.findall('.//trans-unit')
    print(f"📊 Total de unidades en archivo traducido: {len(unidades_traducidas)}")
    
    # Crear diccionario de unidades traducidas por ID
    unidades_traducidas_dict = {}
    for unidad in unidades_traducidas:
        unit_id = unidad.get('id', '')
        source_elem = unidad.find('source')
        target_elem = unidad.find('target')
        
        if source_elem is not None and target_elem is not None:
            source_text = source_elem.text if source_elem.text else ''
            target_text = target_elem.text if target_elem.text else ''
            unidades_traducidas_dict[unit_id] = {
                'source': source_text,
                'target': target_text
            }
    
    # Analizar unidades no traducidas
    no_traducidas = []
    parcialmente_traducidas = []
    total_originales = len(unidades_originales)
    
    print("🔍 Analizando cada unidad...")
    
    for i, unidad in enumerate(unidades_originales):
        if i % 1000 == 0:
            print(f"   Procesando unidad {i+1}/{total_originales}...")
            
        unit_id = unidad.get('id', '')
        source_elem = unidad.find('source')
        target_elem = unidad.find('target')
        
        if source_elem is not None:
            source_text = source_elem.text if source_elem.text else ''
            
            if unit_id in unidades_traducidas_dict:
                # La unidad existe en el archivo traducido
                traducida = unidades_traducidas_dict[unit_id]
                target_text = traducida['target']
                
                # Verificar si está realmente traducida
                if source_text == target_text:
                    # No está traducida (source = target)
                    no_traducidas.append({
                        'id': unit_id,
                        'source': source_text,
                        'target': target_text,
                        'tipo': 'no_traducida'
                    })
                elif target_text.strip() == '':
                    # Target vacío
                    no_traducidas.append({
                        'id': unit_id,
                        'source': source_text,
                        'target': target_text,
                        'tipo': 'target_vacio'
                    })
                else:
                    # Verificar si es una traducción parcial o de baja calidad
                    if len(target_text) < len(source_text) * 0.3:  # Menos del 30% de la longitud
                        parcialmente_traducidas.append({
                            'id': unit_id,
                            'source': source_text,
                            'target': target_text,
                            'tipo': 'traduccion_corta'
                        })
            else:
                # La unidad no existe en el archivo traducido
                no_traducidas.append({
                    'id': unit_id,
                    'source': source_text,
                    'target': '',
                    'tipo': 'no_encontrada'
                })
    
    return no_traducidas, parcialmente_traducidas, total_originales

def generar_informe(no_traducidas, parcialmente_traducidas, total_originales):
    """
    Genera un informe detallado
    """
    total_no_traducidas = len(no_traducidas)
    total_parcialmente = len(parcialmente_traducidas)
    total_traducidas = total_originales - total_no_traducidas - total_parcialmente
    
    # Estadísticas por tipo
    tipos_no_traducidas = {}
    for unidad in no_traducidas:
        tipo = unidad['tipo']
        if tipo not in tipos_no_traducidas:
            tipos_no_traducidas[tipo] = 0
        tipos_no_traducidas[tipo] += 1
    
    # Generar informe
    informe = f"""
# 📊 INFORME DE UNIDADES NO TRADUCIDAS
# Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📈 Estadísticas Generales

- **Total de unidades originales:** {total_originales:,}
- **Unidades traducidas correctamente:** {total_traducidas:,} ({total_traducidas/total_originales*100:.1f}%)
- **Unidades no traducidas:** {total_no_traducidas:,} ({total_no_traducidas/total_originales*100:.1f}%)
- **Unidades parcialmente traducidas:** {total_parcialmente:,} ({total_parcialmente/total_originales*100:.1f}%)

## 🔍 Análisis por Tipo de Problema

"""
    
    for tipo, cantidad in tipos_no_traducidas.items():
        porcentaje = cantidad / total_originales * 100
        tipo_desc = {
            'no_traducida': 'Source = Target (no traducida)',
            'target_vacio': 'Target vacío',
            'no_encontrada': 'Unidad no encontrada en archivo traducido'
        }.get(tipo, tipo)
        
        informe += f"- **{tipo_desc}:** {cantidad:,} ({porcentaje:.1f}%)\n"
    
    if total_parcialmente > 0:
        informe += f"- **Traducciones cortas/sospechosas:** {total_parcialmente:,} ({total_parcialmente/total_originales*100:.1f}%)\n"
    
    informe += f"""

## 📋 Ejemplos de Unidades No Traducidas

### No Traducidas (Source = Target)
"""
    
    # Mostrar ejemplos de cada tipo
    ejemplos_no_traducidas = [u for u in no_traducidas if u['tipo'] == 'no_traducida'][:10]
    for i, unidad in enumerate(ejemplos_no_traducidas, 1):
        source_short = unidad['source'][:100] + '...' if len(unidad['source']) > 100 else unidad['source']
        informe += f"{i}. **ID:** {unidad['id']}\n"
        informe += f"   **Source:** {source_short}\n"
        informe += f"   **Target:** {unidad['target']}\n\n"
    
    if total_parcialmente > 0:
        informe += f"### Traducciones Parciales/Sospechosas\n"
        ejemplos_parciales = parcialmente_traducidas[:5]
        for i, unidad in enumerate(ejemplos_parciales, 1):
            source_short = unidad['source'][:100] + '...' if len(unidad['source']) > 100 else unidad['source']
            target_short = unidad['target'][:100] + '...' if len(unidad['target']) > 100 else unidad['target']
            informe += f"{i}. **ID:** {unidad['id']}\n"
            informe += f"   **Source:** {source_short}\n"
            informe += f"   **Target:** {target_short}\n\n"
    
    informe += f"""
## 💡 Recomendaciones

1. **Revisar unidades no traducidas:** {total_no_traducidas:,} unidades necesitan traducción manual
2. **Verificar traducciones parciales:** {total_parcialmente:,} unidades pueden necesitar revisión
3. **Tasa de éxito:** {total_traducidas/total_originales*100:.1f}% de las unidades fueron traducidas correctamente

## 📁 Archivos de Datos

- **Unidades no traducidas:** `unidades_no_traducidas.json`
- **Traducciones parciales:** `traducciones_parciales.json`
- **Informe completo:** `informe_no_traducidas.md`
"""
    
    return informe

def main():
    archivo_original = '../xliff-english.xliff'
    archivo_traducido = '../xliff-english_ca.xliff'
    
    print("🚀 Iniciando análisis de unidades no traducidas...")
    
    try:
        # Analizar unidades
        no_traducidas, parcialmente_traducidas, total_originales = analizar_unidades_no_traducidas(
            archivo_original, archivo_traducido
        )
        
        # Generar informe
        print("📝 Generando informe...")
        informe = generar_informe(no_traducidas, parcialmente_traducidas, total_originales)
        
        # Guardar archivos
        with open('informe_no_traducidas.md', 'w', encoding='utf-8') as f:
            f.write(informe)
        
        with open('unidades_no_traducidas.json', 'w', encoding='utf-8') as f:
            json.dump(no_traducidas, f, ensure_ascii=False, indent=2)
        
        with open('traducciones_parciales.json', 'w', encoding='utf-8') as f:
            json.dump(parcialmente_traducidas, f, ensure_ascii=False, indent=2)
        
        print("✅ Análisis completado!")
        print(f"📊 Total no traducidas: {len(no_traducidas):,}")
        print(f"📊 Traducciones parciales: {len(parcialmente_traducidas):,}")
        print(f"📁 Archivos generados:")
        print(f"   - informe_no_traducidas.md")
        print(f"   - unidades_no_traducidas.json")
        print(f"   - traducciones_parciales.json")
        
        # Mostrar resumen
        print("\n" + "="*60)
        print(informe)
        
    except Exception as e:
        print(f"❌ Error durante el análisis: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
