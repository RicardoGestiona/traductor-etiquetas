#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Crea un archivo de muestra con las primeras N unidades de traducción
Útil para hacer pruebas rápidas antes de procesar el archivo completo
Preserva el formato exacto del archivo original
"""

import sys
import re
from pathlib import Path

def crear_muestra(archivo_entrada: str, num_unidades: int = 100, archivo_salida: str = None):
    """Crea un archivo de muestra con las primeras N unidades preservando el formato exacto"""
    
    print(f"📂 Cargando archivo: {archivo_entrada}")
    
    # Leer el archivo completo
    with open(archivo_entrada, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    # Contar total de trans-units
    total = len(re.findall(r'<trans-unit', contenido))
    print(f"📊 Total de unidades en el archivo: {total}")
    
    if num_unidades >= total:
        print(f"⚠️  El archivo solo tiene {total} unidades. No es necesario crear una muestra.")
        return
    
    print(f"✂️  Creando muestra con las primeras {num_unidades} unidades...")
    
    # Dividir el contenido por líneas
    lineas = contenido.split('\n')
    
    # Encontrar las líneas donde están las trans-unit
    lineas_resultado = []
    trans_unit_count = 0
    dentro_trans_unit = False
    incluir_linea = True
    
    for linea in lineas:
        # Si encontramos un trans-unit
        if '<trans-unit' in linea:
            trans_unit_count += 1
            dentro_trans_unit = True
            
            # Si ya tenemos suficientes unidades, no incluir esta
            if trans_unit_count > num_unidades:
                incluir_linea = False
        
        # Si estamos dentro de una trans-unit que no queremos, saltarla
        if incluir_linea:
            lineas_resultado.append(linea)
        
        # Si encontramos el cierre de trans-unit
        if '</trans-unit>' in linea:
            dentro_trans_unit = False
            if trans_unit_count > num_unidades:
                incluir_linea = True
    
    # Reconstruir el contenido
    contenido_final = '\n'.join(lineas_resultado)
    
    # Determinar nombre del archivo de salida
    if archivo_salida is None:
        entrada_path = Path(archivo_entrada)
        archivo_salida = str(
            entrada_path.parent / f"{entrada_path.stem}_muestra_{num_unidades}{entrada_path.suffix}"
        )
    
    # Guardar el archivo de muestra
    print(f"💾 Guardando muestra en: {archivo_salida}")
    with open(archivo_salida, 'w', encoding='utf-8') as f:
        f.write(contenido_final)
    
    print(f"\n✅ ¡Muestra creada exitosamente!")
    print(f"   📝 Unidades incluidas: {num_unidades}")
    print(f"   💾 Archivo: {archivo_salida}")
    print(f"\n💡 Ahora puedes probar la traducción con:")
    print(f"   python3 traductor_simple.py {archivo_salida}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Crea un archivo de muestra con las primeras N unidades de traducción'
    )
    parser.add_argument(
        'archivo_entrada',
        help='Archivo XLIFF original'
    )
    parser.add_argument(
        '-n', '--num-unidades',
        type=int,
        default=100,
        help='Número de unidades a incluir en la muestra (por defecto: 100)'
    )
    parser.add_argument(
        '-o', '--output',
        help='Archivo de salida (por defecto: archivo_muestra_N.xliff)'
    )
    
    args = parser.parse_args()
    
    try:
        crear_muestra(args.archivo_entrada, args.num_unidades, args.output)
    except FileNotFoundError:
        print(f"❌ Error: El archivo '{args.archivo_entrada}' no existe")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

