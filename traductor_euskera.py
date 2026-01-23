#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Traductor XLIFF Simple - Inglés a Euskera
Usa googletrans (librería gratuita que no requiere API key)
Preserva el formato exacto del archivo XLIFF original
"""

import json
import os
import sys
import time
import re
from pathlib import Path

try:
    from deep_translator import GoogleTranslator
except ImportError:
    print("❌ ERROR: deep-translator no está instalado")
    print("\nInstala con:")
    print("  pip install deep-translator")
    sys.exit(1)

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None
    print("ℹ️  Instala 'tqdm' para una barra de progreso: pip install tqdm\n")


class TraductorXLIFFEuskera:
    """Traductor simple que preserva el formato exacto del XLIFF original"""

    def __init__(self, archivo_entrada: str, archivo_salida: str = None):
        self.archivo_entrada = archivo_entrada

        if archivo_salida is None:
            entrada_path = Path(archivo_entrada)
            self.archivo_salida = str(
                entrada_path.parent / f"{entrada_path.stem}_eu{entrada_path.suffix}"
            )
        else:
            self.archivo_salida = archivo_salida

        self.traductor = GoogleTranslator(source='en', target='eu')
        self.checkpoint_file = "checkpoint_euskera.json"
        self.checkpoint = self._cargar_checkpoint()

        # Patrón para encontrar las etiquetas target con CDATA
        self.pattern_target = re.compile(
            r'(<target>)<!\[CDATA\[(.*?)\]\]>(</target>)',
            re.DOTALL
        )

    def _cargar_checkpoint(self):
        """Carga el checkpoint si existe"""
        if os.path.exists(self.checkpoint_file):
            try:
                with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _guardar_checkpoint(self, id_unidad: str, traduccion: str):
        """Guarda el progreso"""
        self.checkpoint[id_unidad] = traduccion
        # Guardar cada 10 traducciones
        if len(self.checkpoint) % 10 == 0:
            with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(self.checkpoint, f, ensure_ascii=False, indent=2)

    def traducir(self, texto: str, reintentos: int = 3) -> str:
        """Traduce un texto del inglés al euskera"""
        if not texto or not texto.strip():
            return texto

        for intento in range(reintentos):
            try:
                return self.traductor.translate(texto)
            except Exception as e:
                if intento < reintentos - 1:
                    print(f"\n⚠️  Error en intento {intento + 1}, reintentando...")
                    time.sleep(2 ** intento)  # Espera exponencial: 1s, 2s, 4s
                else:
                    print(f"\n❌ Error al traducir: {texto[:50]}...")
                    return texto  # Devolver el original si falla

        return texto

    def _extraer_id_trans_unit(self, linea: str) -> str:
        """Extrae el ID de una línea trans-unit"""
        match = re.search(r'<trans-unit\s+id="([^"]*)"', linea)
        if match:
            return match.group(1)
        return None

    def procesar(self):
        """Procesa el archivo XLIFF preservando el formato exacto"""
        print(f"📂 Cargando archivo: {self.archivo_entrada}")

        # Leer todo el contenido del archivo
        with open(self.archivo_entrada, 'r', encoding='utf-8') as f:
            contenido = f.read()

        # Contar total de trans-units
        total = len(re.findall(r'<trans-unit', contenido))
        print(f"📊 Total de unidades encontradas: {total}")

        if total == 0:
            print("❌ No se encontraron unidades de traducción")
            return

        print(f"🔄 Iniciando traducción al euskera...\n")

        procesadas = 0
        desde_checkpoint = 0
        nuevas = 0
        errores = 0

        # Dividir en líneas para procesar
        lineas = contenido.split('\n')
        trans_unit_id = None

        # Crear barra de progreso
        if tqdm:
            pbar = tqdm(total=total, desc="Traduciendo", unit=" unidades")

        for i, linea in enumerate(lineas):
            # Detectar trans-unit para obtener el ID
            if '<trans-unit' in linea:
                trans_unit_id = self._extraer_id_trans_unit(linea)

            # Buscar líneas con <target>
            if '<target>' in linea and '<![CDATA[' in linea:
                # Extraer el texto actual del target
                match = self.pattern_target.search(linea)
                if match:
                    tag_apertura = match.group(1)
                    texto_original = match.group(2)
                    tag_cierre = match.group(3)

                    # Usar el ID de trans-unit como clave de checkpoint
                    checkpoint_key = trans_unit_id or f'line_{i}'

                    # Verificar checkpoint
                    if checkpoint_key in self.checkpoint:
                        traduccion = self.checkpoint[checkpoint_key]
                        desde_checkpoint += 1
                    else:
                        # Traducir el texto
                        traduccion = self.traducir(texto_original)
                        self._guardar_checkpoint(checkpoint_key, traduccion)
                        nuevas += 1

                        # Pausa cada 50 traducciones para no saturar
                        if nuevas % 50 == 0:
                            time.sleep(1)

                    # Reemplazar la línea completa manteniendo el formato exacto
                    linea_nueva = linea.replace(
                        f'<target><![CDATA[{texto_original}]]></target>',
                        f'<target><![CDATA[{traduccion}]]></target>'
                    )
                    lineas[i] = linea_nueva

                    procesadas += 1

                    if tqdm:
                        pbar.update(1)
                    elif procesadas % 100 == 0:
                        porcentaje = (procesadas / total) * 100
                        print(f"Progreso: {procesadas}/{total} ({porcentaje:.1f}%)")

        if tqdm:
            pbar.close()

        # Guardar archivo final
        print(f"\n💾 Guardando archivo traducido...")

        # Guardar checkpoint final
        with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(self.checkpoint, f, ensure_ascii=False, indent=2)

        # Escribir el archivo de salida manteniendo el formato exacto
        contenido_final = '\n'.join(lineas)
        with open(self.archivo_salida, 'w', encoding='utf-8') as f:
            f.write(contenido_final)

        # Resumen
        print(f"\n✅ ¡Traducción completada!")
        print(f"   📝 Unidades procesadas: {procesadas}")
        print(f"   🆕 Nuevas traducciones: {nuevas}")
        print(f"   📋 Desde checkpoint: {desde_checkpoint}")
        if errores > 0:
            print(f"   ⚠️  Errores: {errores}")
        print(f"   💾 Archivo guardado: {self.archivo_salida}")

        # Preguntar si eliminar checkpoint
        if os.path.exists(self.checkpoint_file):
            print(f"\n💡 El archivo de checkpoint se ha guardado en: {self.checkpoint_file}")
            print("   Puedes eliminarlo si la traducción está completa.")


def main():
    """Función principal"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Traductor XLIFF simple - Inglés a Euskera (sin API key)'
    )
    parser.add_argument(
        'archivo',
        help='Archivo XLIFF a traducir'
    )
    parser.add_argument(
        '-o', '--output',
        help='Archivo de salida (por defecto: archivo_eu.xliff)'
    )

    args = parser.parse_args()

    if not os.path.exists(args.archivo):
        print(f"❌ Error: El archivo '{args.archivo}' no existe")
        sys.exit(1)

    try:
        traductor = TraductorXLIFFEuskera(args.archivo, args.output)
        traductor.procesar()
    except KeyboardInterrupt:
        print("\n\n⚠️  Proceso interrumpido por el usuario")
        print("💡 El progreso se ha guardado. Ejecuta el script de nuevo para continuar.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
